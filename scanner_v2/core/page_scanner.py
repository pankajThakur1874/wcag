"""Page scanner for scanning individual pages."""

from typing import Dict, List, Any, Optional
from datetime import datetime

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, calculate_duration_ms, generate_id
from scanner_v2.services.scanner_service import scanner_service
from scanner_v2.database.models import ScannedPage, RawScanResults

logger = get_logger("page_scanner")


class PageScanner:
    """Scans individual web pages for accessibility issues."""

    def __init__(
        self,
        scanners: Optional[List[str]] = None,
        screenshot_enabled: bool = True,
        timeout: int = 30000
    ):
        """
        Initialize page scanner.

        Args:
            scanners: List of scanners to use
            screenshot_enabled: Whether to capture screenshots
            timeout: Scanner timeout (ms)
        """
        self.scanners = scanners or ["axe"]
        self.screenshot_enabled = screenshot_enabled
        self.timeout = timeout

    async def scan_page(
        self,
        url: str,
        scan_id: str,
        viewport: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Scan a single page using V1 scanners with shared browser.

        Args:
            url: URL to scan
            scan_id: Parent scan ID
            viewport: Viewport size (currently unused, V1 BrowserManager handles this)

        Returns:
            Scan result dictionary
        """
        logger.info(f"Scanning page: {url}")

        start_time = utc_now()
        page_id = generate_id()

        try:
            # Call scanner_service which now handles:
            # 1. Browser creation (single instance)
            # 2. Screenshot capture
            # 3. Running all V1 scanners with shared browser
            scan_result = await scanner_service.scan_page(
                url=url,
                scan_id=scan_id,
                page_id=page_id,
                scanners=self.scanners,
                screenshot_enabled=self.screenshot_enabled,
                timeout=self.timeout
            )

            # Extract scanner results
            scanner_results = scan_result.get("scanner_results", {})
            screenshot_path = scan_result.get("screenshot_path")
            title = scan_result.get("title")
            status_code = scan_result.get("status_code")

            # Extract all issues and raw results
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
            logger.error(f"Scanner execution failed for {url}: {e}")

            return {
                "page_id": page_id,
                "url": url,
                "error": str(e),
                "load_time_ms": duration_ms,
                "issues": [],
                "issues_count": 0,
            }
