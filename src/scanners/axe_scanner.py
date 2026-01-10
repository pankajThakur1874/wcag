"""Axe-core scanner implementation."""

import json
from typing import Optional
from pathlib import Path

from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, get_wcag_level
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Axe-core JavaScript (minified version will be injected)
AXE_CORE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.3/axe.min.js"


class AxeScanner(BaseScanner):
    """Scanner using axe-core library."""

    name = "axe"
    version = "4.8.3"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Scan URL using axe-core.

        Args:
            url: URL to scan
            html_content: Ignored, axe needs live page

        Returns:
            List of violations
        """
        if self._browser_manager is None:
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

        try:
            async with self._browser_manager.get_page(url) as page:
                return await self._run_axe(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _run_axe(self, page: Page) -> list[Violation]:
        """Run axe-core on the page."""
        # Inject axe-core
        logger.debug("Injecting axe-core...")
        await page.add_script_tag(url=AXE_CORE_CDN)

        # Wait for axe to load
        await page.wait_for_function("typeof axe !== 'undefined'")

        # Run axe analysis
        logger.debug("Running axe analysis...")
        results = await page.evaluate("""
            async () => {
                const results = await axe.run(document, {
                    runOnly: {
                        type: 'tag',
                        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']
                    }
                });
                return JSON.stringify(results);
            }
        """)

        axe_results = json.loads(results)

        # Count rules checked (passes + violations + incomplete)
        passes = len(axe_results.get("passes", []))
        violations_count = len(axe_results.get("violations", []))
        incomplete = len(axe_results.get("incomplete", []))

        # Set rules checked for percentage calculation
        self._rules_checked = passes + violations_count + incomplete
        self._rules_passed = passes
        self._rules_failed = violations_count

        logger.debug(f"Axe: {passes} passed, {violations_count} failed, {incomplete} incomplete")

        # Convert to our violation format
        violations = []
        for violation_data in axe_results.get("violations", []):
            violation = self._convert_violation(violation_data)
            violations.append(violation)

        return violations

    def _convert_violation(self, axe_violation: dict) -> Violation:
        """Convert axe violation to our format."""
        # Map axe impact to our impact levels
        impact_map = {
            "critical": Impact.CRITICAL,
            "serious": Impact.SERIOUS,
            "moderate": Impact.MODERATE,
            "minor": Impact.MINOR
        }

        # Extract WCAG criteria from tags
        wcag_criteria = []
        for tag in axe_violation.get("tags", []):
            if tag.startswith("wcag") and len(tag) > 4:
                # Extract criteria like "wcag111" -> "1.1.1"
                criteria_part = tag[4:]
                if criteria_part.isdigit() and len(criteria_part) >= 3:
                    formatted = f"{criteria_part[0]}.{criteria_part[1]}.{criteria_part[2:]}"
                    wcag_criteria.append(formatted)

        # Get WCAG level from first criteria
        wcag_level = None
        if wcag_criteria:
            wcag_level = get_wcag_level(wcag_criteria[0])

        # Convert instances (nodes)
        instances = []
        for node in axe_violation.get("nodes", []):
            instance = ViolationInstance(
                html=node.get("html", ""),
                selector=", ".join(node.get("target", [])) if node.get("target") else "",
                xpath=node.get("xpath", [""])[0] if node.get("xpath") else None,
                fix_suggestion=node.get("failureSummary", "")
            )
            instances.append(instance)

        return Violation(
            id=f"axe-{axe_violation.get('id', 'unknown')}",
            rule_id=axe_violation.get("id", "unknown"),
            wcag_criteria=wcag_criteria,
            wcag_level=wcag_level,
            impact=impact_map.get(axe_violation.get("impact", "moderate"), Impact.MODERATE),
            description=axe_violation.get("description", ""),
            help_text=axe_violation.get("help", ""),
            help_url=axe_violation.get("helpUrl", ""),
            detected_by=["axe"],
            instances=instances,
            tags=axe_violation.get("tags", [])
        )
