"""Results aggregator for combining and deduplicating scan results."""

import asyncio
from typing import Optional
from datetime import datetime
import time

from src.models import (
    Violation,
    ScanResult,
    ScanStatus,
    ToolStatus,
    ScanScores
)
from src.scanners import (
    AxeScanner,
    Pa11yScanner,
    LighthouseScanner,
    HTMLValidatorScanner,
    ContrastChecker,
    SCANNERS
)
from src.utils.browser import BrowserManager
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ResultsAggregator:
    """Aggregates results from multiple scanners."""

    def __init__(self, tools: Optional[list[str]] = None):
        """
        Initialize the aggregator.

        Args:
            tools: List of tool names to run. Defaults to config setting.
        """
        config = get_config()
        self.tools = tools or config.scan.tools
        self._browser_manager: Optional[BrowserManager] = None

    async def scan(self, url: str) -> ScanResult:
        """
        Run all configured scanners and aggregate results.

        Args:
            url: URL to scan

        Returns:
            Aggregated scan result
        """
        start_time = time.time()

        # Initialize result
        result = ScanResult(
            url=url,
            status=ScanStatus.RUNNING,
            timestamp=datetime.utcnow()
        )

        try:
            # Start shared browser
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

            # Run scanners concurrently
            all_violations = []
            tool_statuses = {}
            scores = ScanScores()

            # Create scanner tasks
            tasks = []
            scanner_names = []

            for tool_name in self.tools:
                if tool_name not in SCANNERS:
                    logger.warning(f"Unknown scanner: {tool_name}, skipping")
                    continue

                scanner_class = SCANNERS[tool_name]

                # Create scanner with shared browser where applicable
                if tool_name in ["axe", "html_validator", "contrast"]:
                    scanner = scanner_class(browser_manager=self._browser_manager)
                else:
                    scanner = scanner_class()

                tasks.append(scanner.run(url))
                scanner_names.append(tool_name)

            # Run all scanners concurrently
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, (tool_name, task_result) in enumerate(zip(scanner_names, results)):
                    if isinstance(task_result, Exception):
                        logger.error(f"Scanner {tool_name} failed: {task_result}")
                        tool_statuses[tool_name] = ToolStatus(
                            name=tool_name,
                            status="error",
                            error=str(task_result)
                        )
                    else:
                        violations, status = task_result
                        all_violations.extend(violations)
                        tool_statuses[tool_name] = status

                        # Capture scores from specific scanners
                        if tool_name == "lighthouse" and hasattr(SCANNERS[tool_name], "score"):
                            # Get score from scanner instance
                            pass  # Score is captured in the status

            # Deduplicate violations
            deduplicated = self._deduplicate_violations(all_violations)

            # Calculate passes from axe
            total_passes = sum(
                status.rules_checked or 0
                for status in tool_statuses.values()
                if status.status == "success"
            )

            # Update result
            result.violations = deduplicated
            result.tools_used = tool_statuses
            result.summary.passes = total_passes
            result.finalize(time.time() - start_time)

            # Update tool-specific scores
            for tool_name, status in tool_statuses.items():
                if tool_name == "axe":
                    result.scores.axe = self._calculate_tool_score(
                        [v for v in deduplicated if "axe" in v.detected_by]
                    )
                elif tool_name == "lighthouse":
                    result.scores.lighthouse = self._calculate_tool_score(
                        [v for v in deduplicated if "lighthouse" in v.detected_by]
                    )
                elif tool_name == "pa11y":
                    result.scores.pa11y = self._calculate_tool_score(
                        [v for v in deduplicated if "pa11y" in v.detected_by]
                    )
                elif tool_name == "html_validator":
                    result.scores.html_validator = self._calculate_tool_score(
                        [v for v in deduplicated if "html_validator" in v.detected_by]
                    )

            logger.info(
                f"Scan completed: {len(deduplicated)} violations found "
                f"(score: {result.scores.overall})"
            )

            return result

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error = str(e)
            result.finalize(time.time() - start_time)
            return result

        finally:
            # Clean up browser
            if self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    def _deduplicate_violations(self, violations: list[Violation]) -> list[Violation]:
        """
        Deduplicate violations from multiple tools.

        Violations are considered duplicates if they have the same rule_id
        or affect the same element with similar descriptions.
        """
        unique_violations: dict[str, Violation] = {}

        for violation in violations:
            # Create a key based on rule_id and first instance selector
            first_selector = ""
            if violation.instances:
                first_selector = violation.instances[0].selector

            # Normalize rule_id for comparison
            normalized_rule = violation.rule_id.lower().replace("-", "_").replace(" ", "_")

            # Create compound key
            key = f"{normalized_rule}:{first_selector}"

            if key in unique_violations:
                # Merge with existing violation
                existing = unique_violations[key]
                existing.add_detected_by(violation.detected_by[0] if violation.detected_by else "unknown")
                existing.merge_instances(violation)

                # Upgrade impact if new one is more severe
                impact_order = {"critical": 4, "serious": 3, "moderate": 2, "minor": 1}
                if impact_order.get(violation.impact.value, 0) > impact_order.get(existing.impact.value, 0):
                    existing.impact = violation.impact

                # Merge WCAG criteria
                for criteria in violation.wcag_criteria:
                    if criteria not in existing.wcag_criteria:
                        existing.wcag_criteria.append(criteria)

            else:
                unique_violations[key] = violation

        return list(unique_violations.values())

    def _calculate_tool_score(self, violations: list[Violation]) -> float:
        """Calculate a score (0-100) based on violations."""
        if not violations:
            return 100.0

        # Weight by impact
        weights = {
            "critical": 25,
            "serious": 15,
            "moderate": 7,
            "minor": 3
        }

        penalty = sum(
            weights.get(v.impact.value, 5)
            for v in violations
        )

        return max(0.0, min(100.0, 100.0 - penalty))


async def run_scan(url: str, tools: Optional[list[str]] = None) -> ScanResult:
    """
    Convenience function to run a scan.

    Args:
        url: URL to scan
        tools: Optional list of tools to use

    Returns:
        Scan result
    """
    aggregator = ResultsAggregator(tools=tools)
    return await aggregator.scan(url)
