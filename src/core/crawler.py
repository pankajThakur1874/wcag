"""Site crawler for discovering pages on a website."""

import asyncio
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Optional, Set, Callable
from dataclasses import dataclass, field

from playwright.async_api import Page
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CrawlResult:
    """Result of crawling a website."""
    base_url: str
    pages_found: list[str] = field(default_factory=list)
    pages_failed: list[str] = field(default_factory=list)
    total_discovered: int = 0


class SiteCrawler:
    """Crawls a website to discover all pages."""

    def __init__(
        self,
        max_pages: int = 50,
        max_depth: int = 3,
        same_domain_only: bool = True,
        respect_robots: bool = True,
        browser_manager: Optional[BrowserManager] = None
    ):
        """
        Initialize the crawler.

        Args:
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth to crawl (0 = only the given URL)
            same_domain_only: Only crawl pages on the same domain
            respect_robots: Respect robots.txt (basic support)
            browser_manager: Shared browser manager
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        self.respect_robots = respect_robots
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

        self._visited: Set[str] = set()
        self._to_visit: list[tuple[str, int]] = []  # (url, depth)
        self._base_domain: str = ""
        self._disallowed_paths: Set[str] = set()
        self._on_page_discovered: Optional[Callable[[str, int], None]] = None

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """Set callback for when a page is discovered. Args: (url, total_found)"""
        self._on_page_discovered = callback

    async def crawl(self, start_url: str) -> CrawlResult:
        """
        Crawl website starting from the given URL.

        Args:
            start_url: URL to start crawling from

        Returns:
            CrawlResult with discovered pages
        """
        result = CrawlResult(base_url=start_url)

        # Parse base URL
        parsed = urlparse(start_url)
        self._base_domain = parsed.netloc

        # Normalize start URL
        start_url = self._normalize_url(start_url)
        self._to_visit = [(start_url, 0)]
        self._visited = set()

        # Start browser if needed
        if self._browser_manager is None:
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

        try:
            # Fetch robots.txt if enabled
            if self.respect_robots:
                await self._fetch_robots(f"{parsed.scheme}://{parsed.netloc}/robots.txt")

            # Crawl pages
            while self._to_visit and len(result.pages_found) < self.max_pages:
                url, depth = self._to_visit.pop(0)

                if url in self._visited:
                    continue

                if self._is_disallowed(url):
                    logger.debug(f"Skipping disallowed URL: {url}")
                    continue

                self._visited.add(url)

                try:
                    # Discover links on this page
                    links = await self._extract_links(url)

                    result.pages_found.append(url)
                    result.total_discovered = len(self._visited)

                    if self._on_page_discovered:
                        self._on_page_discovered(url, len(result.pages_found))

                    logger.info(f"Crawled ({len(result.pages_found)}/{self.max_pages}): {url}")

                    # Add discovered links to queue
                    if depth < self.max_depth:
                        for link in links:
                            if link not in self._visited and link not in [u for u, _ in self._to_visit]:
                                self._to_visit.append((link, depth + 1))

                except Exception as e:
                    logger.warning(f"Failed to crawl {url}: {e}")
                    result.pages_failed.append(url)

            return result

        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _extract_links(self, url: str) -> list[str]:
        """Extract all links from a page."""
        links = []

        try:
            async with self._browser_manager.get_page(url) as page:
                # Get all anchor tags
                hrefs = await page.evaluate("""
                    () => {
                        const links = [];
                        const anchors = document.querySelectorAll('a[href]');
                        for (const a of anchors) {
                            links.push(a.href);
                        }
                        return links;
                    }
                """)

                for href in hrefs:
                    normalized = self._normalize_url(href)
                    if normalized and self._should_crawl(normalized):
                        links.append(normalized)

        except Exception as e:
            logger.debug(f"Error extracting links from {url}: {e}")

        return list(set(links))  # Remove duplicates

    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize a URL for comparison."""
        try:
            parsed = urlparse(url)

            # Skip non-http(s) URLs
            if parsed.scheme not in ('http', 'https'):
                return None

            # Remove fragment
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path.rstrip('/') or '/',
                '',  # params
                parsed.query,
                ''  # fragment
            ))

            return normalized

        except Exception:
            return None

    def _should_crawl(self, url: str) -> bool:
        """Check if URL should be crawled."""
        parsed = urlparse(url)

        # Same domain check
        if self.same_domain_only and parsed.netloc != self._base_domain:
            return False

        # Skip common non-page resources
        path_lower = parsed.path.lower()
        skip_extensions = (
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.tar', '.gz',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv',
            '.css', '.js', '.json', '.xml',
            '.woff', '.woff2', '.ttf', '.eot'
        )
        if any(path_lower.endswith(ext) for ext in skip_extensions):
            return False

        # Skip common non-content paths
        skip_paths = (
            '/wp-admin', '/admin', '/login', '/logout', '/signup', '/register',
            '/cart', '/checkout', '/account', '/api/', '/feed', '/rss'
        )
        if any(path_lower.startswith(skip) for skip in skip_paths):
            return False

        return True

    def _is_disallowed(self, url: str) -> bool:
        """Check if URL is disallowed by robots.txt."""
        if not self.respect_robots or not self._disallowed_paths:
            return False

        parsed = urlparse(url)
        path = parsed.path.lower()

        for disallowed in self._disallowed_paths:
            if path.startswith(disallowed):
                return True

        return False

    async def _fetch_robots(self, robots_url: str):
        """Fetch and parse robots.txt."""
        try:
            async with self._browser_manager.get_page(robots_url) as page:
                content = await page.content()

                # Basic robots.txt parsing
                current_agent = None
                for line in content.split('\n'):
                    line = line.strip().lower()

                    if line.startswith('user-agent:'):
                        agent = line.split(':', 1)[1].strip()
                        current_agent = agent

                    elif line.startswith('disallow:') and current_agent in ('*', 'wcagscanner'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            self._disallowed_paths.add(path)

                logger.debug(f"Loaded {len(self._disallowed_paths)} disallowed paths from robots.txt")

        except Exception as e:
            logger.debug(f"Could not fetch robots.txt: {e}")
