"""Browser management utilities for WCAG Scanner."""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Error as PlaywrightError
from playwright_stealth import Stealth

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Realistic user agent to avoid bot detection
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class BrowserManager:
    """Manages browser instances for scanning."""

    def __init__(self, stealth_mode: bool = True):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._config = get_config()
        self._stealth_mode = stealth_mode

    async def start(self) -> None:
        """Start the browser."""
        if self._browser is not None:
            return

        logger.info("Starting browser...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._config.browser.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--disable-http2',  # Force HTTP/1.1
                '--enable-features=NetworkService,NetworkServiceInProcess',
            ]
        )
        logger.info("Browser started successfully")

    async def stop(self) -> None:
        """Stop the browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Browser stopped")

    @asynccontextmanager
    async def get_page(self, url: str, retries: int = 2) -> AsyncGenerator[Page, None]:
        """
        Get a page context for the given URL with retry logic.

        Args:
            url: URL to navigate to
            retries: Number of retries on failure

        Yields:
            Page instance
        """
        if self._browser is None:
            await self.start()

        context: BrowserContext = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
            java_script_enabled=True,
            bypass_csp=True,
            ignore_https_errors=True,
        )

        page = await context.new_page()

        # Create stealth instance for bot detection evasion
        stealth = None
        if self._stealth_mode:
            stealth = Stealth(
                navigator_webdriver=True,
                navigator_plugins=True,
                navigator_permissions=True,
                webgl_vendor=True,
                chrome_runtime=True,
            )
            await stealth.apply_stealth_async(page)

        last_error = None

        # Wait strategies to try in order (from fastest to most complete)
        wait_strategies = ["domcontentloaded", "load", "networkidle"]

        try:
            for attempt in range(retries + 1):
                for wait_strategy in wait_strategies:
                    try:
                        logger.debug(f"Navigating to {url} (attempt {attempt + 1}, wait: {wait_strategy})")
                        await page.goto(
                            url,
                            wait_until=wait_strategy,
                            timeout=self._config.browser.timeout
                        )
                        # Wait a bit for dynamic content
                        await asyncio.sleep(1.5)
                        yield page
                        return
                    except PlaywrightError as e:
                        last_error = e
                        error_msg = str(e).lower()
                        # If it's a protocol error or timeout, try next strategy
                        if "protocol" in error_msg or "timeout" in error_msg or "net::" in error_msg:
                            logger.warning(f"Navigation failed with {wait_strategy}: {e}")
                            # Close and recreate page for fresh connection
                            await page.close()
                            page = await context.new_page()
                            if stealth:
                                await stealth.apply_stealth_async(page)
                            continue
                        # For other errors, raise immediately
                        raise

                # If all strategies failed, wait before retry
                if attempt < retries:
                    logger.warning(f"All strategies failed, retrying in 3s...")
                    await asyncio.sleep(3)

            # All retries exhausted
            if last_error:
                raise last_error
            raise PlaywrightError(f"Failed to navigate to {url} after {retries + 1} attempts")

        finally:
            await page.close()
            await context.close()

    async def get_page_content(self, url: str) -> str:
        """
        Get the HTML content of a page.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        async with self.get_page(url) as page:
            return await page.content()


@asynccontextmanager
async def get_browser_manager() -> AsyncGenerator[BrowserManager, None]:
    """Context manager for browser lifecycle."""
    manager = BrowserManager()
    try:
        await manager.start()
        yield manager
    finally:
        await manager.stop()
