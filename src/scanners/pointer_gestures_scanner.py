"""Pointer Gestures Scanner - WCAG 2.5.1, 2.5.2, 2.5.7 (Level A/AA)

Detects pointer gesture functionality that may not have single-pointer alternatives,
pointer cancellation issues, and dragging without keyboard alternatives.
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PointerGesturesScanner(BaseScanner):
    """Scanner for pointer gesture and interaction issues."""

    name = "pointer-gestures"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check pointer gesture accessibility.

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
                return await self._check_pointer_gestures(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_pointer_gestures(self, page: Page) -> list[Violation]:
        """Run pointer gesture checks."""
        violations = []

        # This scanner checks 6 rules
        self._rules_checked = 6

        issues = await page.evaluate("""
            () => {
                const issues = [];

                // Helper function
                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        return el.tagName.toLowerCase() + '.' + classes[0];
                    }
                    return el.tagName.toLowerCase();
                }

                // Helper: Check if element has keyboard alternative
                function hasKeyboardAlternative(el) {
                    return el.hasAttribute('tabindex') &&
                           (el.hasAttribute('onkeydown') ||
                            el.hasAttribute('onkeyup') ||
                            el.hasAttribute('onkeypress'));
                }

                // 1. Check for multi-touch gesture handlers (2.5.1 - Pointer Gestures)
                const multiTouchPatterns = [
                    'touchstart', 'touchmove', 'touchend',
                    'gesturestart', 'gesturechange', 'gestureend',
                    'pointerdown', 'pointermove', 'pointerup'
                ];

                // Scan inline event handlers
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const attrs = Array.from(el.attributes);

                    for (const attr of attrs) {
                        const attrName = attr.name.toLowerCase();

                        // Check for touch/gesture handlers
                        if (multiTouchPatterns.some(pattern => attrName.includes(pattern))) {
                            // Check for single-pointer alternative
                            const hasClick = el.hasAttribute('onclick') || el.hasAttribute('click');
                            const hasMouseHandler = el.hasAttribute('onmousedown') ||
                                                   el.hasAttribute('onmouseup');

                            if (!hasClick && !hasMouseHandler) {
                                issues.push({
                                    type: 'multi-touch-no-alternative',
                                    element: el.outerHTML.substring(0, 300),
                                    selector: getSelector(el),
                                    handler: attrName,
                                    wcag: '2.5.1'
                                });
                            }
                        }
                    }

                    // Check class names for gesture libraries
                    const className = el.className || '';
                    const usesGestureLibrary = /swipe|pinch|zoom|rotate|hammer|gesture/i.test(className);

                    if (usesGestureLibrary) {
                        // Check for alternative controls (buttons for zoom, etc.)
                        const hasButtons = el.querySelector('button') !== null;

                        if (!hasButtons) {
                            issues.push({
                                type: 'gesture-library-no-alternative',
                                element: el.outerHTML.substring(0, 300),
                                selector: getSelector(el),
                                className: className,
                                wcag: '2.5.1'
                            });
                        }
                    }
                }

                // 2. Check for down-event handlers without up-event completion (2.5.2 - Pointer Cancellation)
                for (const el of allElements) {
                    const hasMouseDown = el.hasAttribute('onmousedown');
                    const hasTouchStart = el.hasAttribute('ontouchstart');
                    const hasPointerDown = el.hasAttribute('onpointerdown');

                    if (hasMouseDown || hasTouchStart || hasPointerDown) {
                        // Check if action completes on down event (anti-pattern)
                        const mouseDownCode = el.getAttribute('onmousedown') || '';
                        const touchStartCode = el.getAttribute('ontouchstart') || '';

                        // Simple heuristic: if down-event calls functions, might be completing on down
                        const triggersOnDown = /\\(\\)/.test(mouseDownCode) || /\\(\\)/.test(touchStartCode);

                        if (triggersOnDown) {
                            // Check for corresponding up-event
                            const hasMouseUp = el.hasAttribute('onmouseup');
                            const hasTouchEnd = el.hasAttribute('ontouchend');
                            const hasClick = el.hasAttribute('onclick');

                            if (!hasMouseUp && !hasTouchEnd && !hasClick) {
                                issues.push({
                                    type: 'down-event-completion',
                                    element: el.outerHTML.substring(0, 300),
                                    selector: getSelector(el),
                                    handler: hasMouseDown ? 'onmousedown' : 'ontouchstart',
                                    wcag: '2.5.2'
                                });
                            }
                        }
                    }
                }

                // 3. Check for draggable elements without keyboard alternative (2.5.7 - Dragging Movements)
                const draggableElements = document.querySelectorAll('[draggable="true"]');

                for (const el of draggableElements) {
                    // Check for keyboard alternative (arrow key handlers, buttons to move)
                    const hasKeyboard = hasKeyboardAlternative(el);

                    // Check for nearby move buttons
                    const parent = el.parentElement;
                    const hasMoveButtons = parent && (
                        parent.querySelector('[aria-label*="move"]') ||
                        parent.querySelector('button[class*="move"]') ||
                        parent.querySelector('[class*="arrow"]')
                    );

                    if (!hasKeyboard && !hasMoveButtons) {
                        issues.push({
                            type: 'draggable-no-keyboard',
                            element: el.outerHTML.substring(0, 300),
                            selector: getSelector(el),
                            wcag: '2.5.7'
                        });
                    }
                }

                // Check for drag-drop class patterns
                const dragDropPatterns = document.querySelectorAll(
                    '[class*="drag"], [class*="sortable"], [class*="droppable"]'
                );

                for (const el of dragDropPatterns) {
                    const className = el.className || '';

                    if (/drag|sortable|droppable/i.test(className)) {
                        // Skip if already checked as draggable
                        if (el.draggable) continue;

                        // Check for keyboard alternative
                        const hasKeyboard = hasKeyboardAlternative(el);
                        const container = el.closest('[class*="container"]') || el.parentElement;
                        const hasMoveButtons = container && container.querySelector('button[aria-label*="move"]');

                        if (!hasKeyboard && !hasMoveButtons) {
                            issues.push({
                                type: 'drag-class-no-keyboard',
                                element: el.outerHTML.substring(0, 300),
                                selector: getSelector(el),
                                className: className,
                                wcag: '2.5.7'
                            });
                        }
                    }
                }

                // 4. Check for swipe/slider gestures
                const sliders = document.querySelectorAll(
                    'input[type="range"], [role="slider"], [class*="slider"], [class*="carousel"]'
                );

                for (const slider of sliders) {
                    // Range inputs are inherently keyboard accessible
                    if (slider.tagName === 'INPUT' && slider.type === 'range') continue;

                    // Check for keyboard controls
                    const hasKeyboard = hasKeyboardAlternative(slider);

                    // Check for prev/next buttons
                    const container = slider.closest('[class*="slider"]') ||
                                     slider.closest('[class*="carousel"]') ||
                                     slider.parentElement;

                    const hasNavButtons = container && (
                        container.querySelector('[class*="prev"]') ||
                        container.querySelector('[class*="next"]') ||
                        container.querySelector('[aria-label*="previous"]') ||
                        container.querySelector('[aria-label*="next"]')
                    );

                    if (!hasKeyboard && !hasNavButtons) {
                        issues.push({
                            type: 'slider-no-alternative',
                            element: slider.outerHTML.substring(0, 300),
                            selector: getSelector(slider),
                            wcag: '2.5.1'
                        });
                    }
                }

                // 5. Check for pinch-zoom without alternative zoom controls
                const zoomableElements = document.querySelectorAll(
                    '[class*="zoom"], [class*="pinch"], img[class*="zoomable"]'
                );

                for (const el of zoomableElements) {
                    const className = el.className || '';

                    if (/zoom|pinch/i.test(className)) {
                        // Look for zoom buttons
                        const container = el.closest('[class*="container"]') || el.parentElement;
                        const hasZoomButtons = container && (
                            container.querySelector('[aria-label*="zoom in"]') ||
                            container.querySelector('[aria-label*="zoom out"]') ||
                            container.querySelector('[class*="zoom-in"]') ||
                            container.querySelector('[class*="zoom-out"]')
                        );

                        if (!hasZoomButtons) {
                            issues.push({
                                type: 'zoom-no-alternative',
                                element: el.outerHTML.substring(0, 300),
                                selector: getSelector(el),
                                className: className,
                                wcag: '2.5.1'
                            });
                        }
                    }
                }

                // 6. Check for path-based gestures (drawing, signatures)
                const canvasElements = document.querySelectorAll('canvas');

                for (const canvas of canvasElements) {
                    const className = canvas.className || '';
                    const ariaLabel = canvas.getAttribute('aria-label') || '';

                    // Check if it's a signature or drawing canvas
                    const isPathBased = /signature|draw|sketch|paint/i.test(className + ariaLabel);

                    if (isPathBased) {
                        // Check for alternative input method
                        const container = canvas.closest('form') ||
                                         canvas.closest('[class*="container"]') ||
                                         canvas.parentElement;

                        const hasAlternative = container && (
                            container.querySelector('input[type="text"]') ||
                            container.querySelector('input[type="file"]') ||
                            container.querySelector('[aria-label*="type"]')
                        );

                        if (!hasAlternative) {
                            issues.push({
                                type: 'path-based-no-alternative',
                                element: canvas.outerHTML.substring(0, 300),
                                selector: getSelector(canvas),
                                wcag: '2.5.1'
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
                rule_types_failed.add(issue.get("wcag"))

        # Update rules failed count
        self._rules_failed = len(rule_types_failed)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    def _create_violation(self, issue: dict) -> Optional[Violation]:
        """Create violation from issue data."""
        issue_type = issue.get("type")

        violation_configs = {
            "multi-touch-no-alternative": {
                "id": "gesture-multi-touch",
                "rule_id": "pointer-gestures",
                "wcag": ["2.5.1"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": f"Element has multi-touch handler ({issue.get('handler')}) without single-pointer alternative",
                "help": "Add onclick or mouse event handler as single-pointer alternative to touch gestures"
            },
            "gesture-library-no-alternative": {
                "id": "gesture-library",
                "rule_id": "pointer-gestures",
                "wcag": ["2.5.1"],
                "level": WCAGLevel.A,
                "impact": Impact.SERIOUS,
                "description": "Element uses gesture library without alternative controls",
                "help": "Provide buttons or single-pointer alternatives (e.g., +/- buttons for zoom, arrow buttons for swipe)"
            },
            "down-event-completion": {
                "id": "pointer-down-event",
                "rule_id": "pointer-cancellation",
                "wcag": ["2.5.2"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": f"Action may complete on {issue.get('handler')} without ability to cancel",
                "help": "Complete actions on mouseup/touchend/click events, not on down events. Allow cancellation by moving pointer away before release"
            },
            "draggable-no-keyboard": {
                "id": "drag-no-keyboard",
                "rule_id": "dragging-movements",
                "wcag": ["2.5.7"],
                "level": WCAGLevel.AA,
                "impact": Impact.SERIOUS,
                "description": "Draggable element lacks keyboard alternative for moving",
                "help": "Add keyboard event handlers (arrow keys) or provide move up/down/left/right buttons"
            },
            "drag-class-no-keyboard": {
                "id": "drag-class-no-keyboard",
                "rule_id": "dragging-movements",
                "wcag": ["2.5.7"],
                "level": WCAGLevel.AA,
                "impact": Impact.SERIOUS,
                "description": f"Element with drag class ({issue.get('className')}) lacks keyboard alternative",
                "help": "Implement keyboard support (Space/Enter to grab, arrow keys to move) or provide action buttons"
            },
            "slider-no-alternative": {
                "id": "gesture-slider",
                "rule_id": "pointer-gestures",
                "wcag": ["2.5.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Slider/carousel requires swipe gesture without alternative navigation",
                "help": "Add previous/next buttons or make element keyboard accessible with arrow keys"
            },
            "zoom-no-alternative": {
                "id": "gesture-zoom",
                "rule_id": "pointer-gestures",
                "wcag": ["2.5.1"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Pinch-zoom functionality without single-pointer zoom controls",
                "help": "Provide +/- zoom buttons or double-click zoom as alternative to pinch gesture"
            },
            "path-based-no-alternative": {
                "id": "gesture-path-based",
                "rule_id": "pointer-gestures",
                "wcag": ["2.5.1"],
                "level": WCAGLevel.A,
                "impact": Impact.CRITICAL,
                "description": "Signature/drawing canvas requires path-based gesture without alternative input",
                "help": "Provide text input, file upload, or other non-gesture alternative for signatures/drawings"
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
            help_url=f"https://www.w3.org/WAI/WCAG22/Understanding/{config['wcag'][0].replace('.', '')}.html",
            detected_by=["pointer-gestures"],
            instances=[ViolationInstance(
                html=issue.get("element", ""),
                selector=issue.get("selector", ""),
                fix_suggestion=config["help"]
            )],
            tags=["pointer", "gestures", "touch", f"wcag{config['wcag'][0].replace('.', '')}"]
        )
