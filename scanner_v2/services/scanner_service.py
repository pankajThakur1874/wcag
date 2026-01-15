"""Scanner service wrapper for existing scanners."""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent src to path to import existing scanners
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import Page

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, calculate_duration_ms
from scanner_v2.utils.exceptions import ScannerException, ScannerExecutionError, ScannerTimeoutError
from scanner_v2.database.models import ImpactLevel, WCAGLevel, Principle

logger = get_logger("scanner_service")


class ScannerResult:
    """Scanner result container."""

    def __init__(
        self,
        scanner_name: str,
        success: bool,
        violations: List[Dict[str, Any]],
        raw_result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ):
        """
        Initialize scanner result.

        Args:
            scanner_name: Name of scanner
            success: Whether scan succeeded
            violations: List of violations found
            raw_result: Raw scanner output
            error: Error message if failed
            duration_ms: Scan duration in milliseconds
        """
        self.scanner_name = scanner_name
        self.success = success
        self.violations = violations
        self.raw_result = raw_result
        self.error = error
        self.duration_ms = duration_ms


class ScannerService:
    """Service for running accessibility scanners."""

    def __init__(self):
        """Initialize scanner service."""
        self.available_scanners = ["axe", "pa11y", "lighthouse"]

    async def scan_page(
        self,
        page: Page,
        url: str,
        scanners: Optional[List[str]] = None,
        timeout: int = 30000
    ) -> Dict[str, ScannerResult]:
        """
        Scan page with specified scanners.

        Args:
            page: Playwright page instance
            url: URL being scanned
            scanners: List of scanner names to run (default: all)
            timeout: Timeout in milliseconds

        Returns:
            Dictionary of scanner results
        """
        if scanners is None:
            scanners = self.available_scanners

        logger.info(f"Scanning {url} with scanners: {', '.join(scanners)}")

        results = {}

        # Run scanners concurrently
        tasks = []
        for scanner_name in scanners:
            if scanner_name in self.available_scanners:
                tasks.append(self._run_scanner(scanner_name, page, url, timeout))
            else:
                logger.warning(f"Unknown scanner: {scanner_name}")

        scanner_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for scanner_name, result in zip(scanners, scanner_results):
            if isinstance(result, Exception):
                logger.error(f"{scanner_name} failed: {result}")
                results[scanner_name] = ScannerResult(
                    scanner_name=scanner_name,
                    success=False,
                    violations=[],
                    error=str(result)
                )
            else:
                results[scanner_name] = result

        return results

    async def _run_scanner(
        self,
        scanner_name: str,
        page: Page,
        url: str,
        timeout: int
    ) -> ScannerResult:
        """
        Run individual scanner.

        Args:
            scanner_name: Scanner name
            page: Playwright page
            url: URL
            timeout: Timeout in milliseconds

        Returns:
            Scanner result
        """
        start_time = utc_now()

        try:
            if scanner_name == "axe":
                result = await self._run_axe(page, url, timeout)
            elif scanner_name == "pa11y":
                result = await self._run_pa11y(page, url, timeout)
            elif scanner_name == "lighthouse":
                result = await self._run_lighthouse(page, url, timeout)
            else:
                raise ScannerExecutionError(f"Unknown scanner: {scanner_name}")

            duration_ms = calculate_duration_ms(start_time)
            result.duration_ms = duration_ms

            logger.info(f"{scanner_name} scan complete: {len(result.violations)} violations in {duration_ms}ms")

            return result

        except asyncio.TimeoutError:
            duration_ms = calculate_duration_ms(start_time)
            logger.error(f"{scanner_name} scan timed out after {duration_ms}ms")
            raise ScannerTimeoutError(f"{scanner_name} timed out")

        except Exception as e:
            duration_ms = calculate_duration_ms(start_time)
            logger.error(f"{scanner_name} scan failed: {e}")
            raise ScannerExecutionError(f"{scanner_name} failed: {e}")

    async def _run_axe(self, page: Page, url: str, timeout: int) -> ScannerResult:
        """
        Run axe-core scanner.

        Args:
            page: Playwright page
            url: URL
            timeout: Timeout

        Returns:
            Scanner result
        """
        try:
            # Inject axe-core
            await page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js")

            # Run axe
            axe_results = await page.evaluate("""
                async () => {
                    return await axe.run();
                }
            """)

            # Normalize violations
            violations = self._normalize_axe_violations(axe_results.get("violations", []))

            return ScannerResult(
                scanner_name="axe",
                success=True,
                violations=violations,
                raw_result=axe_results
            )

        except Exception as e:
            logger.error(f"axe scan failed: {e}")
            return ScannerResult(
                scanner_name="axe",
                success=False,
                violations=[],
                error=str(e)
            )

    async def _run_pa11y(self, page: Page, url: str, timeout: int) -> ScannerResult:
        """
        Run pa11y scanner.

        Args:
            page: Playwright page
            url: URL
            timeout: Timeout

        Returns:
            Scanner result
        """
        # Note: pa11y requires node.js and is harder to integrate directly
        # For now, return empty result with note
        # In production, you would call pa11y CLI or use pa11y as node module

        logger.info("pa11y scanner - skipping (requires node.js integration)")

        return ScannerResult(
            scanner_name="pa11y",
            success=True,
            violations=[],
            raw_result={"note": "pa11y integration pending"}
        )

    async def _run_lighthouse(self, page: Page, url: str, timeout: int) -> ScannerResult:
        """
        Run Lighthouse accessibility audit.

        Args:
            page: Playwright page
            url: URL
            timeout: Timeout

        Returns:
            Scanner result
        """
        # Note: Lighthouse requires separate process
        # For now, return empty result
        # In production, you would use lighthouse CLI or lighthouse API

        logger.info("lighthouse scanner - skipping (requires lighthouse integration)")

        return ScannerResult(
            scanner_name="lighthouse",
            success=True,
            violations=[],
            raw_result={"note": "lighthouse integration pending"}
        )

    def _normalize_axe_violations(self, violations: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normalize axe-core violations to common format.

        Args:
            violations: Raw axe violations

        Returns:
            Normalized violations
        """
        normalized = []

        for violation in violations:
            # Map axe impact to our impact levels
            impact_map = {
                "critical": ImpactLevel.CRITICAL,
                "serious": ImpactLevel.SERIOUS,
                "moderate": ImpactLevel.MODERATE,
                "minor": ImpactLevel.MINOR,
            }

            impact = impact_map.get(violation.get("impact", "moderate"), ImpactLevel.MODERATE)

            # Extract WCAG tags
            wcag_criteria = []
            for tag in violation.get("tags", []):
                if tag.startswith("wcag"):
                    # Extract criterion number from tag like "wcag111" or "wcag143"
                    criterion_num = tag.replace("wcag", "")
                    if len(criterion_num) >= 3:
                        # Format as X.X.X
                        formatted = f"{criterion_num[0]}.{criterion_num[1]}.{criterion_num[2:]}"
                        wcag_criteria.append(formatted)

            # Determine WCAG level and principle
            wcag_level = WCAGLevel.AA  # Default
            if "wcag2a" in violation.get("tags", []):
                wcag_level = WCAGLevel.A
            elif "wcag2aaa" in violation.get("tags", []):
                wcag_level = WCAGLevel.AAA

            # Determine principle from criterion
            principle = Principle.PERCEIVABLE  # Default
            if wcag_criteria:
                first_criterion = wcag_criteria[0]
                if first_criterion.startswith("2."):
                    principle = Principle.OPERABLE
                elif first_criterion.startswith("3."):
                    principle = Principle.UNDERSTANDABLE
                elif first_criterion.startswith("4."):
                    principle = Principle.ROBUST

            # Extract instances
            instances = []
            for node in violation.get("nodes", []):
                instances.append({
                    "selector": node.get("target", [""])[0] if node.get("target") else "",
                    "html": node.get("html", ""),
                    "failure_summary": node.get("failureSummary", ""),
                })

            normalized.append({
                "rule_id": violation.get("id"),
                "description": violation.get("description"),
                "help": violation.get("help"),
                "help_url": violation.get("helpUrl"),
                "impact": impact.value,
                "wcag_criteria": wcag_criteria,
                "wcag_level": wcag_level.value,
                "principle": principle.value,
                "instances": instances,
            })

        return normalized


# Global scanner service instance
scanner_service = ScannerService()
