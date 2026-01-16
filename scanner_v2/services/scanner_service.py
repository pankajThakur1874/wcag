"""Scanner service wrapper for existing V1 scanners."""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent src to path to import existing scanners
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, calculate_duration_ms
from scanner_v2.utils.exceptions import ScannerException, ScannerExecutionError, ScannerTimeoutError
from scanner_v2.database.models import ImpactLevel, WCAGLevel, Principle
from scanner_v2.services.screenshot_service import screenshot_service

# Import V1 scanners with error handling
try:
    from src.scanners import (
        AxeScanner, HTMLValidatorScanner, ContrastChecker, KeyboardScanner,
        ARIAScanner, FormsScanner, SEOAccessibilityScanner, LinkTextScanner,
        ImageAltScanner, MediaScanner, TouchTargetScanner, ReadabilityScanner,
        InteractiveScanner, Pa11yScanner, LighthouseScanner
    )
    from src.utils.browser import BrowserManager
    V1_SCANNERS_AVAILABLE = True
except ImportError as e:
    V1_SCANNERS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Create placeholder to avoid NameError
    BrowserManager = None
    AxeScanner = HTMLValidatorScanner = ContrastChecker = None
    KeyboardScanner = ARIAScanner = FormsScanner = None
    SEOAccessibilityScanner = LinkTextScanner = ImageAltScanner = None
    MediaScanner = TouchTargetScanner = ReadabilityScanner = None
    InteractiveScanner = Pa11yScanner = LighthouseScanner = None

logger = get_logger("scanner_service")

