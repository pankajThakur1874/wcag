"""Keyboard accessibility scanner implementation."""

from typing import Optional
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeyboardScanner(BaseScanner):
    """Scanner for keyboard accessibility issues."""

    name = "keyboard"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check keyboard accessibility.

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
                return await self._check_keyboard(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_keyboard(self, page: Page) -> list[Violation]:
        """Run keyboard accessibility checks."""
        violations = []

        # This scanner checks 7 rules
        self._rules_checked = 7

        # Check for various keyboard issues
        issues = await page.evaluate("""
            () => {
                const issues = [];

                // 1. Check for positive tabindex (disrupts natural tab order)
                const positiveTabindex = document.querySelectorAll('[tabindex]:not([tabindex="-1"]):not([tabindex="0"])');
                for (const el of positiveTabindex) {
                    const tabindex = parseInt(el.getAttribute('tabindex'));
                    if (tabindex > 0) {
                        issues.push({
                            type: 'positive-tabindex',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el),
                            tabindex: tabindex
                        });
                    }
                }

                // 2. Check for mouse-only handlers without keyboard equivalents
                const mouseOnlyElements = document.querySelectorAll('[onclick], [onmousedown], [onmouseup]');
                for (const el of mouseOnlyElements) {
                    const hasKeyHandler = el.hasAttribute('onkeydown') ||
                                         el.hasAttribute('onkeyup') ||
                                         el.hasAttribute('onkeypress');
                    const isNativeInteractive = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName);

                    if (!hasKeyHandler && !isNativeInteractive) {
                        issues.push({
                            type: 'mouse-only',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el)
                        });
                    }
                }

                // 3. Check for elements with click handlers but no role/tabindex
                const clickableNonInteractive = document.querySelectorAll('div[onclick], span[onclick], div[class*="click"], span[class*="click"]');
                for (const el of clickableNonInteractive) {
                    const hasRole = el.hasAttribute('role');
                    const hasTabindex = el.hasAttribute('tabindex');

                    if (!hasRole && !hasTabindex) {
                        issues.push({
                            type: 'non-interactive-clickable',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el)
                        });
                    }
                }

                // 4. Check for focus visible issues (outline: none without alternative)
                const allFocusable = document.querySelectorAll('a, button, input, select, textarea, [tabindex]');
                for (const el of allFocusable) {
                    const style = window.getComputedStyle(el);
                    const focusStyle = window.getComputedStyle(el, ':focus');

                    if (style.outline === 'none' || style.outline === '0px none') {
                        // Check if there's a box-shadow or border that might serve as focus indicator
                        // This is a heuristic and may have false positives
                        issues.push({
                            type: 'focus-not-visible',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el),
                            outline: style.outline
                        });
                    }
                }

                // 5. Check for accesskey attributes (can conflict with AT shortcuts)
                const accesskeyElements = document.querySelectorAll('[accesskey]');
                for (const el of accesskeyElements) {
                    issues.push({
                        type: 'accesskey-used',
                        element: el.outerHTML.substring(0, 200),
                        selector: getSelector(el),
                        accesskey: el.getAttribute('accesskey')
                    });
                }

                // 6. Check for scroll containers without keyboard access
                const scrollContainers = document.querySelectorAll('*');
                for (const el of scrollContainers) {
                    const style = window.getComputedStyle(el);
                    const isScrollable = (style.overflow === 'scroll' || style.overflow === 'auto' ||
                                         style.overflowY === 'scroll' || style.overflowY === 'auto') &&
                                        (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth);

                    if (isScrollable && !el.hasAttribute('tabindex') &&
                        !['BODY', 'HTML', 'TEXTAREA'].includes(el.tagName)) {
                        issues.push({
                            type: 'non-focusable-scroll',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el)
                        });
                    }
                }

                // 7. Check for autofocus (can disorient users)
                const autofocusElements = document.querySelectorAll('[autofocus]');
                for (const el of autofocusElements) {
                    issues.push({
                        type: 'autofocus-used',
                        element: el.outerHTML.substring(0, 200),
                        selector: getSelector(el)
                    });
                }

                return issues;

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        return el.tagName.toLowerCase() + '.' + el.className.split(' ')[0];
                    }
                    return el.tagName.toLowerCase();
                }
            }
        """)

        # Convert issues to violations
        rule_types_failed = set()
        for issue in issues:
            violation = self._create_violation(issue)
            if violation:
                violations.append(violation)
                rule_types_failed.add(issue.get("type"))

        # Update rules failed count based on unique rule types
        self._rules_failed = len(rule_types_failed)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    def _create_violation(self, issue: dict) -> Optional[Violation]:
        """Create violation from issue data."""
        issue_type = issue.get("type")

        violation_configs = {
            "positive-tabindex": {
                "id": "keyboard-positive-tabindex",
                "rule_id": "tabindex",
                "wcag": ["2.4.3"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Element has positive tabindex ({issue.get('tabindex')}), which disrupts natural tab order",
                "help": "Use tabindex='0' to add elements to natural tab order, or tabindex='-1' to make them programmatically focusable only"
            },
            "mouse-only": {
                "id": "keyboard-mouse-only",
                "rule_id": "keyboard-access",
                "wcag": ["2.1.1"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": "Element has mouse event handler but no keyboard equivalent",
                "help": "Add keyboard event handlers (onkeydown/onkeyup) or use native interactive elements"
            },
            "non-interactive-clickable": {
                "id": "keyboard-non-interactive",
                "rule_id": "interactive-element",
                "wcag": ["2.1.1", "4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Non-interactive element has click handler but lacks role and tabindex",
                "help": "Add role='button' and tabindex='0', or use a native <button> element"
            },
            "focus-not-visible": {
                "id": "keyboard-focus-not-visible",
                "rule_id": "focus-visible",
                "wcag": ["2.4.7"],
                "level": WCAGLevel.AA,
                "impact": Impact.SERIOUS,
                "description": "Element may have focus indicator removed (outline: none)",
                "help": "Ensure visible focus indicator via outline, box-shadow, or border"
            },
            "accesskey-used": {
                "id": "keyboard-accesskey",
                "rule_id": "accesskey",
                "wcag": ["2.1.4"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": f"Accesskey '{issue.get('accesskey')}' may conflict with assistive technology shortcuts",
                "help": "Consider removing accesskey or ensuring it doesn't conflict with AT"
            },
            "non-focusable-scroll": {
                "id": "keyboard-scroll-focus",
                "rule_id": "scrollable-region-focusable",
                "wcag": ["2.1.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Scrollable region is not keyboard accessible",
                "help": "Add tabindex='0' to make scrollable container focusable"
            },
            "autofocus-used": {
                "id": "keyboard-autofocus",
                "rule_id": "autofocus",
                "wcag": ["3.2.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MINOR,
                "description": "Autofocus attribute used, which may disorient users",
                "help": "Consider removing autofocus unless essential for the user experience"
            }
        }

        config = violation_configs.get(issue_type)
        if not config:
            return None

        return Violation(
            id=f"{config['id']}-{hash(issue.get('selector', '')) % 10000}",
            rule_id=config["rule_id"],
            wcag_criteria=config["wcag"],
            wcag_level=config["level"],
            impact=config["impact"],
            description=config["description"],
            help_text=config["help"],
            detected_by=["keyboard"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["keyboard", f"wcag{config['wcag'][0].replace('.', '')}"]
        )
