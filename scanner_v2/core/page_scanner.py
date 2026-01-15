"""Page scanner for scanning individual pages."""

from typing import Dict, List, Any, Optional
from datetime import datetime

from playwright.async_api import Browser, Page

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, calculate_duration_ms, generate_id
from scanner_v2.services.scanner_service import scanner_service
from scanner_v2.services.screenshot_service import screenshot_service
from scanner_v2.database.models import ScannedPage, RawScanResults

logger = get_logger("page_scanner")


class PageScanner:
    """Scans individual web pages for accessibility issues."""

    def __init__(
        self,
        browser: Browser,
        scanners: Optional[List[str]] = None,
        screenshot_enabled: bool = True,
        wait_time: int = 2000,
        timeout: int = 30000
    ):
        """
        Initialize page scanner.

        Args:
            browser: Playwright browser instance
            scanners: List of scanners to use
            screenshot_enabled: Whether to capture screenshots
            wait_time: Time to wait after page load (ms)
            timeout: Page load timeout (ms)
        """
        self.browser = browser
        self.scanners = scanners or ["axe"]
        self.screenshot_enabled = screenshot_enabled
        self.wait_time = wait_time
        self.timeout = timeout

    async def scan_page(
        self,
        url: str,
        scan_id: str,
        viewport: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Scan a single page.

        Args:
            url: URL to scan
            scan_id: Parent scan ID
            viewport: Viewport size

        Returns:
            Scan result dictionary
        """
        logger.info(f"Scanning page: {url}")

        start_time = utc_now()
        page: Optional[Page] = None
        page_id = generate_id()

        try:
            # Create new page
            page = await self.browser.new_page(
                viewport=viewport or {"width": 1920, "height": 1080}
            )

            # Navigate to URL
            response = await page.goto(url, timeout=self.timeout, wait_until="networkidle")

            # Wait for additional rendering
            await page.wait_for_timeout(self.wait_time)

            # Get page info
            title = await page.title()
            status_code = response.status if response else None

            # Capture full page screenshot
            screenshot_path = None
            if self.screenshot_enabled:
                screenshot_path = await screenshot_service.capture_full_page(
                    page, scan_id, page_id, url
                )

            # Run scanners
            scanner_results = await scanner_service.scan_page(
                page, url, self.scanners, self.timeout
            )

            # Extract all issues
            all_issues = []
            raw_results = {}

            for scanner_name, result in scanner_results.items():
                if result.success:
                    all_issues.extend(result.violations)
                    raw_results[scanner_name] = result.raw_result

            duration_ms = calculate_duration_ms(start_time)

            logger.info(f"Page scan complete: {url} - {len(all_issues)} issues in {duration_ms}ms")

            return {
                "page_id": page_id,
                "url": url,
                "title": title,
                "status_code": status_code,
                "load_time_ms": duration_ms,
                "screenshot_path": screenshot_path,
                "raw_results": raw_results,
                "issues": all_issues,
                "issues_count": len(all_issues),
            }

        except Exception as e:
            duration_ms = calculate_duration_ms(start_time)
            logger.error(f"Page scan failed for {url}: {e}")

            return {
                "page_id": page_id,
                "url": url,
                "error": str(e),
                "load_time_ms": duration_ms,
                "issues": [],
                "issues_count": 0,
            }

        finally:
            if page:
                await page.close()
