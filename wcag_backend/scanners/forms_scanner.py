"""Forms accessibility scanner implementation."""

from typing import Optional
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FormsScanner(BaseScanner):
    """Scanner for form accessibility issues."""

    name = "forms"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check form accessibility.

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
                return await self._check_forms(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_forms(self, page: Page) -> list[Violation]:
        """Run form accessibility checks."""
        violations = []

        # This scanner checks 9 rules
        self._rules_checked = 9

        issues = await page.evaluate("""
            () => {
                const issues = [];

                // Get all forms
                const forms = document.querySelectorAll('form');

                for (const form of forms) {
                    // 1. Check for missing form labels/legends
                    const fieldsets = form.querySelectorAll('fieldset');
                    for (const fieldset of fieldsets) {
                        const legend = fieldset.querySelector('legend');
                        if (!legend || !legend.textContent.trim()) {
                            issues.push({
                                type: 'fieldset-no-legend',
                                element: fieldset.outerHTML.substring(0, 200),
                                selector: getSelector(fieldset)
                            });
                        }
                    }

                    // 2. Check for inputs without labels
                    const inputs = form.querySelectorAll('input, select, textarea');
                    for (const input of inputs) {
                        const type = input.type || 'text';
                        if (['hidden', 'submit', 'reset', 'button', 'image'].includes(type)) continue;

                        const id = input.id;
                        let hasLabel = false;

                        // Check for associated label
                        if (id) {
                            const label = document.querySelector(`label[for="${id}"]`);
                            if (label && label.textContent.trim()) hasLabel = true;
                        }

                        // Check for wrapping label
                        if (!hasLabel) {
                            let parent = input.parentElement;
                            while (parent && parent !== form) {
                                if (parent.tagName === 'LABEL' && parent.textContent.trim()) {
                                    hasLabel = true;
                                    break;
                                }
                                parent = parent.parentElement;
                            }
                        }

                        // Check for aria-label/aria-labelledby
                        if (input.getAttribute('aria-label') || input.getAttribute('aria-labelledby')) {
                            hasLabel = true;
                        }

                        // Check for title attribute
                        if (input.title) {
                            hasLabel = true;
                        }

                        // Check for placeholder (not sufficient alone but noting it)
                        const hasOnlyPlaceholder = !hasLabel && input.placeholder;

                        if (!hasLabel) {
                            issues.push({
                                type: 'input-no-label',
                                element: input.outerHTML.substring(0, 200),
                                selector: getSelector(input),
                                inputType: type,
                                hasPlaceholder: !!input.placeholder
                            });
                        } else if (hasOnlyPlaceholder) {
                            issues.push({
                                type: 'placeholder-only-label',
                                element: input.outerHTML.substring(0, 200),
                                selector: getSelector(input)
                            });
                        }
                    }

                    // 3. Check for missing autocomplete
                    const autocompletableInputs = form.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], input[type="password"], input[type="url"], input:not([type])');
                    for (const input of autocompletableInputs) {
                        const name = (input.name || '').toLowerCase();
                        const id = (input.id || '').toLowerCase();

                        // Common field patterns that should have autocomplete
                        const patterns = {
                            'name': 'name',
                            'email': 'email',
                            'phone': 'tel',
                            'tel': 'tel',
                            'address': 'street-address',
                            'city': 'address-level2',
                            'state': 'address-level1',
                            'zip': 'postal-code',
                            'postal': 'postal-code',
                            'country': 'country',
                            'password': 'current-password',
                            'username': 'username',
                            'firstname': 'given-name',
                            'lastname': 'family-name',
                            'cc': 'cc-number'
                        };

                        for (const [pattern, autocomplete] of Object.entries(patterns)) {
                            if ((name.includes(pattern) || id.includes(pattern)) && !input.autocomplete) {
                                issues.push({
                                    type: 'missing-autocomplete',
                                    element: input.outerHTML.substring(0, 200),
                                    selector: getSelector(input),
                                    suggestedAutocomplete: autocomplete
                                });
                                break;
                            }
                        }
                    }

                    // 4. Check for required fields without indication
                    const requiredInputs = form.querySelectorAll('[required], [aria-required="true"]');
                    for (const input of requiredInputs) {
                        const id = input.id;
                        let labelText = '';

                        if (id) {
                            const label = document.querySelector(`label[for="${id}"]`);
                            if (label) labelText = label.textContent;
                        }

                        // Check if required is indicated in label
                        const hasRequiredIndicator = labelText.includes('*') ||
                                                    labelText.toLowerCase().includes('required') ||
                                                    input.getAttribute('aria-required') === 'true';

                        if (!hasRequiredIndicator) {
                            issues.push({
                                type: 'required-no-indicator',
                                element: input.outerHTML.substring(0, 200),
                                selector: getSelector(input)
                            });
                        }
                    }

                    // 5. Check for error handling
                    const hasAriaInvalid = form.querySelector('[aria-invalid]');
                    const hasAriaErrormessage = form.querySelector('[aria-errormessage]');
                    const hasAriaDescribedby = form.querySelector('[aria-describedby]');

                    // 6. Check submit buttons
                    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"], button:not([type])');
                    if (submitButtons.length === 0) {
                        issues.push({
                            type: 'form-no-submit',
                            element: form.outerHTML.substring(0, 200),
                            selector: getSelector(form)
                        });
                    }

                    for (const btn of submitButtons) {
                        const text = btn.textContent || btn.value || '';
                        if (!text.trim()) {
                            issues.push({
                                type: 'submit-no-text',
                                element: btn.outerHTML.substring(0, 200),
                                selector: getSelector(btn)
                            });
                        }
                    }
                }

                // 7. Check for inputs outside forms
                const orphanInputs = document.querySelectorAll('input:not(form input), select:not(form select), textarea:not(form textarea)');
                for (const input of orphanInputs) {
                    const type = input.type || 'text';
                    if (['hidden', 'search'].includes(type)) continue;

                    // Check if it's part of a custom form component
                    const hasRole = input.closest('[role="form"]');
                    if (!hasRole && !input.closest('form')) {
                        issues.push({
                            type: 'input-outside-form',
                            element: input.outerHTML.substring(0, 200),
                            selector: getSelector(input)
                        });
                    }
                }

                // 8. Check for duplicate IDs on form elements
                const formElementsWithId = document.querySelectorAll('input[id], select[id], textarea[id], button[id]');
                const idCounts = {};
                for (const el of formElementsWithId) {
                    const id = el.id;
                    idCounts[id] = (idCounts[id] || 0) + 1;
                }

                for (const [id, count] of Object.entries(idCounts)) {
                    if (count > 1) {
                        issues.push({
                            type: 'duplicate-form-id',
                            element: `Multiple elements with id="${id}"`,
                            selector: `#${id}`,
                            id: id,
                            count: count
                        });
                    }
                }

                return issues;

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.name) return `${el.tagName.toLowerCase()}[name="${el.name}"]`;
                    if (el.className && typeof el.className === 'string') {
                        return el.tagName.toLowerCase() + '.' + el.className.split(' ')[0];
                    }
                    return el.tagName.toLowerCase();
                }
            }
        """)

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
            "fieldset-no-legend": {
                "id": "forms-fieldset-legend",
                "rule_id": "fieldset-legend",
                "wcag": ["1.3.1", "3.3.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Fieldset missing legend element",
                "help": "Add a <legend> element to describe the group of related fields"
            },
            "input-no-label": {
                "id": "forms-input-label",
                "rule_id": "input-label",
                "wcag": ["1.3.1", "3.3.2", "4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": f"Form input ({issue.get('inputType', 'text')}) has no accessible label",
                "help": "Add a <label> with for attribute, wrap input in <label>, or use aria-label"
            },
            "placeholder-only-label": {
                "id": "forms-placeholder-label",
                "rule_id": "placeholder-label",
                "wcag": ["1.3.1", "3.3.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Input uses placeholder as only label",
                "help": "Placeholders disappear when typing; add a persistent visible label"
            },
            "missing-autocomplete": {
                "id": "forms-autocomplete",
                "rule_id": "input-autocomplete",
                "wcag": ["1.3.5"],
                "level": WCAGLevel.AA,
                "impact": Impact.MODERATE,
                "description": f"Input should have autocomplete attribute (suggested: {issue.get('suggestedAutocomplete')})",
                "help": f"Add autocomplete='{issue.get('suggestedAutocomplete')}' for better user experience"
            },
            "required-no-indicator": {
                "id": "forms-required-indicator",
                "rule_id": "required-indicator",
                "wcag": ["3.3.2"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Required field lacks visible indicator (e.g., * or 'required')",
                "help": "Add visible indicator in label that field is required"
            },
            "form-no-submit": {
                "id": "forms-no-submit",
                "rule_id": "form-submit",
                "wcag": ["3.2.2"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Form has no submit button",
                "help": "Add a submit button or input[type='submit']"
            },
            "submit-no-text": {
                "id": "forms-submit-text",
                "rule_id": "button-name",
                "wcag": ["4.1.2"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Submit button has no accessible name",
                "help": "Add text content or value attribute to submit button"
            },
            "input-outside-form": {
                "id": "forms-orphan-input",
                "rule_id": "input-in-form",
                "wcag": ["1.3.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MINOR,
                "description": "Form input found outside of <form> element",
                "help": "Wrap form controls in <form> element or add role='form'"
            },
            "duplicate-form-id": {
                "id": "forms-duplicate-id",
                "rule_id": "duplicate-id",
                "wcag": ["4.1.1"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Duplicate ID '{issue.get('id')}' found on {issue.get('count')} form elements",
                "help": "Ensure all IDs are unique within the document"
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
            detected_by=["forms"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["forms", f"wcag{config['wcag'][0].replace('.', '')}"]
        )
