"""Site-wide scanner for scanning all pages of a website."""

import asyncio
import time
from typing import Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from src.core.crawler import SiteCrawler, CrawlResult
from src.core.aggregator import ResultsAggregator
from src.models import ScanResult, ScanStatus, ToolStatus, ScanScores, ScanSummary, Violation
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageResult:
    """Result for a single page scan."""
    url: str
    score: float
    violations_count: int
    rules_checked: int
    rules_passed: int
    rules_failed: int
    status: str = "completed"
    error: Optional[str] = None


@dataclass
class SiteScanResult:
    """Result of scanning an entire website."""
    scan_id: str = ""
    base_url: str = ""
    status: ScanStatus = ScanStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0

    # Crawl info
    pages_discovered: int = 0
    pages_scanned: int = 0
    pages_failed: int = 0

    # Aggregated scores
    overall_score: float = 0.0
    total_rules_checked: int = 0
    total_rules_passed: int = 0
    total_rules_failed: int = 0

    # Per-page results
    page_results: list[PageResult] = field(default_factory=list)

    # Aggregated violations (deduplicated across all pages)
    all_violations: list[Violation] = field(default_factory=list)
    unique_violations: list[Violation] = field(default_factory=list)

    # Summary
    summary: dict = field(default_factory=dict)

    # Tools used
    tools_used: list[str] = field(default_factory=list)

    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "scan_id": self.scan_id,
            "base_url": self.base_url,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "pages_discovered": self.pages_discovered,
            "pages_scanned": self.pages_scanned,
            "pages_failed": self.pages_failed,
            "overall_score": self.overall_score,
            "total_rules_checked": self.total_rules_checked,
            "total_rules_passed": self.total_rules_passed,
            "total_rules_failed": self.total_rules_failed,
            "page_results": [
                {
                    "url": p.url,
                    "score": p.score,
                    "violations_count": p.violations_count,
                    "rules_checked": p.rules_checked,
                    "rules_passed": p.rules_passed,
                    "rules_failed": p.rules_failed,
                    "status": p.status,
                    "error": p.error
                }
                for p in self.page_results
            ],
            "unique_violations_count": len(self.unique_violations),
            "total_violations_count": len(self.all_violations),
            "summary": self.summary,
            "tools_used": self.tools_used,
            "error": self.error
        }


