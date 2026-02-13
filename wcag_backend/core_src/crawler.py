"""Site crawler for discovering pages on a website."""

import asyncio
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Optional, Set, Callable
from dataclasses import dataclass, field

from playwright.async_api import Page
from wcag_backend.utils_src.browser import BrowserManager
from wcag_backend.utils.logger import get_logger

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
                    # Silently skip disallowed URLs
                    continue

                self._visited.add(url)

                try:
                    # Discover links on this page
                    links = await self._extract_links(url)

                    result.pages_found.append(url)
                    result.total_discovered = len(self._visited)

                    if self._on_page_discovered:
                        self._on_page_discovered(url, len(result.pages_found))

                    # Add discovered links to queue
                    if depth < self.max_depth:
                        new_links_count = 0
                        for link in links:
                            if link not in self._visited and link not in [u for u, _ in self._to_visit]:
                                self._to_visit.append((link, depth + 1))
                                new_links_count += 1

                        if new_links_count > 0:
                            logger.info(f"   └─ Found {new_links_count} new links (depth {depth + 1})")

                except Exception as e:
                    logger.warning(f"⚠️  Failed to crawl {url}: {e}")
                    result.pages_failed.append(url)

            return result

        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _extract_links(self, url: str) -> list[str]:
        """Extract all links from a page including dynamic content."""
        links = []
        all_found_links = []
        filtered_out = []

        try:
            async with self._browser_manager.get_page(url) as page:
                # Wait for network to be idle (JavaScript to load)
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass  # Continue even if timeout

                # Expand dropdowns and hidden navigation
                try:
                    await page.evaluate("""
                        () => {
                            // Click on common dropdown triggers
                            const dropdownTriggers = document.querySelectorAll(
                                '[class*="dropdown"], [class*="menu-toggle"], ' +
                                '[aria-haspopup="true"], [data-toggle="dropdown"], ' +
                                'button[class*="nav"], .navbar-toggler, .hamburger, ' +
                                '[class*="mobile"], [id*="menu"]'
                            );

                            dropdownTriggers.forEach(trigger => {
                                try {
                                    // Make hidden content visible
                                    if (trigger.nextElementSibling) {
                                        trigger.nextElementSibling.style.display = 'block';
                                        trigger.nextElementSibling.style.visibility = 'visible';
                                        trigger.nextElementSibling.style.opacity = '1';
                                    }
                                    // Set aria-expanded
                                    trigger.setAttribute('aria-expanded', 'true');
                                } catch (e) {}
                            });

                            // Expand all details/summary elements
                            document.querySelectorAll('details').forEach(details => {
                                details.open = true;
                            });

                            // Show all hidden menus
                            document.querySelectorAll('[style*="display: none"], [style*="visibility: hidden"]').forEach(el => {
                                if (el.tagName === 'NAV' || el.className.includes('menu') || el.className.includes('nav')) {
                                    el.style.display = 'block';
                                    el.style.visibility = 'visible';
                                }
                            });
                        }
                    """)
                    await page.wait_for_timeout(500)
                except Exception:
                    pass

                # Scroll to load lazy content
                try:
                    await page.evaluate("""
                        async () => {
                            await new Promise((resolve) => {
                                let totalHeight = 0;
                                const distance = 100;
                                const timer = setInterval(() => {
                                    window.scrollBy(0, distance);
                                    totalHeight += distance;
                                    if(totalHeight >= document.body.scrollHeight){
                                        clearInterval(timer);
                                        window.scrollTo(0, 0);
                                        resolve();
                                    }
                                }, 100);
                            });
                        }
                    """)
                    await page.wait_for_timeout(500)
                except Exception:
                    pass

                # Extract links from multiple sources
                hrefs = await page.evaluate("""
                    () => {
                        const links = new Set();

                        // 1. Regular anchor tags
                        document.querySelectorAll('a[href]').forEach(a => {
                            links.add(a.href);
                        });

                        // 2. Buttons with data-href or onclick with URLs
                        document.querySelectorAll('button, [role="button"]').forEach(btn => {
                            // Check data attributes
                            const dataHref = btn.getAttribute('data-href') ||
                                           btn.getAttribute('data-url') ||
                                           btn.getAttribute('data-link');
                            if (dataHref) links.add(dataHref);

                            // Check onclick for URLs
                            const onclick = btn.getAttribute('onclick');
                            if (onclick) {
                                const urlMatch = onclick.match(/(?:window\\.location|href)\\s*=\\s*['"]([^'"]+)['"]/);
                                if (urlMatch) links.add(urlMatch[1]);
                            }
                        });

                        // 3. Navigation items (common in SPAs)
                        document.querySelectorAll('[class*="nav"] a, [class*="menu"] a, [class*="link"] a').forEach(a => {
                            if (a.href) links.add(a.href);
                        });

                        // 4. Check for SPA route links
                        document.querySelectorAll('[routerLink], [to], [href^="#/"]').forEach(el => {
                            const route = el.getAttribute('routerLink') ||
                                        el.getAttribute('to') ||
                                        el.getAttribute('href');
                            if (route && !route.startsWith('#')) {
                                // Convert relative route to absolute URL
                                const url = new URL(route, window.location.href);
                                links.add(url.href);
                            }
                        });

                        // 5. Meta refresh and canonical links
                        const canonical = document.querySelector('link[rel="canonical"]');
                        if (canonical) links.add(canonical.href);

                        return Array.from(links);
                    }
                """)

                logger.info(f"      ├─ Raw links found: {len(hrefs)}")

                for href in hrefs:
                    all_found_links.append(href)
                    normalized = self._normalize_url(href)
                    if not normalized:
                        filtered_out.append(f"{href} (invalid URL)")
                        continue

                    if not self._should_crawl(normalized):
                        # Log why it was filtered
                        parsed = urlparse(normalized)
                        if parsed.netloc != self._base_domain:
                            filtered_out.append(f"{normalized} (external)")
                        else:
                            filtered_out.append(f"{normalized} (filtered)")
                        continue

                    links.append(normalized)

                # Log filtering results
                if len(links) > 0:
                    logger.info(f"      ├─ Valid links: {len(links)}")
                    for link in links[:5]:  # Show first 5
                        logger.info(f"      │  • {link}")
                    if len(links) > 5:
                        logger.info(f"      │  ... and {len(links) - 5} more")
                else:
                    logger.warning(f"      ├─ ⚠️  No valid links found!")
                    if len(filtered_out) > 0:
                        logger.warning(f"      ├─ Filtered out {len(filtered_out)} links:")
                        for filtered in filtered_out[:5]:
                            logger.warning(f"      │  • {filtered}")

        except Exception as e:
            logger.error(f"      ├─ ❌ Error extracting links: {e}")

        return list(set(links))  # Remove duplicates

    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize a URL for comparison."""
        try:
            # Handle relative URLs
            if url.startswith('/'):
                base_parsed = urlparse(f"https://{self._base_domain}")
                url = urljoin(f"{base_parsed.scheme}://{base_parsed.netloc}", url)

            parsed = urlparse(url)

            # Skip non-http(s) URLs
            if parsed.scheme not in ('http', 'https'):
                return None

            # Skip empty or just-fragment URLs
            if not parsed.netloc or (not parsed.path and not parsed.query):
                return None

            # Skip mailto, tel, javascript, etc
            if parsed.scheme in ('mailto', 'tel', 'javascript'):
                return None

            # Remove fragment and trailing slash
            path = parsed.path.rstrip('/') if parsed.path != '/' else '/'

            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                path,
                '',  # params
                parsed.query,
                ''  # fragment
            ))

            return normalized

        except Exception as e:
            logger.debug(f"Failed to normalize URL {url}: {e}")
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

        # Skip common non-content paths (made less restrictive)
        skip_paths = (
            '/wp-admin/', '/wp-login', '/admin/login',
            '/api/', '/feed/', '/rss/', '/_next/', '/static/'
        )
        if any(path_lower.startswith(skip) for skip in skip_paths):
            return False

        # Skip anchor-only links (same page navigation)
        if parsed.path == '/' and parsed.query == '' and not parsed.fragment:
            return True

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

                if len(self._disallowed_paths) > 0:
                    logger.info(f"ℹ️  Loaded {len(self._disallowed_paths)} disallowed paths from robots.txt")

        except Exception as e:
            # Silently handle robots.txt fetch errors
            pass
