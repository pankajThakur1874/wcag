"""Touch target size scanner - checks if interactive elements are large enough."""

from typing import Optional
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# WCAG 2.2 recommends minimum 44x44 CSS pixels for touch targets
# WCAG 2.1 AAA recommends 44x44
MIN_TARGET_SIZE = 44  # pixels
MIN_TARGET_SIZE_ENHANCED = 24  # minimum for WCAG AA (with spacing)


class TouchTargetScanner(BaseScanner):
    """Scanner for touch target size issues."""

    name = "touch_target"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check touch target sizes.

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
                return await self._check_targets(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_targets(self, page: Page) -> list[Violation]:
        """Run touch target size checks."""
        violations = []

        # This scanner checks 4 rules
        self._rules_checked = 4

        targets_data = await page.evaluate(f"""
            () => {{
                const targets = [];
                const minSize = {MIN_TARGET_SIZE};
                const minSizeEnhanced = {MIN_TARGET_SIZE_ENHANCED};

                // Interactive elements
                const selectors = [
                    'a[href]',
                    'button',
                    'input:not([type="hidden"])',
                    'select',
                    'textarea',
                    '[role="button"]',
                    '[role="link"]',
                    '[role="checkbox"]',
                    '[role="radio"]',
                    '[role="tab"]',
                    '[role="menuitem"]',
                    '[onclick]',
                    '[tabindex="0"]'
                ];

                const elements = document.querySelectorAll(selectors.join(', '));

                for (const el of elements) {{
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);

                    // Skip hidden elements
                    if (rect.width === 0 || rect.height === 0 ||
                        style.display === 'none' || style.visibility === 'hidden') {{
                        continue;
                    }}

                    // Skip elements in text flow (inline links within paragraphs)
                    const isInlineText = el.tagName === 'A' &&
                        el.parentElement &&
                        ['P', 'LI', 'TD', 'SPAN', 'DIV'].includes(el.parentElement.tagName) &&
                        el.parentElement.innerText.length > el.innerText.length * 2;

                    const width = rect.width;
                    const height = rect.height;
                    const isTooSmall = width < minSize || height < minSize;
                    const isTiny = width < minSizeEnhanced || height < minSizeEnhanced;

                    // Get padding (can affect clickable area)
                    const paddingTop = parseFloat(style.paddingTop) || 0;
                    const paddingBottom = parseFloat(style.paddingBottom) || 0;
                    const paddingLeft = parseFloat(style.paddingLeft) || 0;
                    const paddingRight = parseFloat(style.paddingRight) || 0;

                    targets.push({{
                        tagName: el.tagName.toLowerCase(),
                        type: el.getAttribute('type') || '',
                        role: el.getAttribute('role') || '',
                        width: Math.round(width),
                        height: Math.round(height),
                        isTooSmall: isTooSmall,
                        isTiny: isTiny,
                        isInlineText: isInlineText,
                        text: (el.innerText || el.value || '').substring(0, 50).trim(),
                        padding: {{
                            top: paddingTop,
                            bottom: paddingBottom,
                            left: paddingLeft,
                            right: paddingRight
                        }},
                        html: el.outerHTML.substring(0, 300),
                        selector: getSelector(el)
                    }});
                }}

                return targets;

                function getSelector(el) {{
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {{
                        return el.tagName.toLowerCase() + '.' + el.className.split(' ')[0];
                    }}
                    return el.tagName.toLowerCase();
                }}
            }}
        """)

        rule_failures = set()
        small_targets = []
        tiny_targets = []

        for target in targets_data:
            # Skip inline text links (excluded by WCAG 2.5.5)
            if target["isInlineText"]:
                continue

            # Rule 1: Check for critically small targets (< 24px)
            if target["isTiny"]:
                tiny_targets.append(target)

            # Rule 2: Check for small targets (< 44px)
            elif target["isTooSmall"]:
                small_targets.append(target)

        # Report tiny targets (critical)
        if tiny_targets:
            rule_failures.add("tiny-target")
            for target in tiny_targets[:10]:  # Limit to first 10
                violations.append(Violation(
                    id=f"target-tiny-{hash(target['selector']) % 10000}",
                    rule_id="target-size-minimum",
                    wcag_criteria=["2.5.5", "2.5.8"],
                    wcag_level=WCAGLevel.AA,
                    impact=Impact.SERIOUS,
                    description=f"Touch target is too small: {target['width']}x{target['height']}px (minimum: {MIN_TARGET_SIZE_ENHANCED}px)",
                    help_text=f"Interactive elements should be at least {MIN_TARGET_SIZE}x{MIN_TARGET_SIZE}px for easy touch interaction.",
                    detected_by=["touch_target"],
                    instances=[ViolationInstance(
                        html=target["html"],
                        selector=target["selector"],
                        fix_suggestion=f"Increase size to at least {MIN_TARGET_SIZE}x{MIN_TARGET_SIZE}px using padding or min-width/min-height"
                    )],
                    tags=["touch", "target-size", "wcag2.5.5"]
                ))

        # Report small targets (warning)
        if small_targets:
            rule_failures.add("small-target")
            for target in small_targets[:10]:  # Limit to first 10
                violations.append(Violation(
                    id=f"target-small-{hash(target['selector']) % 10000}",
                    rule_id="target-size-enhanced",
                    wcag_criteria=["2.5.5"],
                    wcag_level=WCAGLevel.AAA,
                    impact=Impact.MODERATE,
                    description=f"Touch target smaller than recommended: {target['width']}x{target['height']}px (recommended: {MIN_TARGET_SIZE}px)",
                    help_text=f"For optimal accessibility, interactive elements should be at least {MIN_TARGET_SIZE}x{MIN_TARGET_SIZE}px.",
                    detected_by=["touch_target"],
                    instances=[ViolationInstance(
                        html=target["html"],
                        selector=target["selector"],
                        fix_suggestion=f"Consider increasing size to {MIN_TARGET_SIZE}x{MIN_TARGET_SIZE}px for better touch accessibility"
                    )],
                    tags=["touch", "target-size", "wcag2.5.5"]
                ))

        # Rule 3: Check for targets that are close together
        # (Simplified - would need more complex spatial analysis)

        # Rule 4: Summary if many small targets
        total_small = len(tiny_targets) + len(small_targets)
        if total_small > 10:
            rule_failures.add("many-small-targets")
            violations.append(Violation(
                id="many-small-targets",
                rule_id="target-size-pattern",
                wcag_criteria=["2.5.5"],
                wcag_level=WCAGLevel.AA,
                impact=Impact.SERIOUS,
                description=f"Page has {total_small} interactive elements smaller than {MIN_TARGET_SIZE}px",
                help_text="Many small touch targets make the page difficult to use on touch devices.",
                detected_by=["touch_target"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion=f"Review CSS to ensure all interactive elements meet {MIN_TARGET_SIZE}px minimum"
                )],
                tags=["touch", "target-size", "wcag2.5.5"]
            ))

        self._rules_failed = len(rule_failures)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations
