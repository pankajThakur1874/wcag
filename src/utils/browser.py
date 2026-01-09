"""Browser management utilities for WCAG Scanner."""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """Manages browser instances for scanning."""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._config = get_config()

    async def start(self) -> None:
        """Start the browser."""
        if self._browser is not None:
            return

        logger.info("Starting browser...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._config.browser.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
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
    async def get_page(self, url: str) -> AsyncGenerator[Page, None]:
        """
        Get a page context for the given URL.

        Args:
            url: URL to navigate to

        Yields:
            Page instance
        """
        if self._browser is None:
            await self.start()

        context: BrowserContext = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="WCAG-Scanner/1.0"
        )

        page = await context.new_page()

        try:
            logger.debug(f"Navigating to {url}")
            await page.goto(
                url,
                wait_until="networkidle",
                timeout=self._config.browser.timeout
            )
            yield page
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
