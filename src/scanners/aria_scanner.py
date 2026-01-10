"""ARIA validator scanner implementation."""

from typing import Optional
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Valid ARIA roles
VALID_ROLES = {
    "alert", "alertdialog", "application", "article", "banner", "blockquote",
    "button", "caption", "cell", "checkbox", "code", "columnheader", "combobox",
    "complementary", "contentinfo", "definition", "deletion", "dialog", "directory",
    "document", "emphasis", "feed", "figure", "form", "generic", "grid", "gridcell",
    "group", "heading", "img", "insertion", "link", "list", "listbox", "listitem",
    "log", "main", "marquee", "math", "menu", "menubar", "menuitem", "menuitemcheckbox",
    "menuitemradio", "meter", "navigation", "none", "note", "option", "paragraph",
    "presentation", "progressbar", "radio", "radiogroup", "region", "row", "rowgroup",
    "rowheader", "scrollbar", "search", "searchbox", "separator", "slider",
    "spinbutton", "status", "strong", "subscript", "superscript", "switch", "tab",
    "table", "tablist", "tabpanel", "term", "textbox", "time", "timer", "toolbar",
    "tooltip", "tree", "treegrid", "treeitem"
}

# Required ARIA attributes for certain roles
REQUIRED_ATTRIBUTES = {
    "checkbox": ["aria-checked"],
    "combobox": ["aria-expanded"],
    "heading": ["aria-level"],
    "meter": ["aria-valuenow"],
    "option": ["aria-selected"],
    "progressbar": ["aria-valuenow", "aria-valuemin", "aria-valuemax"],
    "radio": ["aria-checked"],
    "scrollbar": ["aria-controls", "aria-valuenow"],
    "slider": ["aria-valuenow", "aria-valuemin", "aria-valuemax"],
    "spinbutton": ["aria-valuenow"],
    "switch": ["aria-checked"],
}


