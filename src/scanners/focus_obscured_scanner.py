"""Focus Not Obscured Scanner - WCAG 2.4.11 (Level AA)

Detects when keyboard focus indicator is partially or fully obscured by
author-created content (e.g., sticky headers, fixed footers, modals).
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FocusObscuredScanner(BaseScanner):
    """Scanner for focus obscured by fixed/sticky content."""

    name = "focus-obscured"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check for focus obscuration issues.

        Args:
            url: URL to scan
            html_content: Ignored, needs live page

        Returns:
            List of violations
        """
        if self._browser_manager is None:
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

        try:
            async with self._browser_manager.get_page(url) as page:
                return await self._check_focus_obscured(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_focus_obscured(self, page: Page) -> list[Violation]:
        """Run focus obscured checks."""
        violations = []

        # This scanner checks 2 rules
        self._rules_checked = 2

        # First, find all fixed/sticky positioned elements
        fixed_elements = await page.evaluate("""
            () => {
                const fixed = [];
                const allElements = document.querySelectorAll('*');

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        return el.tagName.toLowerCase() + '.' + classes[0];
                    }
                    return el.tagName.toLowerCase();
                }

                for (const el of allElements) {
                    const style = window.getComputedStyle(el);
                    const position = style.position;

                    if (position === 'fixed' || position === 'sticky') {
                        const rect = el.getBoundingClientRect();

                        // Only consider visible elements with size
                        if (rect.width > 0 && rect.height > 0 &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            parseFloat(style.opacity) > 0) {

                            fixed.push({
                                selector: getSelector(el),
                                position: position,
                                zIndex: style.zIndex,
                                rect: {
                                    top: rect.top,
                                    left: rect.left,
                                    right: rect.right,
                                    bottom: rect.bottom,
                                    width: rect.width,
                                    height: rect.height
                                },
                                html: el.outerHTML.substring(0, 200)
                            });
                        }
                    }
                }

                return fixed;
            }
        """)

        logger.info(f"Found {len(fixed_elements)} fixed/sticky elements")

        if len(fixed_elements) == 0:
            # No fixed content, no risk
            self._rules_passed = self._rules_checked
            return violations

        # Get all focusable elements
        focusable_selectors = await page.evaluate("""
            () => {
                const focusable = document.querySelectorAll(
                    'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        return el.tagName.toLowerCase() + '.' + classes[0];
                    }
                    return el.tagName.toLowerCase() + ':nth-of-type(' + (Array.from(el.parentElement?.children || []).indexOf(el) + 1) + ')';
                }

                return Array.from(focusable).slice(0, 30).map(el => getSelector(el));
            }
        """)

        logger.info(f"Testing {len(focusable_selectors)} focusable elements")

        # Test each focusable element
        issues = []
        tested_count = 0

        for selector in focusable_selectors[:30]:  # Limit to prevent timeout
            try:
                issue = await self._test_element_obscured(page, selector, fixed_elements)
                if issue:
                    issues.append(issue)
                tested_count += 1
            except Exception as e:
                logger.debug(f"Error testing {selector}: {e}")
                continue

        # Convert issues to violations
        rule_types_failed = set()
        for issue in issues:
            violation = self._create_violation(issue)
            if violation:
                violations.append(violation)
                rule_types_failed.add(issue.get("obscured_by"))

        # Update rules failed count
        self._rules_failed = min(len(rule_types_failed), self._rules_checked)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    async def _test_element_obscured(
        self,
        page: Page,
        selector: str,
        fixed_elements: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Test if an element's focus is obscured."""

        result = await page.evaluate("""
            ({ selector, fixedElements }) => {
                const element = document.querySelector(selector);
                if (!element) return null;

                // Focus the element
                element.focus();

                // Get element's bounding rect
                const rect = element.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return null;

                // Check focus indicator size (using outline or border)
                const style = window.getComputedStyle(element);
                const outlineWidth = parseFloat(style.outlineWidth) || 0;
                const borderWidth = parseFloat(style.borderWidth) || 0;
                const focusIndicatorSize = Math.max(outlineWidth, borderWidth, 2); // At least 2px

                // Expand rect by focus indicator size
                const focusRect = {
                    top: rect.top - focusIndicatorSize,
                    left: rect.left - focusIndicatorSize,
                    right: rect.right + focusIndicatorSize,
                    bottom: rect.bottom + focusIndicatorSize
                };

                // Check if any fixed element obscures the focus
                const obscuringElements = [];

                for (const fixed of fixedElements) {
                    const fixedRect = fixed.rect;

                    // Check for overlap
                    const overlaps = !(
                        focusRect.right < fixedRect.left ||
                        focusRect.left > fixedRect.right ||
                        focusRect.bottom < fixedRect.top ||
                        focusRect.top > fixedRect.bottom
                    );

                    if (overlaps) {
                        // Calculate overlap area
                        const overlapLeft = Math.max(focusRect.left, fixedRect.left);
                        const overlapRight = Math.min(focusRect.right, fixedRect.right);
                        const overlapTop = Math.max(focusRect.top, fixedRect.top);
                        const overlapBottom = Math.min(focusRect.bottom, fixedRect.bottom);

                        const overlapWidth = Math.max(0, overlapRight - overlapLeft);
                        const overlapHeight = Math.max(0, overlapBottom - overlapTop);
                        const overlapArea = overlapWidth * overlapHeight;

                        const elementArea = (focusRect.right - focusRect.left) * (focusRect.bottom - focusRect.top);
                        const percentObscured = (overlapArea / elementArea) * 100;

                        // WCAG 2.4.11 (AA): Focus indicator must not be entirely hidden
                        // We'll flag if more than 50% is obscured as a warning
                        if (percentObscured > 50) {
                            obscuringElements.push({
                                selector: fixed.selector,
                                position: fixed.position,
                                percentObscured: Math.round(percentObscured),
                                html: fixed.html
                            });
                        }
                    }
                }

                // Blur the element
                element.blur();

                if (obscuringElements.length > 0) {
                    return {
                        selector: selector,
                        element: element.outerHTML.substring(0, 300),
                        obscuredBy: obscuringElements
                    };
                }

                return null;
            }
        """, {"selector": selector, "fixedElements": fixed_elements})

        return result

    def _create_violation(self, issue: dict) -> Optional[Violation]:
        """Create violation from issue data."""
        obscured_by = issue.get("obscuredBy", [])
        if not obscured_by:
            return None

        # Get the worst obscuration
        worst = max(obscured_by, key=lambda x: x.get("percentObscured", 0))
        percent = worst.get("percentObscured", 0)

        # Determine impact based on obscuration percentage
        if percent >= 80:
            impact = Impact.CRITICAL
            description = f"Focus indicator is {percent}% obscured by {worst.get('position')} positioned content"
        else:
            impact = Impact.SERIOUS
            description = f"Focus indicator is {percent}% obscured by {worst.get('position')} positioned content"

        help_text = (
            f"Adjust z-index or positioning of {worst.get('selector')} to ensure focus indicators "
            f"are visible. Consider adding padding/margin to prevent overlap, or reposition sticky/fixed content."
        )

        return Violation(
            id=f"focus-obscured-{hash(issue.get('selector', '')) % 10000}",
            rule_id="focus-not-obscured",
            wcag_criteria=["2.4.11"],
            wcag_level=WCAGLevel.AA,
            impact=impact,
            description=description,
            help_text=help_text,
            help_url="https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html",
            detected_by=["focus-obscured"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=f"Obscured by: {worst.get('selector')}. {help_text}"
            )],
            tags=["focus", "sticky", "fixed", "wcag2411", "level-aa"]
        )
