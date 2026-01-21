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
        enable_interactive_crawl: bool = True,
        max_clicks_per_page: int = 10,
        click_timeout: int = 3000,
        js_wait_time: float = 0.5,
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
            enable_interactive_crawl: Enable clicking buttons and interactive elements
            max_clicks_per_page: Maximum interactive elements to click per page
            click_timeout: Timeout for waiting after clicks (ms)
            js_wait_time: Time to wait for JavaScript rendering (seconds)
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
        self.enable_interactive_crawl = enable_interactive_crawl
        self.max_clicks_per_page = max_clicks_per_page
        self.click_timeout = click_timeout
        self.js_wait_time = js_wait_time

        self.discovered_urls: Set[str] = set()
        self.visited_urls: Set[str] = set()
        self.robot_parser: Optional[RobotFileParser] = None
        self.domain = urlparse(self.base_url).netloc
        self.discovered_routes: Set[str] = set()  # Track SPA routes

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
            # Try Firefox first (better compatibility with some sites)
            try:
                browser = await p.firefox.launch(headless=True)
                browser_type = "Firefox"
            except Exception as e:
                logger.warning(f"Firefox launch failed, falling back to Chromium: {e}")
                browser = await p.chromium.launch(headless=True)
                browser_type = "Chromium"

            logger.info(f"Using {browser_type} browser for crawling")

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
        # Check depth limit
        if depth > self.max_depth:
            logger.debug(f"Depth limit reached at {depth} for {url}")
            return

        # Check pages limit
        if len(self.discovered_urls) >= self.max_pages:
            logger.debug(f"Max pages limit reached: {self.max_pages}")
            return

        # Normalize URL
        url = normalize_url(url)

        # Skip if already visited
        if url in self.visited_urls:
            logger.debug(f"Already visited: {url}")
            return

        # Skip if not allowed
        if not self._is_allowed(url):
            logger.debug(f"URL not allowed: {url}")
            return

        # Mark as visited
        self.visited_urls.add(url)
        self.discovered_urls.add(url)

        logger.info(f"Discovered page {len(self.discovered_urls)}/{self.max_pages}: {url} (depth={depth})")

        # Extract links (traditional <a> tags)
        links = await self._extract_links(browser, url)
        logger.info(f"Found {len(links)} traditional links on {url}")

        # Try interactive crawling if enabled
        if self.enable_interactive_crawl and len(self.discovered_urls) < self.max_pages:
            interactive_urls = await self._discover_interactive_pages(browser, url)
            if interactive_urls:
                logger.info(f"Found {len(interactive_urls)} additional pages via interactive elements on {url}")
                links.extend(interactive_urls)

        # Crawl discovered links (limit concurrency to avoid overwhelming the site)
        # Process links in batches to control concurrency
        batch_size = 5  # Process 5 links concurrently

        for i in range(0, len(links), batch_size):
            # Check if we've reached max pages
            if len(self.discovered_urls) >= self.max_pages:
                logger.info(f"Reached max pages limit ({self.max_pages}), stopping crawl")
                break

            batch = links[i:i + batch_size]
            tasks = []

            for link in batch:
                if len(self.discovered_urls) >= self.max_pages:
                    break

                if link not in self.visited_urls:
                    tasks.append(self._crawl_recursive(browser, link, depth + 1))

            if tasks:
                # Process batch concurrently
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
            # Create page with stealth configuration
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # Set extra HTTP headers
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })

            # Hide automation indicators
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                window.chrome = { runtime: {} };
            """)

            await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")

            # Wait for JavaScript to render content (important for SPAs)
            if self.js_wait_time > 0:
                await asyncio.sleep(self.js_wait_time)

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

    async def _discover_interactive_pages(self, browser: Browser, url: str) -> List[str]:
        """
        Discover pages by clicking interactive elements (buttons, divs with click handlers).

        Args:
            browser: Playwright browser instance
            url: Current page URL

        Returns:
            List of newly discovered URLs
        """
        page: Optional[Page] = None
        discovered = []

        try:
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            })

            # Hide automation indicators
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)

            await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")

            # Wait for JavaScript to render content (important for SPAs)
            if self.js_wait_time > 0:
                await asyncio.sleep(self.js_wait_time)

            # Find clickable elements
            clickable_selectors = [
                'button:not([type="submit"]):not([disabled])',
                '[role="button"]:not([disabled])',
                'a[href="#"]:not([data-toggle])',
                'div[onclick]',
                'span[onclick]',
                '[data-navigation]',
                '[data-route]',
                '.nav-link:not([href^="http"])',
                '.menu-item:not([href^="http"])',
            ]

            for selector in clickable_selectors:
                try:
                    elements = await page.query_selector_all(selector)

                    # Limit number of elements to click
                    elements = elements[:self.max_clicks_per_page]

                    for element in elements:
                        # Check if we've reached max pages
                        if len(self.discovered_urls) + len(discovered) >= self.max_pages:
                            break

                        try:
                            # Get current URL before click
                            current_url = page.url

                            # Check if element is visible and enabled
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()

                            if not is_visible or not is_enabled:
                                continue

                            # Setup route change listener for SPAs
                            route_changed = False
                            new_route = None

                            async def handle_route_change(route):
                                nonlocal route_changed, new_route
                                if route != current_url:
                                    route_changed = True
                                    new_route = route

                            # Listen for URL changes (including pushState/replaceState)
                            await page.evaluate("""
                                window.__originalPushState = window.history.pushState;
                                window.__originalReplaceState = window.history.replaceState;
                                window.__routeChanged = false;
                                window.__newRoute = null;

                                window.history.pushState = function(...args) {
                                    window.__routeChanged = true;
                                    window.__newRoute = window.location.href;
                                    return window.__originalPushState.apply(this, args);
                                };

                                window.history.replaceState = function(...args) {
                                    window.__routeChanged = true;
                                    window.__newRoute = window.location.href;
                                    return window.__originalReplaceState.apply(this, args);
                                };
                            """)

                            # Click the element
                            await element.click(timeout=self.click_timeout)

                            # Wait briefly for any navigation or route changes
                            await asyncio.sleep(0.2)

                            # Check if URL changed
                            after_click_url = page.url

                            # Check if route changed via history API
                            route_info = await page.evaluate("""
                                ({
                                    changed: window.__routeChanged,
                                    newRoute: window.__newRoute
                                })
                            """)

                            new_url = None

                            if after_click_url != current_url:
                                new_url = after_click_url
                                logger.debug(f"Click caused navigation to: {new_url}")
                            elif route_info['changed'] and route_info['newRoute']:
                                new_url = route_info['newRoute']
                                logger.debug(f"Click caused SPA route change to: {new_url}")

                            if new_url:
                                new_url = normalize_url(new_url)

                                # Check if this is a new URL from same domain
                                if (is_same_domain(new_url, self.base_url) and
                                    new_url not in self.discovered_urls and
                                    new_url not in discovered and
                                    self._is_allowed(new_url)):

                                    discovered.append(new_url)
                                    logger.info(f"Interactive discovery: {new_url}")

                                # Navigate back if URL changed
                                if after_click_url != current_url:
                                    await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")

                        except Exception as e:
                            logger.debug(f"Failed to click element: {e}")
                            continue

                except Exception as e:
                    logger.debug(f"Failed to process selector {selector}: {e}")
                    continue

            logger.debug(f"Interactive crawl found {len(discovered)} new URLs")
            return discovered

        except Exception as e:
            logger.warning(f"Interactive page discovery failed for {url}: {e}")
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
