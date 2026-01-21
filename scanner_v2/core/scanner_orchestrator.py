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
        scan_type = config.get("scan_type", "full")
        max_depth = config.get("max_depth", 3)
        max_pages = config.get("max_pages", 100)
        exclude_patterns = config.get("exclude_patterns", [])
        include_patterns = config.get("include_patterns", [])

        logger.info(f"Crawling website: scan_type={scan_type}, max_depth={max_depth}, max_pages={max_pages}")

        # If single page scan, just return the base URL
        if scan_type == "single_page":
            logger.info(f"Single page scan - returning base URL only: {base_url}")
            return [base_url]

        # Try sitemap first for full scans
        logger.info("Attempting to fetch sitemap.xml...")
        sitemap_crawler = SitemapCrawler(base_url, max_pages)
        urls = await sitemap_crawler.crawl()

        if urls:
            logger.info(f"✓ Successfully found {len(urls)} URLs from sitemap")
            return urls[:max_pages]

        # Fall back to regular crawling
        logger.info("✗ Sitemap not found, falling back to web crawler")

        # Enhanced crawling options
        enable_interactive_crawl = config.get("enable_interactive_crawl", True)
        max_clicks_per_page = config.get("max_clicks_per_page", 5)  # Reduced from 10 to 5 for speed
        js_wait_time = config.get("js_wait_time", 0.5)  # Reduced from 2s to 0.5s

        if enable_interactive_crawl:
            logger.info(f"Interactive crawling ENABLED - will click buttons and track route changes (max {max_clicks_per_page} clicks/page, {js_wait_time}s JS wait)")
        else:
            logger.info("Interactive crawling DISABLED - will only follow <a> links")

        logger.info(f"Starting recursive crawl with max_depth={max_depth}, max_pages={max_pages}")

        crawler = WebsiteCrawler(
            base_url=base_url,
            max_depth=max_depth,
            max_pages=max_pages,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
            enable_interactive_crawl=enable_interactive_crawl,
            max_clicks_per_page=max_clicks_per_page,
            js_wait_time=js_wait_time,
        )

        urls = await crawler.crawl()
        logger.info(f"Web crawler discovered {len(urls)} pages")

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
        total_pages = len(urls)
        scanners_list = config.get("scanners", ["axe"])

        logger.info(f"=" * 60)
        logger.info(f"Starting to scan {total_pages} pages with scanners: {', '.join(scanners_list)}")
        logger.info(f"=" * 60)

        # Track scanning start time for estimates
        scanning_start_time = utc_now()
        page_scan_times = []  # Track time per page for better estimates

        # Create page scanner (no browser needed, V1 handles it)
        page_scanner = PageScanner(
            scanners=scanners_list,
            screenshot_enabled=config.get("screenshot_enabled", True),
            timeout=config.get("page_timeout", 30000)
        )

        for i, url in enumerate(urls):
            page_num = i + 1
            logger.info(f"")
            logger.info(f"[{page_num}/{total_pages}] Scanning: {url}")
            logger.info(f"-" * 60)

            page_start_time = utc_now()

            try:
                # Scan page (scanner_service creates and manages browser internally)
                page_result = await page_scanner.scan_page(
                    url=url,
                    scan_id=scan_id,
                    viewport=config.get("viewport", {"width": 1920, "height": 1080})
                )

                results.append(page_result)

                # Log results
                issues_count = len(page_result.get("issues", []))
                logger.info(f"✓ Page {page_num} complete: {issues_count} issues found")

            except Exception as e:
                logger.error(f"✗ Page {page_num} failed: {e}")
                # Still add a result with error
                results.append({
                    "url": url,
                    "page_id": f"page_{i}",
                    "error": str(e),
                    "issues": []
                })

            # Track scan time for this page
            page_duration = calculate_duration_ms(page_start_time) / 1000  # Convert to seconds
            page_scan_times.append(page_duration)

            # Calculate progress metrics
            percentage_complete = (page_num / total_pages) * 100

            # Estimate remaining time based on average time per page
            avg_time_per_page = sum(page_scan_times) / len(page_scan_times)
            pages_remaining = total_pages - page_num
            estimated_seconds_remaining = int(avg_time_per_page * pages_remaining)

            # Update progress
            if progress_callback:
                await self._update_progress(
                    progress_callback,
                    ScanStatus.SCANNING.value,
                    {
                        "message": f"Scanned {page_num}/{total_pages} pages",
                        "pages_scanned": page_num,
                        "pages_total": total_pages,
                        "current_url": url,
                        "percentage_complete": round(percentage_complete, 1),
                        "estimated_time_remaining_seconds": estimated_seconds_remaining,
                        "started_at": scanning_start_time.isoformat()
                    }
                )

        logger.info(f"")
        logger.info(f"=" * 60)
        logger.info(f"✓ Completed scanning all {total_pages} pages")
        logger.info(f"=" * 60)

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