class ARIAScanner(BaseScanner):
    """Scanner for ARIA accessibility issues."""

    name = "aria"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check ARIA usage.

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
                return await self._check_aria(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_aria(self, page: Page) -> list[Violation]:
        """Run ARIA checks."""
        violations = []

        # This scanner checks 9 rules
        self._rules_checked = 9

        issues = await page.evaluate("""
            () => {
                const issues = [];
                const validRoles = %s;
                const requiredAttrs = %s;

                // 1. Check for invalid roles
                const elementsWithRole = document.querySelectorAll('[role]');
                for (const el of elementsWithRole) {
                    const role = el.getAttribute('role').toLowerCase().trim();
                    if (!validRoles.includes(role)) {
                        issues.push({
                            type: 'invalid-role',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el),
                            role: role
                        });
                    }

                    // Check for required attributes
                    if (requiredAttrs[role]) {
                        for (const attr of requiredAttrs[role]) {
                            if (!el.hasAttribute(attr)) {
                                issues.push({
                                    type: 'missing-required-attr',
                                    element: el.outerHTML.substring(0, 200),
                                    selector: getSelector(el),
                                    role: role,
                                    missingAttr: attr
                                });
                            }
                        }
                    }
                }

                // 2. Check for invalid aria-* attributes
                const allElements = document.querySelectorAll('*');
                const validAriaAttrs = [
                    'aria-activedescendant', 'aria-atomic', 'aria-autocomplete', 'aria-busy',
                    'aria-checked', 'aria-colcount', 'aria-colindex', 'aria-colspan',
                    'aria-controls', 'aria-current', 'aria-describedby', 'aria-details',
                    'aria-disabled', 'aria-dropeffect', 'aria-errormessage', 'aria-expanded',
                    'aria-flowto', 'aria-grabbed', 'aria-haspopup', 'aria-hidden',
                    'aria-invalid', 'aria-keyshortcuts', 'aria-label', 'aria-labelledby',
                    'aria-level', 'aria-live', 'aria-modal', 'aria-multiline',
                    'aria-multiselectable', 'aria-orientation', 'aria-owns', 'aria-placeholder',
                    'aria-posinset', 'aria-pressed', 'aria-readonly', 'aria-relevant',
                    'aria-required', 'aria-roledescription', 'aria-rowcount', 'aria-rowindex',
                    'aria-rowspan', 'aria-selected', 'aria-setsize', 'aria-sort',
                    'aria-valuemax', 'aria-valuemin', 'aria-valuenow', 'aria-valuetext'
                ];

                for (const el of allElements) {
                    for (const attr of el.attributes) {
                        if (attr.name.startsWith('aria-') && !validAriaAttrs.includes(attr.name)) {
                            issues.push({
                                type: 'invalid-aria-attr',
                                element: el.outerHTML.substring(0, 200),
                                selector: getSelector(el),
                                attr: attr.name
                            });
                        }
                    }
                }

                // 3. Check for aria-hidden on focusable elements
                const ariaHiddenFocusable = document.querySelectorAll('[aria-hidden="true"] a, [aria-hidden="true"] button, [aria-hidden="true"] input, [aria-hidden="true"] [tabindex]:not([tabindex="-1"])');
                for (const el of ariaHiddenFocusable) {
                    issues.push({
                        type: 'aria-hidden-focusable',
                        element: el.outerHTML.substring(0, 200),
                        selector: getSelector(el)
                    });
                }

                // 4. Check for empty aria-label/aria-labelledby
                const labelledElements = document.querySelectorAll('[aria-label], [aria-labelledby]');
                for (const el of labelledElements) {
                    const ariaLabel = el.getAttribute('aria-label');
                    const ariaLabelledby = el.getAttribute('aria-labelledby');

                    if (ariaLabel !== null && ariaLabel.trim() === '') {
                        issues.push({
                            type: 'empty-aria-label',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el)
                        });
                    }

                    if (ariaLabelledby) {
                        const ids = ariaLabelledby.split(/\\s+/);
                        for (const id of ids) {
                            if (id && !document.getElementById(id)) {
                                issues.push({
                                    type: 'invalid-aria-labelledby',
                                    element: el.outerHTML.substring(0, 200),
                                    selector: getSelector(el),
                                    invalidId: id
                                });
                            }
                        }
                    }
                }

                // 5. Check for aria-describedby pointing to non-existent elements
                const describedElements = document.querySelectorAll('[aria-describedby]');
                for (const el of describedElements) {
                    const ids = el.getAttribute('aria-describedby').split(/\\s+/);
                    for (const id of ids) {
                        if (id && !document.getElementById(id)) {
                            issues.push({
                                type: 'invalid-aria-describedby',
                                element: el.outerHTML.substring(0, 200),
                                selector: getSelector(el),
                                invalidId: id
                            });
                        }
                    }
                }

                // 6. Check for redundant roles
                const redundantRoles = {
                    'A': 'link',
                    'ARTICLE': 'article',
                    'ASIDE': 'complementary',
                    'BUTTON': 'button',
                    'DATALIST': 'listbox',
                    'DETAILS': 'group',
                    'DIALOG': 'dialog',
                    'FIELDSET': 'group',
                    'FIGURE': 'figure',
                    'FOOTER': 'contentinfo',
                    'FORM': 'form',
                    'H1': 'heading',
                    'H2': 'heading',
                    'H3': 'heading',
                    'H4': 'heading',
                    'H5': 'heading',
                    'H6': 'heading',
                    'HEADER': 'banner',
                    'HR': 'separator',
                    'IMG': 'img',
                    'LI': 'listitem',
                    'MAIN': 'main',
                    'MENU': 'list',
                    'NAV': 'navigation',
                    'OL': 'list',
                    'OPTGROUP': 'group',
                    'OPTION': 'option',
                    'PROGRESS': 'progressbar',
                    'SELECT': 'listbox',
                    'SUMMARY': 'button',
                    'TABLE': 'table',
                    'TBODY': 'rowgroup',
                    'TD': 'cell',
                    'TEXTAREA': 'textbox',
                    'TFOOT': 'rowgroup',
                    'TH': 'columnheader',
                    'THEAD': 'rowgroup',
                    'TR': 'row',
                    'UL': 'list'
                };

                for (const el of elementsWithRole) {
                    const role = el.getAttribute('role').toLowerCase();
                    const implicitRole = redundantRoles[el.tagName];

                    if (implicitRole === role) {
                        issues.push({
                            type: 'redundant-role',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el),
                            role: role,
                            tag: el.tagName.toLowerCase()
                        });
                    }
                }

                // 7. Check for aria-live regions without proper content
                const liveRegions = document.querySelectorAll('[aria-live]');
                for (const el of liveRegions) {
                    const value = el.getAttribute('aria-live');
                    if (!['polite', 'assertive', 'off'].includes(value)) {
                        issues.push({
                            type: 'invalid-aria-live',
                            element: el.outerHTML.substring(0, 200),
                            selector: getSelector(el),
                            value: value
                        });
                    }
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
        """ % (list(VALID_ROLES), REQUIRED_ATTRIBUTES))

        # Convert to violations
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

        configs = {
            "invalid-role": {
                "id": "aria-invalid-role",
                "rule_id": "aria-roles",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": f"Invalid ARIA role: '{issue.get('role')}'",
                "help": "Use a valid ARIA role from the WAI-ARIA specification"
            },
            "missing-required-attr": {
                "id": "aria-required-attr",
                "rule_id": "aria-required-attr",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": f"Role '{issue.get('role')}' missing required attribute: {issue.get('missingAttr')}",
                "help": f"Add the required attribute {issue.get('missingAttr')} to the element"
            },
            "invalid-aria-attr": {
                "id": "aria-invalid-attr",
                "rule_id": "aria-valid-attr",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Invalid ARIA attribute: '{issue.get('attr')}'",
                "help": "Use a valid ARIA attribute from the WAI-ARIA specification"
            },
            "aria-hidden-focusable": {
                "id": "aria-hidden-focus",
                "rule_id": "aria-hidden-focus",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Focusable element inside aria-hidden container",
                "help": "Remove focusable elements from aria-hidden containers or add tabindex='-1'"
            },
            "empty-aria-label": {
                "id": "aria-empty-label",
                "rule_id": "aria-label-empty",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Element has empty aria-label",
                "help": "Provide meaningful text for aria-label or remove the attribute"
            },
            "invalid-aria-labelledby": {
                "id": "aria-invalid-labelledby",
                "rule_id": "aria-valid-attr-value",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"aria-labelledby references non-existent ID: '{issue.get('invalidId')}'",
                "help": "Ensure aria-labelledby references existing element IDs"
            },
            "invalid-aria-describedby": {
                "id": "aria-invalid-describedby",
                "rule_id": "aria-valid-attr-value",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": f"aria-describedby references non-existent ID: '{issue.get('invalidId')}'",
                "help": "Ensure aria-describedby references existing element IDs"
            },
            "redundant-role": {
                "id": "aria-redundant-role",
                "rule_id": "redundant-role",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.MINOR,
                "description": f"Redundant role '{issue.get('role')}' on <{issue.get('tag')}> element",
                "help": "Remove redundant role as the element already has this implicit role"
            },
            "invalid-aria-live": {
                "id": "aria-invalid-live",
                "rule_id": "aria-valid-attr-value",
                "wcag": ["4.1.3"],
                "level": WCAGLevel.AA,
                "impact": Impact.MODERATE,
                "description": f"Invalid aria-live value: '{issue.get('value')}'",
                "help": "Use 'polite', 'assertive', or 'off' for aria-live"
            }
        }

        config = configs.get(issue_type)
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
            detected_by=["aria"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["aria", f"wcag{config['wcag'][0].replace('.', '')}"]
        )