if not V1_SCANNERS_AVAILABLE:
    logger.error(f"Failed to import V1 scanners: {IMPORT_ERROR}")
    logger.error("V1 scanner functionality will be unavailable. Please ensure all scanner dependencies are installed.")


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
    """Service for running accessibility scanners using V1 implementations."""

    def __init__(self):
        """Initialize scanner service."""
        self.available_scanners = [
            "axe", "html_validator", "contrast", "keyboard", "aria", "forms",
            "seo", "link_text", "image_alt", "media", "touch_target",
            "readability", "interactive", "pa11y", "lighthouse"
        ]

        # Map scanner names to classes
        self.scanner_classes = {
            "axe": AxeScanner,
            "html_validator": HTMLValidatorScanner,
            "contrast": ContrastChecker,
            "keyboard": KeyboardScanner,
            "aria": ARIAScanner,
            "forms": FormsScanner,
            "seo": SEOAccessibilityScanner,
            "link_text": LinkTextScanner,
            "image_alt": ImageAltScanner,
            "media": MediaScanner,
            "touch_target": TouchTargetScanner,
            "readability": ReadabilityScanner,
            "interactive": InteractiveScanner,
            "pa11y": Pa11yScanner,
            "lighthouse": LighthouseScanner
        }

        # Scanners that don't accept browser_manager (use subprocess)
        self.subprocess_scanners = ["pa11y", "lighthouse"]

    async def scan_page(
        self,
        url: str,
        scan_id: str,
        page_id: str,
        scanners: Optional[List[str]] = None,
        screenshot_enabled: bool = True,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Scan page with specified scanners using V1 implementations with shared browser.

        Args:
            url: URL being scanned
            scan_id: Scan ID for screenshot organization
            page_id: Page ID for screenshot naming
            scanners: List of scanner names to run (default: all)
            screenshot_enabled: Whether to capture screenshot
            timeout: Timeout in milliseconds

        Returns:
            Dictionary containing scanner results and screenshot path
        """
        # Check if V1 scanners are available
        if not V1_SCANNERS_AVAILABLE:
            raise ScannerException(
                f"V1 scanners are not available. Import error: {IMPORT_ERROR}. "
                "Please install all required dependencies."
            )

        if scanners is None:
            scanners = self.available_scanners

        logger.info(f"Scanning {url} with scanners: {', '.join(scanners)}")

        # Create shared browser manager for all scanners
        browser_manager = BrowserManager(stealth_mode=True)
        await browser_manager.start()

        results = {}
        screenshot_path = None
        page_title = None
        status_code = None

        try:
            # Get page once and reuse for all operations
            async with browser_manager.get_page(url) as page:
                # Capture page title and status
                try:
                    page_title = await page.title()
                    # Status code is not directly available in context manager
                    # but we can assume 200 if page loaded
                    status_code = 200
                except Exception as e:
                    logger.warning(f"Failed to get page info: {e}")

                # Capture screenshot if enabled
                if screenshot_enabled:
                    try:
                        screenshot_path = await screenshot_service.capture_full_page(
                            page, scan_id, page_id, url
                        )
                        logger.info(f"Screenshot captured: {screenshot_path}")
                    except Exception as e:
                        logger.error(f"Screenshot capture failed: {e}")

                # Now run scanners sequentially with the SAME browser instance
                # We'll navigate to the page for each scanner to ensure fresh state
                for scanner_name in scanners:
                    if scanner_name not in self.available_scanners:
                        logger.warning(f"Unknown scanner: {scanner_name} - skipping")
                        continue

                    logger.info(f"Running scanner: {scanner_name}")

                    try:
                        result = await self._run_scanner(
                            scanner_name, url, browser_manager, timeout
                        )
                        results[scanner_name] = result
                        logger.info(
                            f"{scanner_name} scan returned: {len(result.violations)} violations, "
                            f"success={result.success}"
                        )
                    except Exception as e:
                        logger.error(f"{scanner_name} failed with exception: {e}")
                        results[scanner_name] = ScannerResult(
                            scanner_name=scanner_name,
                            success=False,
                            violations=[],
                            error=str(e)
                        )

        finally:
            # Always cleanup browser
            await browser_manager.stop()

        return {
            "scanner_results": results,
            "screenshot_path": screenshot_path,
            "title": page_title,
            "status_code": status_code
        }

    async def _run_scanner(
        self,
        scanner_name: str,
        url: str,
        browser_manager: BrowserManager,
        timeout: int
    ) -> ScannerResult:
        """
        Run individual V1 scanner with shared browser.

        Args:
            scanner_name: Scanner name
            url: URL
            browser_manager: Shared browser manager instance (not used for subprocess scanners)
            timeout: Timeout in milliseconds

        Returns:
            Scanner result
        """
        start_time = utc_now()

        try:
            scanner_class = self.scanner_classes.get(scanner_name)
            if not scanner_class:
                raise ScannerExecutionError(f"Unknown scanner: {scanner_name}")

            # Create scanner instance
            # Subprocess scanners (Pa11y, Lighthouse) don't accept browser_manager
            if scanner_name in self.subprocess_scanners:
                scanner = scanner_class()
                logger.info(f"{scanner_name} uses subprocess (runs its own Chrome instance)")
            else:
                scanner = scanner_class(browser_manager=browser_manager)

            # Run scanner with timeout (V1 scanners accept url and optional html_content)
            violations, tool_status = await asyncio.wait_for(
                scanner.run(url, None),  # html_content=None, let scanner fetch
                timeout=timeout / 1000  # Convert ms to seconds
            )

            duration_ms = calculate_duration_ms(start_time)

            # Convert V1 violations to V2 format
            normalized_violations = self._normalize_v1_violations(violations, scanner_name)

            logger.info(f"{scanner_name} scan complete: {len(normalized_violations)} violations in {duration_ms}ms")

            return ScannerResult(
                scanner_name=scanner_name,
                success=tool_status.status == "success",
                violations=normalized_violations,
                raw_result={
                    "tool_status": {
                        "rules_checked": tool_status.rules_checked,
                        "rules_passed": tool_status.rules_passed,
                        "rules_failed": tool_status.rules_failed,
                        "score": tool_status.score
                    }
                },
                duration_ms=duration_ms
            )

        except asyncio.TimeoutError:
            duration_ms = calculate_duration_ms(start_time)
            logger.error(f"{scanner_name} scan timed out after {duration_ms}ms")
            raise ScannerTimeoutError(f"{scanner_name} timed out")

        except Exception as e:
            duration_ms = calculate_duration_ms(start_time)
            logger.error(f"{scanner_name} scan failed: {e}")
            raise ScannerExecutionError(f"{scanner_name} failed: {e}")

    def _normalize_v1_violations(
        self,
        violations: List[Any],
        scanner_name: str
    ) -> List[Dict[str, Any]]:
        """
        Normalize V1 violations to V2 format.

        Args:
            violations: V1 violation objects
            scanner_name: Scanner name

        Returns:
            Normalized violations
        """
        normalized = []

        for violation in violations:
            # Map V1 Impact enum to V2 format
            impact_map = {
                "critical": ImpactLevel.CRITICAL.value,
                "serious": ImpactLevel.SERIOUS.value,
                "moderate": ImpactLevel.MODERATE.value,
                "minor": ImpactLevel.MINOR.value,
            }

            impact_str = violation.impact.value if hasattr(violation.impact, 'value') else str(violation.impact)
            impact = impact_map.get(impact_str.lower(), ImpactLevel.MODERATE.value)

            # Get WCAG level
            wcag_level = WCAGLevel.AA.value  # Default
            if violation.wcag_level:
                wcag_level_str = violation.wcag_level.value if hasattr(violation.wcag_level, 'value') else str(violation.wcag_level)
                wcag_level = wcag_level_str

            # Determine principle from WCAG criteria
            principle = Principle.PERCEIVABLE.value  # Default
            if violation.wcag_criteria:
                first_criterion = violation.wcag_criteria[0]
                if first_criterion.startswith("2."):
                    principle = Principle.OPERABLE.value
                elif first_criterion.startswith("3."):
                    principle = Principle.UNDERSTANDABLE.value
                elif first_criterion.startswith("4."):
                    principle = Principle.ROBUST.value

            # Convert instances
            instances = []
            for instance in violation.instances:
                # Try to extract additional data if available
                instance_data = None
                if hasattr(instance, '__dict__'):
                    # Extract non-standard fields as data
                    extra_data = {}
                    for key, value in instance.__dict__.items():
                        if key not in ['html', 'selector', 'xpath', 'fix_suggestion'] and value is not None:
                            extra_data[key] = str(value)

                    if extra_data:
                        import json
                        instance_data = json.dumps(extra_data, indent=2)

                instances.append({
                    "selector": instance.selector or "",
                    "html": instance.html or "",
                    "failure_summary": instance.fix_suggestion or "",
                    "data": instance_data
                })

            normalized.append({
                "rule_id": violation.rule_id,
                "description": violation.description,
                "help": violation.help_text,
                "help_url": violation.help_url or "",
                "impact": impact,
                "wcag_criteria": violation.wcag_criteria or [],
                "wcag_level": wcag_level,
                "principle": principle,
                "instances": instances,
                "detected_by": [scanner_name]  # Wrap in list as Issue model expects List[str]
            })

        return normalized


# Global scanner service instance
scanner_service = ScannerService()
