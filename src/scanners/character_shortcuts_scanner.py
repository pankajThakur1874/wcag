"""Character Key Shortcuts Scanner - WCAG 2.1.4 (Level A)

Detects single character key shortcuts that can interfere with assistive
technology and checks if they can be turned off, remapped, or are only active
when component has focus.
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import Page
import re

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CharacterShortcutsScanner(BaseScanner):
    """Scanner for single character keyboard shortcuts."""

    name = "character-shortcuts"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check for problematic character key shortcuts.

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
                return await self._check_character_shortcuts(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_character_shortcuts(self, page: Page) -> list[Violation]:
        """Run character shortcut checks."""
        violations = []

        # This scanner checks 3 compliance mechanisms
        self._rules_checked = 3

        issues = await page.evaluate("""
            () => {
                const issues = [];
                const shortcutsFound = [];

                // Helper function
                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        return el.tagName.toLowerCase() + '.' + classes[0];
                    }
                    return el.tagName.toLowerCase();
                }

                // 1. Check inline keyboard event handlers
                const elementsWithKeyHandlers = document.querySelectorAll('[onkeydown], [onkeyup], [onkeypress]');

                for (const el of elementsWithKeyHandlers) {
                    const keydown = el.getAttribute('onkeydown') || '';
                    const keyup = el.getAttribute('onkeyup') || '';
                    const keypress = el.getAttribute('onkeypress') || '';

                    const code = keydown + keyup + keypress;

                    // Look for single character key checks (e.g., event.key === 'a')
                    // Match patterns like: key === 'x', keyCode === 65, which === 65
                    const singleCharPattern = /(?:key|keyCode|which)\s*===?\s*['"]?([a-zA-Z0-9])['"]?(?!\s*\+)/g;
                    let match;

                    while ((match = singleCharPattern.exec(code)) !== null) {
                        const char = match[1];

                        // Check if it's a modifier key combination
                        const hasModifier = /ctrlKey|altKey|metaKey|shiftKey/.test(code);

                        if (!hasModifier) {
                            shortcutsFound.push({
                                element: el,
                                selector: getSelector(el),
                                character: char,
                                code: code.substring(0, 200),
                                isGlobal: el === document.body || el === document.documentElement
                            });
                        }
                    }
                }

                // 2. Check for accesskey attributes (single character shortcuts)
                const accesskeyElements = document.querySelectorAll('[accesskey]');

                for (const el of accesskeyElements) {
                    const accesskey = el.getAttribute('accesskey');

                    if (accesskey && accesskey.length === 1) {
                        shortcutsFound.push({
                            element: el,
                            selector: getSelector(el),
                            character: accesskey,
                            type: 'accesskey',
                            isGlobal: true  // accesskey is always global
                        });
                    }
                }

                // 3. Look for keyboard shortcut documentation/hints
                const shortcutHints = document.querySelectorAll(
                    '[class*="shortcut"], [class*="hotkey"], [aria-label*="press"], ' +
                    '[title*="press"], kbd'
                );

                for (const hint of shortcutHints) {
                    const text = hint.textContent || hint.getAttribute('aria-label') || hint.getAttribute('title') || '';

                    // Look for single character shortcuts mentioned in text
                    // Patterns like: "Press S to search", "Type / to search", etc.
                    const singleKeyPattern = /(?:press|type|hit)\\s+(['"]?)([a-zA-Z0-9\\/])\\1/gi;
                    let match;

                    while ((match = singleKeyPattern.exec(text)) !== null) {
                        const char = match[2];

                        // Check if modifier is mentioned
                        const hasModifier = /ctrl|alt|cmd|shift|meta/i.test(text);

                        if (!hasModifier) {
                            shortcutsFound.push({
                                element: hint,
                                selector: getSelector(hint),
                                character: char,
                                type: 'documented',
                                text: text.substring(0, 100),
                                isGlobal: true  // Assume documented shortcuts are global
                            });
                        }
                    }
                }

                // Analyze shortcuts found
                for (const shortcut of shortcutsFound) {
                    const element = shortcut.element;

                    // Check compliance mechanisms:
                    // 1. Can it be turned off?
                    // 2. Can it be remapped?
                    // 3. Is it only active when component has focus?

                    // Mechanism 3: Check if shortcut is scoped to component
                    const isScoped = !shortcut.isGlobal && element !== document.body;

                    // Mechanism 1 & 2: Check for settings/preferences
                    const hasSettings = document.querySelector(
                        '[href*="settings"], [href*="preferences"], ' +
                        '[class*="settings"], [aria-label*="settings"]'
                    ) !== null;

                    // Check for keyboard shortcut customization hints
                    const hasCustomizationHints = document.body.textContent.toLowerCase().includes('keyboard shortcut') &&
                                                  (document.body.textContent.toLowerCase().includes('customize') ||
                                                   document.body.textContent.toLowerCase().includes('remap'));

                    // If none of the mechanisms are evident, it's a violation
                    if (!isScoped && !hasSettings && !hasCustomizationHints) {
                        issues.push({
                            type: 'single-char-shortcut-no-mechanism',
                            element: element.outerHTML.substring(0, 300),
                            selector: shortcut.selector,
                            character: shortcut.character,
                            shortcutType: shortcut.type || 'event-handler',
                            isGlobal: shortcut.isGlobal
                        });
                    } else if (shortcut.isGlobal && !hasSettings && !hasCustomizationHints) {
                        // Global shortcut without apparent turn-off/remap mechanism
                        issues.push({
                            type: 'global-char-shortcut-no-control',
                            element: element.outerHTML.substring(0, 300),
                            selector: shortcut.selector,
                            character: shortcut.character,
                            shortcutType: shortcut.type || 'event-handler'
                        });
                    }
                }

                // Check for common problematic shortcuts
                const problematicKeys = ['s', 'f', 'g', 'h', 'j', 'k', 'l', '/'];
                const foundProblematic = shortcutsFound.filter(s =>
                    problematicKeys.includes(s.character.toLowerCase())
                );

                if (foundProblematic.length > 0) {
                    for (const shortcut of foundProblematic) {
                        issues.push({
                            type: 'common-conflict-shortcut',
                            element: shortcut.element.outerHTML.substring(0, 300),
                            selector: shortcut.selector,
                            character: shortcut.character,
                            reason: 'This key commonly conflicts with screen reader shortcuts'
                        });
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

        # Update rules failed count
        self._rules_failed = len(rule_types_failed)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    def _create_violation(self, issue: dict) -> Optional[Violation]:
        """Create violation from issue data."""
        issue_type = issue.get("type")
        char = issue.get("character", "?")

        violation_configs = {
            "single-char-shortcut-no-mechanism": {
                "id": "char-shortcut-no-mechanism",
                "rule_id": "character-key-shortcuts",
                "wcag": ["2.1.4"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Single character shortcut '{char}' lacks turn-off, remap, or focus-scoping mechanism",
                "help": "Provide one of: (1) mechanism to turn off shortcut, (2) mechanism to remap to different keys, or (3) only activate when component has focus"
            },
            "global-char-shortcut-no-control": {
                "id": "char-shortcut-global",
                "rule_id": "character-key-shortcuts",
                "wcag": ["2.1.4"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Global single character shortcut '{char}' without user control mechanism",
                "help": "Add settings page to disable/remap shortcuts, or scope shortcut to activate only when specific component has focus"
            },
            "common-conflict-shortcut": {
                "id": "char-shortcut-conflict",
                "rule_id": "character-key-shortcuts",
                "wcag": ["2.1.4"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": f"Character '{char}' shortcut conflicts with common screen reader shortcuts",
                "help": f"Avoid using '{char}' as single-key shortcut. Use Ctrl+{char} or Alt+{char} instead, or provide turn-off mechanism"
            }
        }

        config = violation_configs.get(issue_type)
        if not config:
            return None

        # Build detailed help text
        help_text = config["help"]
        shortcut_type = issue.get("shortcutType", "unknown")

        if shortcut_type == "accesskey":
            help_text += f" (Currently using accesskey='{char}')"
        elif issue.get("reason"):
            help_text = f"{issue.get('reason')}. {help_text}"

        return Violation(
            id=f"{config['id']}-{hash(issue.get('selector', '')) % 10000}",
            rule_id=config["rule_id"],
            wcag_criteria=config["wcag"],
            wcag_level=config["level"],
            impact=config["impact"],
            description=config["description"],
            help_text=help_text,
            help_url="https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html",
            detected_by=["character-shortcuts"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["keyboard", "shortcuts", "wcag214", "level-a"]
        )
