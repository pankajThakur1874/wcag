"""Scanner orchestrator that coordinates the entire scanning workflow."""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, calculate_duration_ms, generate_id
from scanner_v2.database.models import ScanStatus, WCAGLevel
from scanner_v2.core.crawler import WebsiteCrawler, SitemapCrawler
from scanner_v2.core.page_scanner import PageScanner
from scanner_v2.core.issue_aggregator import issue_aggregator
from scanner_v2.core.compliance_scorer import compliance_scorer

logger = get_logger("orchestrator")


class ScanOrchestrator:
    """Orchestrates the complete scanning workflow."""

    def __init__(self):
        """Initialize scan orchestrator."""
        pass

    async def execute_scan(
        self,
        base_url: str,
        scan_id: str,
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[str, Dict], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute complete scan workflow.

        Args:
            base_url: Base URL to scan
            scan_id: Scan ID
            config: Scan configuration
            progress_callback: Optional callback for progress updates

        Returns:
            Complete scan results
        """
        logger.info(f"Starting scan orchestration for {base_url}")

        start_time = utc_now()
        results = {
            "scan_id": scan_id,
            "base_url": base_url,
            "status": ScanStatus.QUEUED.value,
            "started_at": start_time.isoformat(),
            "pages": [],
            "all_issues": [],
            "summary": {},
            "scores": {},
        }

        try:
            # Update status
            await self._update_progress(
                progress_callback,
                ScanStatus.CRAWLING.value,
                {"message": "Discovering pages..."}
            )

            # Phase 1: Crawl website
            urls = await self._crawl_website(base_url, config)

            logger.info(f"Discovered {len(urls)} URLs")

            results["discovered_urls"] = urls
            results["total_pages"] = len(urls)

            # Update progress
            await self._update_progress(
                progress_callback,
                ScanStatus.SCANNING.value,
                {
                    "message": "Scanning pages...",
                    "pages_discovered": len(urls)
                }
            )

            # Phase 2: Scan pages
            page_results = await self._scan_pages(urls, scan_id, config, progress_callback)

            results["pages"] = page_results
            results["pages_scanned"] = len(page_results)

            # Phase 3: Aggregate issues
            all_issues = []
            for page_result in page_results:
                if "issues" in page_result:
                    for issue in page_result["issues"]:
                        issue["page_url"] = page_result["url"]
                        issue["page_id"] = page_result["page_id"]
                        all_issues.append(issue)

            logger.info(f"Aggregating {len(all_issues)} issues")

            aggregated_issues = issue_aggregator.aggregate_issues(all_issues)
            results["all_issues"] = aggregated_issues

            # Phase 4: Calculate summary and scores
            summary = issue_aggregator.calculate_summary(aggregated_issues)
            results["summary"] = summary

            wcag_level = WCAGLevel(config.get("wcag_level", "AA"))
            scores = compliance_scorer.calculate_score(aggregated_issues, wcag_level)
            results["scores"] = scores

            # Mark as completed
            results["status"] = ScanStatus.COMPLETED.value
            results["completed_at"] = utc_now().isoformat()
            results["duration_seconds"] = calculate_duration_ms(start_time) / 1000

            await self._update_progress(
                progress_callback,
                ScanStatus.COMPLETED.value,
                {
                    "message": "Scan complete",
                    "total_issues": summary["total_issues"],
                    "score": scores["overall"]
                }
            )

            logger.info(f"Scan complete: {summary['total_issues']} issues, score: {scores['overall']}")

            return results

        except Exception as e:
            logger.error(f"Scan failed: {e}")

            results["status"] = ScanStatus.FAILED.value
            results["error_message"] = str(e)
            results["completed_at"] = utc_now().isoformat()

            await self._update_progress(
                progress_callback,
                ScanStatus.FAILED.value,
                {"message": f"Scan failed: {e}"}
            )

            return results

    async def _crawl_website(self, base_url: str, config: Dict[str, Any]) -> List[str]:
        """
        Crawl website to discover pages.

        Args:
            base_url: Base URL
            config: Configuration

        Returns:
            List of discovered URLs
        """
        max_depth = config.get("max_depth", 3)
        max_pages = config.get("max_pages", 100)
        exclude_patterns = config.get("exclude_patterns", [])
        include_patterns = config.get("include_patterns", [])

        # Try sitemap first
        sitemap_crawler = SitemapCrawler(base_url, max_pages)
        urls = await sitemap_crawler.crawl()

        if urls:
            logger.info(f"Found {len(urls)} URLs from sitemap")
            return urls[:max_pages]

        # Fall back to regular crawling
        logger.info("Sitemap not found, using web crawler")

        crawler = WebsiteCrawler(
            base_url=base_url,
            max_depth=max_depth,
            max_pages=max_pages,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )

        urls = await crawler.crawl()
        return urls

    async def _scan_pages(
        self,
        urls: List[str],
        scan_id: str,
        config: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan multiple pages.

        Note: V1 scanners now handle browser creation internally with shared instances.

        Args:
            urls: List of URLs to scan
            scan_id: Scan ID
            config: Configuration
            progress_callback: Progress callback

        Returns:
            List of page scan results
        """
        results = []

        # Create page scanner (no browser needed, V1 handles it)
        page_scanner = PageScanner(
            scanners=config.get("scanners", ["axe"]),
            screenshot_enabled=config.get("screenshot_enabled", True),
            timeout=config.get("page_timeout", 30000)
        )

        for i, url in enumerate(urls):
            logger.info(f"Scanning page {i+1}/{len(urls)}: {url}")

            # Scan page (scanner_service creates and manages browser internally)
            page_result = await page_scanner.scan_page(
                url=url,
                scan_id=scan_id,
                viewport=config.get("viewport", {"width": 1920, "height": 1080})
            )

            results.append(page_result)

            # Update progress
            if progress_callback:
                await self._update_progress(
                    progress_callback,
                    ScanStatus.SCANNING.value,
                    {
                        "message": f"Scanned {i+1}/{len(urls)} pages",
                        "pages_scanned": i+1,
                        "current_url": url
                    }
                )

        return results

    async def _update_progress(
        self,
        callback: Optional[Callable],
        status: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Update scan progress via callback.

        Args:
            callback: Progress callback function (can be sync or async)
            status: Current status
            data: Progress data
        """
        if callback:
            try:
                # Check if callback is async or sync
                import inspect
                if inspect.iscoroutinefunction(callback):
                    await callback(status, data)
                else:
                    callback(status, data)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")


# Global instance
scan_orchestrator = ScanOrchestrator()
