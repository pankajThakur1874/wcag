"""Use of Color Scanner - WCAG 1.4.1 (Level A)

Detects elements that rely solely on color to convey information without
additional visual indicators (icons, text, patterns, etc.).
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import Page

from wcag_backend.scanners.base import BaseScanner
from wcag_backend.models_src import Violation, ViolationInstance, Impact, WCAGLevel
from wcag_backend.utils_src.browser import BrowserManager
from wcag_backend.utils.logger import get_logger

logger = get_logger(__name__)


class ColorOnlyScanner(BaseScanner):
    """Scanner for detecting color-only information conveying."""

    name = "color-only"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check for color-only information.

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
                return await self._check_color_only(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_color_only(self, page: Page) -> list[Violation]:
        """Run color-only checks."""
        violations = []

        # This scanner checks 8 different patterns
        self._rules_checked = 8

        issues = await page.evaluate("""
            () => {
                const issues = [];

                // Helper: Get computed color
                function getColor(el, property = 'color') {
                    return window.getComputedStyle(el)[property];
                }

                // Helper: Get element selector
                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        return el.tagName.toLowerCase() + '.' + classes[0];
                    }
                    return el.tagName.toLowerCase();
                }

                // Helper: Check if element has icon/symbol
                function hasVisualIndicator(el) {
                    // Check for common icon indicators
                    const hasIcon = el.querySelector('svg, i[class*="icon"], img[class*="icon"], span[class*="icon"]');
                    if (hasIcon) return true;

                    // Check for emoji or special characters
                    const text = el.textContent || '';
                    const hasSymbol = /[✓✗✕✖✔✘⚠⚡★☆●○■□▲▼◆◇]/.test(text);
                    if (hasSymbol) return true;

                    // Check for background patterns (using pseudo-elements)
                    const before = window.getComputedStyle(el, '::before');
                    const after = window.getComputedStyle(el, '::after');
                    if (before.content !== 'none' || after.content !== 'none') {
                        return true;
                    }

                    // Check for border indicators (dashed, dotted patterns)
                    const style = window.getComputedStyle(el);
                    if (style.borderStyle && style.borderStyle !== 'solid' && style.borderStyle !== 'none') {
                        return true;
                    }

                    return false;
                }

                // 1. Check form validation errors (red text without icons/symbols)
                const errorPatterns = [
                    '[class*="error"]',
                    '[class*="invalid"]',
                    '[class*="danger"]',
                    '[aria-invalid="true"]',
                    '.has-error',
                    '.is-invalid'
                ];

                for (const pattern of errorPatterns) {
                    const elements = document.querySelectorAll(pattern);
                    for (const el of elements) {
                        const color = getColor(el);
                        const bgColor = getColor(el, 'backgroundColor');

                        // Check if using red/orange colors
                        const isRedish = color.match(/rgb\\((2[0-4][0-9]|25[0-5]),\\s*([0-9]{1,2}|1[0-4][0-9]),\\s*([0-9]{1,2}|1[0-4][0-9])\\)/) ||
                                        bgColor.match(/rgb\\((2[0-4][0-9]|25[0-5]),\\s*([0-9]{1,2}|1[0-4][0-9]),\\s*([0-9]{1,2}|1[0-4][0-9])\\)/);

                        if (isRedish && !hasVisualIndicator(el)) {
                            issues.push({
                                type: 'error-color-only',
                                element: el.outerHTML.substring(0, 300),
                                selector: getSelector(el),
                                color: color,
                                backgroundColor: bgColor,
                                text: el.textContent.substring(0, 100)
                            });
                        }
                    }
                }

                // 2. Check success messages (green text without icons/symbols)
                const successPatterns = [
                    '[class*="success"]',
                    '[class*="valid"]',
                    '[class*="correct"]',
                    '.has-success',
                    '.is-valid'
                ];

                for (const pattern of successPatterns) {
                    const elements = document.querySelectorAll(pattern);
                    for (const el of elements) {
                        const color = getColor(el);
                        const bgColor = getColor(el, 'backgroundColor');

                        // Check if using green colors (high green channel)
                        const isGreenish = color.match(/rgb\\(([0-9]{1,2}|1[0-4][0-9]),\\s*(1[5-9][0-9]|2[0-5][0-9]),\\s*([0-9]{1,2}|1[0-4][0-9])\\)/) ||
                                          bgColor.match(/rgb\\(([0-9]{1,2}|1[0-4][0-9]),\\s*(1[5-9][0-9]|2[0-5][0-9]),\\s*([0-9]{1,2}|1[0-4][0-9])\\)/);

                        if (isGreenish && !hasVisualIndicator(el)) {
                            issues.push({
                                type: 'success-color-only',
                                element: el.outerHTML.substring(0, 300),
                                selector: getSelector(el),
                                color: color,
                                backgroundColor: bgColor,
                                text: el.textContent.substring(0, 100)
                            });
                        }
                    }
                }

                // 3. Check warning messages (yellow/orange without icons)
                const warningPatterns = [
                    '[class*="warning"]',
                    '[class*="alert"]',
                    '[class*="caution"]',
                    '.has-warning'
                ];

                for (const pattern of warningPatterns) {
                    const elements = document.querySelectorAll(pattern);
                    for (const el of elements) {
                        const color = getColor(el);
                        const bgColor = getColor(el, 'backgroundColor');

                        // Check for yellow/orange colors
                        const isYellowish = color.match(/rgb\\((2[0-5][0-9]),\\s*(1[5-9][0-9]|2[0-5][0-9]),\\s*([0-9]{1,2}|1[0-4][0-9])\\)/) ||
                                           bgColor.match(/rgb\\((2[0-5][0-9]),\\s*(1[5-9][0-9]|2[0-5][0-9]),\\s*([0-9]{1,2}|1[0-4][0-9])\\)/);

                        if (isYellowish && !hasVisualIndicator(el)) {
                            issues.push({
                                type: 'warning-color-only',
                                element: el.outerHTML.substring(0, 300),
                                selector: getSelector(el),
                                color: color,
                                backgroundColor: bgColor,
                                text: el.textContent.substring(0, 100)
                            });
                        }
                    }
                }

                // 4. Check required field indicators (* in red without aria-required)
                const inputs = document.querySelectorAll('input, select, textarea');
                for (const input of inputs) {
                    // Look for required indicator in label or nearby
                    const label = input.labels?.[0] ||
                                 document.querySelector(`label[for="${input.id}"]`) ||
                                 input.closest('label');

                    if (label) {
                        const labelText = label.textContent;
                        const hasAsterisk = labelText.includes('*');
                        const hasRequired = input.hasAttribute('required') ||
                                          input.hasAttribute('aria-required');

                        if (hasAsterisk && !hasRequired) {
                            // Check if asterisk is styled with color
                            const spans = label.querySelectorAll('span, abbr');
                            for (const span of spans) {
                                if (span.textContent.includes('*')) {
                                    const color = getColor(span);
                                    const isRed = color.match(/rgb\\((2[0-4][0-9]|25[0-5]),\\s*([0-9]{1,2}|1[0-4][0-9]),\\s*([0-9]{1,2}|1[0-4][0-9])\\)/);

                                    if (isRed) {
                                        issues.push({
                                            type: 'required-color-only',
                                            element: label.outerHTML.substring(0, 300),
                                            selector: getSelector(label),
                                            color: color,
                                            text: labelText.substring(0, 100)
                                        });
                                    }
                                }
                            }
                        }
                    }
                }

                // 5. Check links that differ only in color
                const links = document.querySelectorAll('a');
                const linksByParent = new Map();

                for (const link of links) {
                    const parent = link.parentElement;
                    if (!parent) continue;

                    if (!linksByParent.has(parent)) {
                        linksByParent.set(parent, []);
                    }
                    linksByParent.get(parent).push(link);
                }

                for (const [parent, linksInParent] of linksByParent) {
                    if (linksInParent.length < 2) continue;

                    const parentColor = getColor(parent);

                    for (const link of linksInParent) {
                        const linkColor = getColor(link);
                        const style = window.getComputedStyle(link);

                        // Check if link differs from parent only in color
                        const hasUnderline = style.textDecoration.includes('underline');
                        const hasBorder = style.borderBottom !== 'none' && style.borderBottom !== '0px';
                        const hasBold = parseInt(style.fontWeight) >= 700;

                        if (linkColor !== parentColor && !hasUnderline && !hasBorder && !hasBold) {
                            issues.push({
                                type: 'link-color-only',
                                element: link.outerHTML.substring(0, 300),
                                selector: getSelector(link),
                                color: linkColor,
                                parentColor: parentColor,
                                text: link.textContent.substring(0, 100)
                            });
                        }
                    }
                }

                // 6. Check charts/graphs without patterns or labels
                const chartElements = document.querySelectorAll(
                    '[class*="chart"], [class*="graph"], canvas, svg[class*="chart"], svg[class*="graph"]'
                );

                for (const chart of chartElements) {
                    // Check if SVG/canvas has accessible description
                    const hasTitle = chart.querySelector('title');
                    const hasDesc = chart.querySelector('desc');
                    const hasAriaLabel = chart.hasAttribute('aria-label') ||
                                        chart.hasAttribute('aria-labelledby');
                    const hasAlt = chart.hasAttribute('alt');
                    const hasRole = chart.hasAttribute('role');

                    if (!hasTitle && !hasDesc && !hasAriaLabel && !hasAlt) {
                        issues.push({
                            type: 'chart-color-only',
                            element: chart.outerHTML.substring(0, 300),
                            selector: getSelector(chart),
                            tagName: chart.tagName
                        });
                    }
                }

                // 7. Check disabled state indicated by color only
                const potentialDisabled = document.querySelectorAll(
                    '[class*="disabled"]:not([disabled]):not([aria-disabled])'
                );

                for (const el of potentialDisabled) {
                    if (!el.hasAttribute('disabled') && !el.hasAttribute('aria-disabled')) {
                        issues.push({
                            type: 'disabled-color-only',
                            element: el.outerHTML.substring(0, 300),
                            selector: getSelector(el),
                            text: el.textContent.substring(0, 100)
                        });
                    }
                }

                // 8. Check status indicators (active, current, selected)
                const statusPatterns = [
                    '[class*="active"]:not([aria-current]):not([aria-selected="true"])',
                    '[class*="current"]:not([aria-current])',
                    '[class*="selected"]:not([aria-selected="true"])'
                ];

                for (const pattern of statusPatterns) {
                    const elements = document.querySelectorAll(pattern);
                    for (const el of elements) {
                        if (!hasVisualIndicator(el)) {
                            issues.push({
                                type: 'status-color-only',
                                element: el.outerHTML.substring(0, 300),
                                selector: getSelector(el),
                                text: el.textContent.substring(0, 100),
                                color: getColor(el),
                                backgroundColor: getColor(el, 'backgroundColor')
                            });
                        }
                    }
                }

                return issues;
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
            "error-color-only": {
                "id": "color-error-indicator",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Error message relies solely on red color without additional visual indicator",
                "help": "Add an icon (✗, ⚠), symbol, or text label (e.g., 'Error:') alongside the color"
            },
            "success-color-only": {
                "id": "color-success-indicator",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Success message relies solely on green color without additional visual indicator",
                "help": "Add an icon (✓) or text label (e.g., 'Success:') alongside the color"
            },
            "warning-color-only": {
                "id": "color-warning-indicator",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Warning message relies solely on yellow/orange color without additional visual indicator",
                "help": "Add an icon (⚠) or text label (e.g., 'Warning:') alongside the color"
            },
            "required-color-only": {
                "id": "color-required-indicator",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1", "3.3.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Required field indicated by red asterisk (*) without required attribute or aria-required",
                "help": "Add required or aria-required='true' attribute, or include '(required)' text in label"
            },
            "link-color-only": {
                "id": "color-link-indicator",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Link differs from surrounding text only by color",
                "help": "Add underline, bold weight, or another visual indicator besides color"
            },
            "chart-color-only": {
                "id": "color-chart-data",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": "Chart/graph may rely on color to convey data without text alternatives",
                "help": "Add <title>, <desc>, aria-label, or data table alternative for charts"
            },
            "disabled-color-only": {
                "id": "color-disabled-state",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Disabled state indicated by class name but missing disabled or aria-disabled attribute",
                "help": "Add disabled or aria-disabled='true' attribute to indicate state programmatically"
            },
            "status-color-only": {
                "id": "color-status-indicator",
                "rule_id": "use-of-color",
                "wcag": ["1.4.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Active/current/selected state may rely on color without ARIA attributes",
                "help": "Add aria-current='page'/aria-current='true' or aria-selected='true' attribute"
            }
        }

        config = violation_configs.get(issue_type)
        if not config:
            return None

        # Build detailed help text
        help_text = config["help"]
        if issue.get("color"):
            help_text += f" (Current color: {issue.get('color')})"

        return Violation(
            id=f"{config['id']}-{hash(issue.get('selector', '')) % 10000}",
            rule_id=config["rule_id"],
            wcag_criteria=config["wcag"],
            wcag_level=config["level"],
            impact=config["impact"],
            description=config["description"],
            help_text=help_text,
            help_url="https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html",
            detected_by=["color-only"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["color", "wcag141", "level-a"]
        )