class SiteScanner:
    """Scanner that crawls and scans an entire website."""

    def __init__(
        self,
        max_pages: int = 20,
        max_depth: int = 2,
        tools: Optional[list[str]] = None,
        concurrent_scans: int = 2
    ):
        """
        Initialize site scanner.

        Args:
            max_pages: Maximum pages to scan
            max_depth: Maximum crawl depth
            tools: List of scanner tools to use
            concurrent_scans: Number of pages to scan concurrently
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.tools = tools
        self.concurrent_scans = concurrent_scans

        self._progress_callback: Optional[Callable[[str, int, int, str], None]] = None
        self._browser_manager: Optional[BrowserManager] = None

    def set_progress_callback(self, callback: Callable[[str, int, int, str], None]):
        """
        Set progress callback.

        Args:
            callback: Function(phase, current, total, message)
                phase: 'crawling' or 'scanning'
        """
        self._progress_callback = callback

    def _report_progress(self, phase: str, current: int, total: int, message: str):
        """Report progress to callback if set."""
        if self._progress_callback:
            self._progress_callback(phase, current, total, message)
        logger.info(f"[{phase}] {current}/{total}: {message}")

    async def scan_site(self, start_url: str) -> SiteScanResult:
        """
        Crawl and scan an entire website.

        Args:
            start_url: URL to start from

        Returns:
            SiteScanResult with aggregated results
        """
        start_time = time.time()
        result = SiteScanResult(
            base_url=start_url,
            status=ScanStatus.RUNNING,
            tools_used=self.tools or []
        )

        try:
            # Start shared browser
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

            # Phase 1: Crawl the website
            self._report_progress("crawling", 0, self.max_pages, "Starting crawl...")

            crawler = SiteCrawler(
                max_pages=self.max_pages,
                max_depth=self.max_depth,
                browser_manager=self._browser_manager
            )

            def on_page_found(url: str, total: int):
                self._report_progress("crawling", total, self.max_pages, f"Found: {url}")

            crawler.set_progress_callback(on_page_found)

            crawl_result = await crawler.crawl(start_url)
            result.pages_discovered = len(crawl_result.pages_found)

            logger.info(f"Crawl complete: found {len(crawl_result.pages_found)} pages")

            if not crawl_result.pages_found:
                result.status = ScanStatus.FAILED
                result.error = "No pages found to scan"
                return result

            # Phase 2: Scan each page
            self._report_progress("scanning", 0, len(crawl_result.pages_found), "Starting scans...")

            all_violations = []
            page_index = 0

            # Scan pages (with limited concurrency)
            for i in range(0, len(crawl_result.pages_found), self.concurrent_scans):
                batch = crawl_result.pages_found[i:i + self.concurrent_scans]
                tasks = []

                for url in batch:
                    tasks.append(self._scan_single_page(url))

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for j, page_result in enumerate(batch_results):
                    page_index += 1
                    url = batch[j]

                    if isinstance(page_result, Exception):
                        logger.error(f"Page scan failed {url}: {page_result}")
                        result.page_results.append(PageResult(
                            url=url,
                            score=0,
                            violations_count=0,
                            rules_checked=0,
                            rules_passed=0,
                            rules_failed=0,
                            status="error",
                            error=str(page_result)
                        ))
                        result.pages_failed += 1
                    else:
                        scan_result, violations = page_result
                        result.page_results.append(PageResult(
                            url=url,
                            score=scan_result.scores.overall,
                            violations_count=scan_result.summary.total_violations,
                            rules_checked=scan_result.scores.total_rules_checked,
                            rules_passed=scan_result.scores.total_rules_passed,
                            rules_failed=scan_result.scores.total_rules_failed,
                            status="completed"
                        ))
                        all_violations.extend(violations)
                        result.pages_scanned += 1

                        # Aggregate totals
                        result.total_rules_checked += scan_result.scores.total_rules_checked
                        result.total_rules_passed += scan_result.scores.total_rules_passed
                        result.total_rules_failed += scan_result.scores.total_rules_failed

                    self._report_progress(
                        "scanning",
                        page_index,
                        len(crawl_result.pages_found),
                        f"Scanned: {url}"
                    )

            # Deduplicate violations across all pages
            result.all_violations = all_violations
            result.unique_violations = self._deduplicate_violations(all_violations)

            # Calculate overall score
            if result.total_rules_checked > 0:
                result.overall_score = round(
                    (result.total_rules_passed / result.total_rules_checked) * 100, 1
                )

            # Build summary
            result.summary = self._build_summary(result)

            result.status = ScanStatus.COMPLETED
            result.duration_seconds = round(time.time() - start_time, 2)

            logger.info(
                f"Site scan complete: {result.pages_scanned} pages, "
                f"{len(result.unique_violations)} unique violations, "
                f"score: {result.overall_score}%"
            )

            return result

        except Exception as e:
            logger.error(f"Site scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error = str(e)
            result.duration_seconds = round(time.time() - start_time, 2)
            return result

        finally:
            if self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _scan_single_page(self, url: str) -> tuple[ScanResult, list[Violation]]:
        """Scan a single page and return results."""
        aggregator = ResultsAggregator(tools=self.tools)
        aggregator._browser_manager = self._browser_manager

        # Run scan without managing browser (we manage it)
        result = await aggregator.scan(url)

        # Don't let aggregator close our browser
        aggregator._browser_manager = None

        return result, result.violations

    def _deduplicate_violations(self, violations: list[Violation]) -> list[Violation]:
        """Deduplicate violations across pages by rule_id."""
        unique = {}

        for v in violations:
            key = v.rule_id

            if key not in unique:
                # Create a copy with page count
                unique[key] = Violation(
                    id=v.id,
                    rule_id=v.rule_id,
                    wcag_criteria=v.wcag_criteria,
                    wcag_level=v.wcag_level,
                    impact=v.impact,
                    description=v.description,
                    help_text=v.help_text,
                    help_url=v.help_url,
                    detected_by=v.detected_by.copy(),
                    instances=v.instances.copy(),
                    tags=v.tags.copy()
                )
            else:
                # Merge instances
                unique[key].instances.extend(v.instances)
                # Merge detected_by
                for tool in v.detected_by:
                    if tool not in unique[key].detected_by:
                        unique[key].detected_by.append(tool)

        return list(unique.values())

    def _build_summary(self, result: SiteScanResult) -> dict:
        """Build summary statistics."""
        by_impact = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        by_wcag_level = {"A": 0, "AA": 0, "AAA": 0}

        for v in result.unique_violations:
            impact_key = v.impact.value
            if impact_key in by_impact:
                by_impact[impact_key] += 1

            if v.wcag_level:
                level_key = v.wcag_level.value
                if level_key in by_wcag_level:
                    by_wcag_level[level_key] += 1

        # Find pages with most issues
        worst_pages = sorted(
            result.page_results,
            key=lambda p: p.violations_count,
            reverse=True
        )[:5]

        # Find best pages
        best_pages = sorted(
            [p for p in result.page_results if p.status == "completed"],
            key=lambda p: p.score,
            reverse=True
        )[:5]

        return {
            "total_violations": len(result.all_violations),
            "unique_violations": len(result.unique_violations),
            "by_impact": by_impact,
            "by_wcag_level": by_wcag_level,
            "pages_scanned": result.pages_scanned,
            "pages_failed": result.pages_failed,
            "average_score": round(
                sum(p.score for p in result.page_results if p.status == "completed") /
                max(1, result.pages_scanned),
                1
            ),
            "worst_pages": [
                {"url": p.url, "score": p.score, "violations": p.violations_count}
                for p in worst_pages
            ],
            "best_pages": [
                {"url": p.url, "score": p.score, "violations": p.violations_count}
                for p in best_pages
            ]
        }


async def run_site_scan(
    url: str,
    max_pages: int = 20,
    max_depth: int = 2,
    tools: Optional[list[str]] = None
) -> SiteScanResult:
    """
    Convenience function to run a site-wide scan.

    Args:
        url: Starting URL
        max_pages: Maximum pages to scan
        max_depth: Maximum crawl depth
        tools: Scanner tools to use

    Returns:
        SiteScanResult
    """
    scanner = SiteScanner(
        max_pages=max_pages,
        max_depth=max_depth,
        tools=tools
    )
    return await scanner.scan_site(url)
