"""Lighthouse scanner implementation using subprocess."""

import asyncio
import json
import shutil
import tempfile
from typing import Optional
from pathlib import Path

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, get_wcag_level
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Lighthouse audit IDs to WCAG criteria mapping
LIGHTHOUSE_TO_WCAG = {
    "aria-allowed-attr": ["4.1.2"],
    "aria-hidden-body": ["4.1.2"],
    "aria-hidden-focus": ["4.1.2"],
    "aria-required-attr": ["4.1.2"],
    "aria-required-children": ["4.1.2"],
    "aria-required-parent": ["4.1.2"],
    "aria-roles": ["4.1.2"],
    "aria-valid-attr-value": ["4.1.2"],
    "aria-valid-attr": ["4.1.2"],
    "button-name": ["4.1.2"],
    "bypass": ["2.4.1"],
    "color-contrast": ["1.4.3"],
    "definition-list": ["1.3.1"],
    "dlitem": ["1.3.1"],
    "document-title": ["2.4.2"],
    "duplicate-id-active": ["4.1.1"],
    "duplicate-id-aria": ["4.1.1"],
    "form-field-multiple-labels": ["3.3.2"],
    "frame-title": ["2.4.1"],
    "html-has-lang": ["3.1.1"],
    "html-lang-valid": ["3.1.1"],
    "image-alt": ["1.1.1"],
    "input-image-alt": ["1.1.1"],
    "label": ["1.3.1", "4.1.2"],
    "link-name": ["2.4.4", "4.1.2"],
    "list": ["1.3.1"],
    "listitem": ["1.3.1"],
    "meta-refresh": ["2.2.1"],
    "meta-viewport": ["1.4.4"],
    "object-alt": ["1.1.1"],
    "tabindex": ["2.4.3"],
    "td-headers-attr": ["1.3.1"],
    "th-has-data-cells": ["1.3.1"],
    "valid-lang": ["3.1.2"],
    "video-caption": ["1.2.2"],
}


class LighthouseScanner(BaseScanner):
    """Scanner using Google Lighthouse."""

    name = "lighthouse"
    version = "11.0.0"

    def __init__(self):
        super().__init__()
        self._lighthouse_path = shutil.which("lighthouse")
        self._score: Optional[float] = None

    @property
    def score(self) -> Optional[float]:
        """Get the Lighthouse accessibility score."""
        return self._score

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Scan URL using Lighthouse.

        Args:
            url: URL to scan
            html_content: Ignored, lighthouse needs URL

        Returns:
            List of violations
        """
        if not self._lighthouse_path:
            logger.warning("Lighthouse not found. Install with: npm install -g lighthouse")
            return []

        try:
            # Create temp file for output
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                output_path = tmp.name

            # Run lighthouse
            process = await asyncio.create_subprocess_exec(
                self._lighthouse_path,
                url,
                "--output", "json",
                "--output-path", output_path,
                "--only-categories", "accessibility",
                "--chrome-flags", "--headless --no-sandbox --disable-gpu",
                "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=180
            )

            if process.returncode != 0:
                logger.warning(f"Lighthouse exited with code {process.returncode}")
                if stderr:
                    logger.debug(f"Lighthouse stderr: {stderr.decode()}")

            # Read results
            output_file = Path(output_path)
            if not output_file.exists():
                logger.error("Lighthouse output file not found")
                return []

            with open(output_file) as f:
                results = json.load(f)

            # Clean up temp file
            output_file.unlink(missing_ok=True)

            # Extract score
            categories = results.get("categories", {})
            accessibility = categories.get("accessibility", {})
            self._score = accessibility.get("score", 0) * 100

            # Extract violations from audits
            audits = results.get("audits", {})
            violations = []

            for audit_id, audit_data in audits.items():
                # Only process failed audits
                if audit_data.get("score") == 0:
                    violation = self._convert_audit(audit_id, audit_data)
                    if violation:
                        violations.append(violation)

            return violations

        except asyncio.TimeoutError:
            logger.error("Lighthouse scan timed out")
            return []
        except Exception as e:
            logger.error(f"Lighthouse scan failed: {e}")
            return []

    def _convert_audit(self, audit_id: str, audit_data: dict) -> Optional[Violation]:
        """Convert Lighthouse audit to our format."""
        # Skip informative audits
        if audit_data.get("scoreDisplayMode") == "informative":
            return None

        # Get WCAG criteria
        wcag_criteria = LIGHTHOUSE_TO_WCAG.get(audit_id, [])
        wcag_level = get_wcag_level(wcag_criteria[0]) if wcag_criteria else None

        # Determine impact based on audit weight
        weight = audit_data.get("weight", 1)
        if weight >= 10:
            impact = Impact.CRITICAL
        elif weight >= 5:
            impact = Impact.SERIOUS
        elif weight >= 2:
            impact = Impact.MODERATE
        else:
            impact = Impact.MINOR

        # Extract instances from items
        instances = []
        details = audit_data.get("details", {})
        items = details.get("items", [])

        for item in items[:20]:  # Limit to 20 instances
            html = item.get("node", {}).get("snippet", "")
            selector = item.get("node", {}).get("selector", "")

            if html or selector:
                instance = ViolationInstance(
                    html=html,
                    selector=selector,
                    fix_suggestion=item.get("node", {}).get("explanation", "")
                )
                instances.append(instance)

        if not instances:
            # Create a generic instance if no specific items
            instances.append(ViolationInstance(
                html="",
                selector="",
                fix_suggestion=audit_data.get("description", "")
            ))

        return Violation(
            id=f"lighthouse-{audit_id}",
            rule_id=audit_id,
            wcag_criteria=wcag_criteria,
            wcag_level=wcag_level,
            impact=impact,
            description=audit_data.get("title", ""),
            help_text=audit_data.get("description", ""),
            detected_by=["lighthouse"],
            instances=instances,
            tags=["lighthouse"]
        )
