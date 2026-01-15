"""Website crawler for discovering pages to scan."""

import asyncio
from typing import Set, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import re

from playwright.async_api import async_playwright, Browser, Page

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import normalize_url, is_same_domain, is_valid_url
from scanner_v2.utils.exceptions import CrawlerException, CrawlLimitExceededError, InvalidURLError

logger = get_logger("crawler")


class WebsiteCrawler:
    """Crawls a website to discover pages for scanning."""

    def __init__(
        self,
        base_url: str,
        max_depth: int = 3,
        max_pages: int = 100,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        respect_robots_txt: bool = True,
        timeout: int = 30000,
    ):
        """
        Initialize crawler.

        Args:
            base_url: Base URL to start crawling from
            max_depth: Maximum crawl depth
            max_pages: Maximum number of pages to discover
            exclude_patterns: URL patterns to exclude
            include_patterns: URL patterns to include
            respect_robots_txt: Whether to respect robots.txt
            timeout: Page load timeout in milliseconds
        """
        if not is_valid_url(base_url):
            raise InvalidURLError(f"Invalid base URL: {base_url}")

        self.base_url = normalize_url(base_url)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []
        self.respect_robots_txt = respect_robots_txt
        self.timeout = timeout

        self.discovered_urls: Set[str] = set()
        self.visited_urls: Set[str] = set()
        self.robot_parser: Optional[RobotFileParser] = None
        self.domain = urlparse(self.base_url).netloc

    async def crawl(self) -> List[str]:
        """
        Crawl website and discover pages.

        Returns:
            List of discovered URLs

        Raises:
            CrawlerException: If crawling fails
        """
        logger.info(f"Starting crawl of {self.base_url} (max_depth={self.max_depth}, max_pages={self.max_pages})")

        # Load robots.txt
        if self.respect_robots_txt:
            await self._load_robots_txt()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                # Start crawling from base URL
                await self._crawl_recursive(browser, self.base_url, depth=0)

            finally:
                await browser.close()

        discovered = list(self.discovered_urls)
        logger.info(f"Crawl complete. Discovered {len(discovered)} pages")

        return discovered

    async def _crawl_recursive(self, browser: Browser, url: str, depth: int) -> None:
        """
        Recursively crawl pages.

        Args:
            browser: Playwright browser instance
            url: URL to crawl
            depth: Current depth
        """
        # Check limits
        if depth > self.max_depth:
            return

        if len(self.discovered_urls) >= self.max_pages:
            logger.warning(f"Reached max pages limit: {self.max_pages}")
            return

        # Normalize URL
        url = normalize_url(url)

        # Skip if already visited
        if url in self.visited_urls:
            return

        # Skip if not allowed
        if not self._is_allowed(url):
            logger.debug(f"URL not allowed: {url}")
            return

        # Mark as visited
        self.visited_urls.add(url)
        self.discovered_urls.add(url)

        logger.debug(f"Crawling: {url} (depth={depth})")

        # Extract links
        links = await self._extract_links(browser, url)

        # Crawl discovered links
        tasks = []
        for link in links:
            if len(self.discovered_urls) >= self.max_pages:
                break

            if link not in self.visited_urls:
                tasks.append(self._crawl_recursive(browser, link, depth + 1))

        # Crawl links concurrently (but limit concurrency)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _extract_links(self, browser: Browser, url: str) -> List[str]:
        """
        Extract links from a page.

        Args:
            browser: Playwright browser instance
            url: URL to extract links from

        Returns:
            List of discovered links
        """
        page: Optional[Page] = None

        try:
            page = await browser.new_page()
            await page.goto(url, timeout=self.timeout, wait_until="networkidle")

            # Extract all links
            link_elements = await page.query_selector_all("a[href]")
            links = []

            for element in link_elements:
                href = await element.get_attribute("href")
                if href:
                    # Convert to absolute URL
                    absolute_url = urljoin(url, href)

                    # Normalize and validate
                    absolute_url = normalize_url(absolute_url)

                    # Only include links from same domain
                    if is_same_domain(absolute_url, self.base_url):
                        links.append(absolute_url)

            logger.debug(f"Extracted {len(links)} links from {url}")
            return links

        except Exception as e:
            logger.warning(f"Failed to extract links from {url}: {e}")
            return []

        finally:
            if page:
                await page.close()

    def _is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed to be crawled.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        # Check same domain
        if not is_same_domain(url, self.base_url):
            return False

        # Check robots.txt
        if self.respect_robots_txt and self.robot_parser:
            if not self.robot_parser.can_fetch("*", url):
                return False

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if re.search(pattern, url):
                logger.debug(f"URL matches exclude pattern '{pattern}': {url}")
                return False

        # Check include patterns (if specified)
        if self.include_patterns:
            matched = False
            for pattern in self.include_patterns:
                if re.search(pattern, url):
                    matched = True
                    break

            if not matched:
                logger.debug(f"URL doesn't match any include pattern: {url}")
                return False

        # Skip common non-content URLs
        excluded_extensions = [
            ".pdf", ".zip", ".tar", ".gz", ".jpg", ".jpeg", ".png", ".gif",
            ".svg", ".ico", ".css", ".js", ".xml", ".json", ".txt"
        ]

        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        for ext in excluded_extensions:
            if path_lower.endswith(ext):
                return False

        return True

    async def _load_robots_txt(self) -> None:
        """Load and parse robots.txt."""
        try:
            robots_url = urljoin(self.base_url, "/robots.txt")

            self.robot_parser = RobotFileParser()
            self.robot_parser.set_url(robots_url)

            # Note: RobotFileParser.read() is synchronous
            # In production, consider using aiohttp to fetch robots.txt
            await asyncio.to_thread(self.robot_parser.read)

            logger.info(f"Loaded robots.txt from {robots_url}")

        except Exception as e:
            logger.warning(f"Failed to load robots.txt: {e}")
            self.robot_parser = None


class SitemapCrawler:
    """Crawls website using sitemap.xml (faster alternative)."""

    def __init__(self, base_url: str, max_pages: int = 100):
        """
        Initialize sitemap crawler.

        Args:
            base_url: Base URL
            max_pages: Maximum pages to return
        """
        self.base_url = normalize_url(base_url)
        self.max_pages = max_pages

    async def crawl(self) -> List[str]:
        """
        Crawl website using sitemap.

        Returns:
            List of URLs from sitemap
        """
        logger.info(f"Crawling sitemap for {self.base_url}")

        sitemap_url = urljoin(self.base_url, "/sitemap.xml")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(sitemap_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"Sitemap not found: {sitemap_url}")
                        return []

                    content = await response.text()

                    # Parse sitemap XML
                    urls = self._parse_sitemap(content)

                    logger.info(f"Found {len(urls)} URLs in sitemap")
                    return urls[:self.max_pages]

        except Exception as e:
            logger.warning(f"Failed to fetch sitemap: {e}")
            return []

    def _parse_sitemap(self, xml_content: str) -> List[str]:
        """
        Parse sitemap XML.

        Args:
            xml_content: Sitemap XML content

        Returns:
            List of URLs
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(xml_content, "xml")
        urls = []

        # Standard sitemap
        for loc in soup.find_all("loc"):
            url = loc.text.strip()
            if is_valid_url(url) and is_same_domain(url, self.base_url):
                urls.append(normalize_url(url))

        return urls
