"""Pa11y scanner implementation using subprocess."""

import asyncio
import json
import shutil
from typing import Optional

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, get_wcag_level
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Pa11yScanner(BaseScanner):
    """Scanner using Pa11y CLI tool."""

    name = "pa11y"
    version = "6.2.3"

    def __init__(self):
        super().__init__()
        self._pa11y_path = shutil.which("pa11y")

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Scan URL using Pa11y.

        Args:
            url: URL to scan
            html_content: Ignored, pa11y needs URL

        Returns:
            List of violations
        """
        if not self._pa11y_path:
            logger.warning("Pa11y not found. Install with: npm install -g pa11y")
            return []

        try:
            # Run pa11y command
            process = await asyncio.create_subprocess_exec(
                self._pa11y_path,
                url,
                "--reporter", "json",
                "--standard", "WCAG2AA",
                "--timeout", "60000",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120
            )

            # Pa11y exits with 2 if issues found, that's normal
            if process.returncode not in (0, 2):
                if stderr:
                    logger.warning(f"Pa11y stderr: {stderr.decode()}")

            if not stdout:
                return []

            # Parse JSON output
            try:
                issues = json.loads(stdout.decode())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Pa11y output: {e}")
                return []

            # Convert to violations
            violations = []
            for issue in issues:
                violation = self._convert_issue(issue)
                if violation:
                    violations.append(violation)

            return violations

        except asyncio.TimeoutError:
            logger.error("Pa11y scan timed out")
            return []
        except Exception as e:
            logger.error(f"Pa11y scan failed: {e}")
            return []

    def _convert_issue(self, issue: dict) -> Optional[Violation]:
        """Convert Pa11y issue to our format."""
        # Map Pa11y type to impact
        type_to_impact = {
            "error": Impact.SERIOUS,
            "warning": Impact.MODERATE,
            "notice": Impact.MINOR
        }

        issue_type = issue.get("type", "warning")
        impact = type_to_impact.get(issue_type, Impact.MODERATE)

        # Extract WCAG code
        code = issue.get("code", "")
        wcag_criteria = []
        wcag_level = None

        # Try to extract WCAG criteria from code
        # Pa11y codes often contain WCAG references
        if "WCAG2" in code:
            # Extract pattern like WCAG2AA.Principle1.Guideline1_1.1_1_1
            parts = code.split(".")
            for part in parts:
                if part.startswith("Guideline"):
                    # Extract from "Guideline1_1" format
                    guideline = part.replace("Guideline", "").replace("_", ".")
                    if guideline:
                        wcag_criteria.append(guideline)
                elif "_" in part and part[0].isdigit():
                    # Format like "1_1_1"
                    criteria = part.replace("_", ".")
                    wcag_criteria.append(criteria)

            if wcag_criteria:
                wcag_level = get_wcag_level(wcag_criteria[0])

        instance = ViolationInstance(
            html=issue.get("context", ""),
            selector=issue.get("selector", ""),
            fix_suggestion=issue.get("message", "")
        )

        return Violation(
            id=f"pa11y-{hash(code) % 100000}",
            rule_id=code,
            wcag_criteria=wcag_criteria,
            wcag_level=wcag_level,
            impact=impact,
            description=issue.get("message", ""),
            help_text=issue.get("message", ""),
            detected_by=["pa11y"],
            instances=[instance],
            tags=[issue_type, code]
        )
