"""Content on Hover or Focus Scanner - WCAG 1.4.13 (Level AA)

Detects additional content triggered by hover or focus and checks if it meets
the three requirements: dismissible, hoverable, and persistent.
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import Page

from wcag_backend.scanners.base import BaseScanner
from wcag_backend.models_src import Violation, ViolationInstance, Impact, WCAGLevel
from wcag_backend.utils_src.browser import BrowserManager
from wcag_backend.utils.logger import get_logger

logger = get_logger(__name__)


class HoverContentScanner(BaseScanner):
    """Scanner for hover/focus triggered content accessibility."""

    name = "hover-content"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check hover/focus content accessibility.

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
                return await self._check_hover_content(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_hover_content(self, page: Page) -> list[Violation]:
        """Run hover content checks."""
        violations = []

        # This scanner checks 3 rules (dismissible, hoverable, persistent)
        self._rules_checked = 3

        # First, find all elements that might trigger hover content
        trigger_elements = await page.evaluate("""
            () => {
                const triggers = [];

                // Find elements with title attribute (native tooltips)
                const withTitle = document.querySelectorAll('[title]');
                for (const el of withTitle) {
                    if (el.title.trim()) {
                        triggers.push({
                            selector: el.id ? '#' + el.id : el.className ?
                                el.tagName.toLowerCase() + '.' + el.className.split(' ')[0] :
                                el.tagName.toLowerCase(),
                            type: 'title',
                            hasTitle: true,
                            element: el.outerHTML.substring(0, 200)
                        });
                    }
                }

                // Find elements with CSS hover states
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    // Check for tooltip/popover class patterns
                    const className = el.className || '';
                    const isTooltip = /tooltip|popover|dropdown|menu|submenu/i.test(className);

                    if (isTooltip) {
                        triggers.push({
                            selector: el.id ? '#' + el.id : className ?
                                el.tagName.toLowerCase() + '.' + className.split(' ')[0] :
                                el.tagName.toLowerCase(),
                            type: 'css-class',
                            className: className,
                            element: el.outerHTML.substring(0, 200)
                        });
                    }

                    // Check for aria-describedby (often used for tooltips)
                    if (el.hasAttribute('aria-describedby')) {
                        const describedById = el.getAttribute('aria-describedby');
                        const describedBy = document.getElementById(describedById);

                        if (describedBy) {
                            triggers.push({
                                selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                                type: 'aria-describedby',
                                describedById: describedById,
                                element: el.outerHTML.substring(0, 200)
                            });
                        }
                    }
                }

                // Find elements with :hover pseudo-class in CSS
                const sheets = Array.from(document.styleSheets);
                const hoverSelectors = new Set();

                for (const sheet of sheets) {
                    try {
                        const rules = sheet.cssRules || sheet.rules;
                        for (const rule of rules) {
                            if (rule.selectorText && rule.selectorText.includes(':hover')) {
                                hoverSelectors.add(rule.selectorText.split(':hover')[0]);
                            }
                        }
                    } catch (e) {
                        // Skip cross-origin stylesheets
                    }
                }

                // Add elements that have hover styles
                for (const selector of hoverSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            triggers.push({
                                selector: selector,
                                type: 'hover-css',
                                element: el.outerHTML.substring(0, 200)
                            });
                        }
                    } catch (e) {
                        // Invalid selector
                    }
                }

                return triggers;
            }
        """)

        logger.info(f"Found {len(trigger_elements)} potential hover/focus triggers")

        # Test each trigger element
        issues = []
        tested_selectors = set()

        for trigger in trigger_elements[:20]:  # Limit to first 20 to avoid timeout
            selector = trigger.get("selector")

            # Skip if already tested
            if selector in tested_selectors:
                continue
            tested_selectors.add(selector)

            try:
                # Test the element
                issue = await self._test_hover_element(page, selector, trigger)
                if issue:
                    issues.append(issue)
            except Exception as e:
                logger.debug(f"Error testing {selector}: {e}")
                continue

        # Convert issues to violations
        rule_types_failed = set()
        for issue in issues:
            violation = self._create_violation(issue)
            if violation:
                violations.append(violation)
                rule_types_failed.add(issue.get("violation_type"))

        # Update rules failed count
        self._rules_failed = len(rule_types_failed)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    async def _test_hover_element(
        self,
        page: Page,
        selector: str,
        trigger_info: Dict
    ) -> Optional[Dict[str, Any]]:
        """Test a specific element for hover content issues."""

        result = await page.evaluate("""
            async ({ selector, triggerInfo }) => {
                const element = document.querySelector(selector);
                if (!element) return null;

                const issues = {
                    selector: selector,
                    type: triggerInfo.type,
                    element: element.outerHTML.substring(0, 300),
                    violations: []
                };

                // Get initial DOM state
                const initialHTML = document.body.innerHTML;

                // Test 1: Native title tooltips (always fail dismissible/hoverable)
                if (triggerInfo.hasTitle) {
                    issues.violations.push({
                        type: 'title-not-dismissible',
                        reason: 'Native title tooltips cannot be dismissed without moving pointer',
                        title: element.title
                    });
                    issues.violations.push({
                        type: 'title-not-hoverable',
                        reason: 'Native title tooltips disappear when pointer moves to content'
                    });
                    return issues;
                }

                // For other types, simulate hover
                try {
                    element.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                    element.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));

                    // Wait a bit for content to appear
                    await new Promise(resolve => setTimeout(resolve, 100));

                    // Check if new content appeared
                    const afterHoverHTML = document.body.innerHTML;
                    const contentAppeared = initialHTML !== afterHoverHTML;

                    if (contentAppeared) {
                        // Find the new content
                        const tooltips = document.querySelectorAll(
                            '[role="tooltip"], .tooltip, .popover, [class*="tooltip"], [class*="popover"]'
                        );

                        for (const tooltip of tooltips) {
                            const style = window.getComputedStyle(tooltip);

                            // Check if visible
                            if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                                // Test 2: Check if dismissible with Escape
                                const hasEscapeHandler = tooltip.hasAttribute('data-dismiss') ||
                                                        tooltip.hasAttribute('data-bs-dismiss') ||
                                                        element.hasAttribute('data-dismiss');

                                if (!hasEscapeHandler) {
                                    // Check if there's a close button
                                    const closeBtn = tooltip.querySelector('[aria-label*="close"], [class*="close"], button[aria-label*="dismiss"]');

                                    if (!closeBtn) {
                                        issues.violations.push({
                                            type: 'not-dismissible',
                                            reason: 'No Escape key handler or close button detected',
                                            tooltipHTML: tooltip.outerHTML.substring(0, 200)
                                        });
                                    }
                                }

                                // Test 3: Check if hoverable (tooltip itself needs to accept hover)
                                const tooltipRect = tooltip.getBoundingClientRect();
                                const isPositioned = tooltipRect.width > 0 && tooltipRect.height > 0;

                                if (isPositioned) {
                                    // Check if tooltip has pointer-events: none
                                    if (style.pointerEvents === 'none') {
                                        issues.violations.push({
                                            type: 'not-hoverable',
                                            reason: 'Tooltip has pointer-events: none, cannot be hovered',
                                            tooltipHTML: tooltip.outerHTML.substring(0, 200)
                                        });
                                    }
                                }

                                // Test 4: Check persistence (doesn't disappear on blur without intent)
                                // This is hard to test automatically, so we check for common anti-patterns
                                const hasAutoHide = tooltip.hasAttribute('data-autohide') ||
                                                   tooltip.hasAttribute('data-auto-close');

                                if (hasAutoHide) {
                                    issues.violations.push({
                                        type: 'auto-dismiss',
                                        reason: 'Tooltip has auto-hide/auto-close that may dismiss without user control',
                                        tooltipHTML: tooltip.outerHTML.substring(0, 200)
                                    });
                                }
                            }
                        }
                    }
                } catch (e) {
                    // Error during testing
                }

                // Clean up - try to hide tooltip
                element.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));
                element.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));

                return issues.violations.length > 0 ? issues : null;
            }
        """, {"selector": selector, "triggerInfo": trigger_info})

        return result

    def _create_violation(self, issue: dict) -> Optional[Violation]:
        """Create violation from issue data."""
        violations_list = issue.get("violations", [])
        if not violations_list:
            return None

        # Take the first violation type for this element
        violation_data = violations_list[0]
        violation_type = violation_data.get("type")

        violation_configs = {
            "title-not-dismissible": {
                "id": "hover-title-not-dismissible",
                "rule_id": "content-on-hover-or-focus",
                "wcag": ["1.4.13"],
                "level": WCAGLevel.AA,
                "impact": Impact.SERIOUS,
                "description": "Native title attribute tooltip cannot be dismissed without moving pointer",
                "help": "Replace title attribute with custom tooltip using role='tooltip' with Escape key handler"
            },
            "title-not-hoverable": {
                "id": "hover-title-not-hoverable",
                "rule_id": "content-on-hover-or-focus",
                "wcag": ["1.4.13"],
                "level": WCAGLevel.AA,
                "impact": Impact.SERIOUS,
                "description": "Native title attribute tooltip is not hoverable (disappears when pointer moves to content)",
                "help": "Replace title attribute with custom tooltip that allows hovering over the tooltip content"
            },
            "not-dismissible": {
                "id": "hover-not-dismissible",
                "rule_id": "content-on-hover-or-focus",
                "wcag": ["1.4.13"],
                "level": WCAGLevel.AA,
                "impact": Impact.MODERATE,
                "description": "Hover/focus triggered content cannot be dismissed with Escape key",
                "help": "Add Escape key handler to dismiss tooltip, or provide visible close button with aria-label"
            },
            "not-hoverable": {
                "id": "hover-not-hoverable",
                "rule_id": "content-on-hover-or-focus",
                "wcag": ["1.4.13"],
                "level": WCAGLevel.AA,
                "impact": Impact.MODERATE,
                "description": "Hover triggered content has pointer-events: none, preventing users from hovering over it",
                "help": "Remove pointer-events: none or set to auto to allow hovering the tooltip content"
            },
            "auto-dismiss": {
                "id": "hover-auto-dismiss",
                "rule_id": "content-on-hover-or-focus",
                "wcag": ["1.4.13"],
                "level": WCAGLevel.AA,
                "impact": Impact.MODERATE,
                "description": "Hover content has auto-dismiss behavior that may remove it without user intent",
                "help": "Remove auto-dismiss. Content should persist until user dismisses or moves focus away"
            }
        }

        config = violation_configs.get(violation_type)
        if not config:
            return None

        # Build detailed help text
        help_text = config["help"]
        if violation_data.get("reason"):
            help_text = f"{violation_data.get('reason')}. {help_text}"

        return Violation(
            id=f"{config['id']}-{hash(issue.get('selector', '')) % 10000}",
            rule_id=config["rule_id"],
            wcag_criteria=config["wcag"],
            wcag_level=config["level"],
            impact=config["impact"],
            description=config["description"],
            help_text=help_text,
            help_url="https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html",
            detected_by=["hover-content"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["hover", "focus", "wcag1413", "level-aa"]
        )
