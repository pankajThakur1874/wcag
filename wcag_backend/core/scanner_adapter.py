"""Scanner adapter to integrate existing src/scanners with wcag-backend."""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Callable
import asyncio

# Add src directory to path to import existing scanners
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wcag_backend.core_src.aggregator import ResultsAggregator
from wcag_backend.core_src.site_scanner import SiteScanner
from wcag_backend.models_src.scan_result import ScanResult as SrcScanResult
from wcag_backend.models_src.violation import Violation as SrcViolation

from wcag_backend.database.models import ImpactLevel, WCAGLevel
from wcag_backend.utils.logger import get_logger

logger = get_logger("scanner_adapter")


class ScannerAdapter:
    """Adapter to use existing src/scanners with wcag-backend."""

    def __init__(self):
        """Initialize scanner adapter."""
        pass

    async def scan_single_page(
        self,
        url: str,
        scanners: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Scan a single page using existing scanners.

        Args:
            url: URL to scan
            scanners: List of scanner names to use (default: ["axe"])
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with scan results
        """
        try:
            logger.info(f"Starting single-page scan for {url}")

            # Use existing ResultsAggregator
            aggregator = ResultsAggregator(tools=scanners or ["axe"])
            result: SrcScanResult = await aggregator.scan(url)

            logger.info(f"Scan completed for {url}, score: {result.scores.overall}")

            # Convert to backend format
            return self._convert_scan_result(result)

        except Exception as e:
            logger.error(f"Scan failed for {url}: {e}")
            raise

    async def scan_site(
        self,
        url: str,
        max_pages: int = 10,
        max_depth: int = 3,
        scanners: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Scan multiple pages (site-wide scan).

        Args:
            url: Starting URL
            max_pages: Maximum pages to scan
            max_depth: Maximum crawl depth
            scanners: List of scanner names to use
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with aggregated scan results
        """
        try:
            logger.info(f"Starting site-wide scan for {url} (max {max_pages} pages)")

            # Use existing SiteScanner
            scanner = SiteScanner(
                max_pages=max_pages,
                max_depth=max_depth,
                tools=scanners or ["axe"],
                concurrent_scans=2
            )

            # Set progress callback if provided
            if progress_callback:
                scanner.set_progress_callback(progress_callback)

            result = await scanner.scan_site(url)

            logger.info(f"Site scan completed for {url}, pages scanned: {result.pages_scanned}")

            # Convert to backend format (aggregate from all pages)
            return self._convert_site_scan_result(result)

        except Exception as e:
            logger.error(f"Site scan failed for {url}: {e}")
            raise

    def _convert_scan_result(self, src_result: SrcScanResult) -> Dict:
        """
        Convert src.models.ScanResult to backend format.

        Args:
            src_result: ScanResult from src/scanners

        Returns:
            Dictionary with converted data
        """
        return {
            "score": round(src_result.scores.overall),
            "violations": [self._convert_violation(v) for v in src_result.violations],
            "duration": src_result.duration_seconds,
            "rules_checked": src_result.scores.total_rules_checked,
            "rules_passed": src_result.scores.total_rules_passed,
            "rules_failed": src_result.scores.total_rules_failed
        }

    def _convert_site_scan_result(self, result) -> Dict:
        """
        Convert site scan result to backend format.

        Args:
            result: SiteScanResult from src/scanners

        Returns:
            Dictionary with converted data
        """
        return {
            "score": round(result.overall_score),
            "violations": [self._convert_violation(v) for v in result.unique_violations],
            "duration": result.duration_seconds,
            "pages_scanned": result.pages_scanned,
            "rules_checked": result.total_rules_checked,
            "rules_passed": result.total_rules_passed,
            "rules_failed": result.total_rules_failed
        }

    def _convert_violation(self, src_violation: SrcViolation) -> Dict:
        """
        Convert src.models.Violation to backend Issue format.

        Args:
            src_violation: Violation from src/scanners

        Returns:
            Dictionary suitable for Issue model
        """
        # Map impact to ImpactLevel enum
        impact_map = {
            "critical": "critical",
            "serious": "serious",
            "moderate": "moderate",
            "minor": "minor"
        }

        # Map WCAG level
        wcag_level_map = {
            "A": "A",
            "AA": "AA",
            "AAA": "AAA"
        }

        # Get first instance for HTML snippet and selector
        instance = src_violation.instances[0] if src_violation.instances else None

        return {
            "description": src_violation.description,
            "impact": impact_map.get(src_violation.impact.value, "moderate"),
            "wcag_criteria": src_violation.wcag_criteria[0] if src_violation.wcag_criteria else None,
            "wcag_level": wcag_level_map.get(src_violation.wcag_level.value) if src_violation.wcag_level else None,
            "selector": instance.selector if instance else None,
            "html_snippet": instance.html[:500] if instance else None,  # Limit to 500 chars
            "how_to_fix": src_violation.help_text,
            "help_url": src_violation.help_url
        }
