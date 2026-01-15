"""Screenshot service for capturing page and element screenshots."""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from playwright.async_api import Page, ElementHandle

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import sanitize_filename, utc_now
from scanner_v2.utils.exceptions import ScannerException

logger = get_logger("screenshot")


class ScreenshotService:
    """Service for capturing screenshots."""

    def __init__(self, screenshots_dir: Optional[str] = None):
        """
        Initialize screenshot service.

        Args:
            screenshots_dir: Directory to save screenshots (default: ./screenshots)
        """
        if screenshots_dir is None:
            screenshots_dir = Path.cwd() / "screenshots"

        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def capture_full_page(
        self,
        page: Page,
        scan_id: str,
        page_id: str,
        url: str
    ) -> Optional[str]:
        """
        Capture full page screenshot.

        Args:
            page: Playwright page
            scan_id: Scan ID
            page_id: Page ID
            url: Page URL

        Returns:
            Screenshot path or None if failed
        """
        try:
            # Create scan directory
            scan_dir = self.screenshots_dir / scan_id
            scan_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = f"{page_id}_full.png"
            filepath = scan_dir / filename

            # Capture screenshot
            await page.screenshot(path=str(filepath), full_page=True)

            logger.info(f"Captured full page screenshot: {filepath}")

            return str(filepath.relative_to(self.screenshots_dir))

        except Exception as e:
            logger.error(f"Failed to capture full page screenshot: {e}")
            return None

    async def capture_element(
        self,
        page: Page,
        selector: str,
        scan_id: str,
        page_id: str,
        issue_index: int
    ) -> Optional[str]:
        """
        Capture screenshot of specific element.

        Args:
            page: Playwright page
            selector: CSS selector
            scan_id: Scan ID
            page_id: Page ID
            issue_index: Issue index

        Returns:
            Screenshot path or None if failed
        """
        try:
            # Create scan directory
            scan_dir = self.screenshots_dir / scan_id
            scan_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = f"{page_id}_issue_{issue_index}.png"
            filepath = scan_dir / filename

            # Find element
            element = await page.query_selector(selector)

            if element:
                # Highlight element before screenshot
                await self._highlight_element(page, selector)

                # Capture element screenshot
                await element.screenshot(path=str(filepath))

                logger.debug(f"Captured element screenshot: {filepath}")

                return str(filepath.relative_to(self.screenshots_dir))
            else:
                logger.warning(f"Element not found for screenshot: {selector}")
                return None

        except Exception as e:
            logger.warning(f"Failed to capture element screenshot for {selector}: {e}")
            return None

    async def capture_viewport(
        self,
        page: Page,
        scan_id: str,
        page_id: str,
        suffix: str = "viewport"
    ) -> Optional[str]:
        """
        Capture viewport screenshot (current visible area).

        Args:
            page: Playwright page
            scan_id: Scan ID
            page_id: Page ID
            suffix: Filename suffix

        Returns:
            Screenshot path or None if failed
        """
        try:
            # Create scan directory
            scan_dir = self.screenshots_dir / scan_id
            scan_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = f"{page_id}_{suffix}.png"
            filepath = scan_dir / filename

            # Capture screenshot
            await page.screenshot(path=str(filepath), full_page=False)

            logger.debug(f"Captured viewport screenshot: {filepath}")

            return str(filepath.relative_to(self.screenshots_dir))

        except Exception as e:
            logger.error(f"Failed to capture viewport screenshot: {e}")
            return None

    async def _highlight_element(self, page: Page, selector: str) -> None:
        """
        Highlight element with red border.

        Args:
            page: Playwright page
            selector: CSS selector
        """
        try:
            await page.evaluate(f"""
                (selector) => {{
                    const element = document.querySelector(selector);
                    if (element) {{
                        element.style.outline = '3px solid red';
                        element.style.outlineOffset = '2px';
                    }}
                }}
            """, selector)
        except Exception as e:
            logger.warning(f"Failed to highlight element {selector}: {e}")

    def get_screenshot_path(self, relative_path: str) -> Path:
        """
        Get absolute screenshot path from relative path.

        Args:
            relative_path: Relative path from screenshots directory

        Returns:
            Absolute path
        """
        return self.screenshots_dir / relative_path

    def cleanup_scan_screenshots(self, scan_id: str) -> None:
        """
        Delete all screenshots for a scan.

        Args:
            scan_id: Scan ID
        """
        try:
            scan_dir = self.screenshots_dir / scan_id

            if scan_dir.exists():
                import shutil
                shutil.rmtree(scan_dir)
                logger.info(f"Deleted screenshots for scan: {scan_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup screenshots for scan {scan_id}: {e}")


# Global screenshot service
screenshot_service = ScreenshotService()
