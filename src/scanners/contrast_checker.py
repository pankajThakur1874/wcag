"""Color contrast checker scanner implementation."""

import re
from typing import Optional, Tuple
from bs4 import BeautifulSoup
import cssutils
import logging

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

# Suppress cssutils logging
cssutils.log.setLevel(logging.CRITICAL)

logger = get_logger(__name__)


class ContrastChecker(BaseScanner):
    """Scanner for color contrast issues."""

    name = "contrast"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check color contrast on the page.

        Args:
            url: URL to scan
            html_content: Pre-fetched HTML content (ignored, needs computed styles)

        Returns:
            List of violations
        """
        if self._browser_manager is None:
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

        try:
            async with self._browser_manager.get_page(url) as page:
                return await self._check_contrast(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_contrast(self, page) -> list[Violation]:
        """Check contrast of text elements on the page."""
        violations = []

        # Get all text elements with their computed colors
        elements_data = await page.evaluate("""
            () => {
                const results = [];
                const textElements = document.querySelectorAll('p, span, a, li, td, th, h1, h2, h3, h4, h5, h6, label, button');

                for (const el of textElements) {
                    const text = el.textContent?.trim();
                    if (!text || text.length === 0) continue;

                    const style = window.getComputedStyle(el);
                    const color = style.color;
                    const bgColor = getBackgroundColor(el);
                    const fontSize = parseFloat(style.fontSize);
                    const fontWeight = style.fontWeight;

                    results.push({
                        tag: el.tagName.toLowerCase(),
                        text: text.substring(0, 50),
                        color: color,
                        backgroundColor: bgColor,
                        fontSize: fontSize,
                        fontWeight: fontWeight,
                        selector: getSelector(el),
                        html: el.outerHTML.substring(0, 200)
                    });

                    if (results.length >= 100) break;
                }

                return results;

                function getBackgroundColor(element) {
                    let el = element;
                    while (el) {
                        const style = window.getComputedStyle(el);
                        const bg = style.backgroundColor;
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                            return bg;
                        }
                        el = el.parentElement;
                    }
                    return 'rgb(255, 255, 255)';
                }

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className) return el.tagName.toLowerCase() + '.' + el.className.split(' ')[0];
                    return el.tagName.toLowerCase();
                }
            }
        """)

        for elem_data in elements_data:
            try:
                fg_rgb = self._parse_color(elem_data["color"])
                bg_rgb = self._parse_color(elem_data["backgroundColor"])

                if fg_rgb is None or bg_rgb is None:
                    continue

                contrast_ratio = self._calculate_contrast(fg_rgb, bg_rgb)
                font_size = elem_data.get("fontSize", 16)
                font_weight = elem_data.get("fontWeight", "400")

                # Determine if text is large
                # Large text: 18pt (24px) or 14pt (18.66px) bold
                is_large = font_size >= 24 or (font_size >= 18.66 and int(font_weight) >= 700)

                # WCAG AA requirements
                min_ratio_aa = 3.0 if is_large else 4.5
                # WCAG AAA requirements
                min_ratio_aaa = 4.5 if is_large else 7.0

                if contrast_ratio < min_ratio_aa:
                    violations.append(Violation(
                        id=f"contrast-aa-fail-{hash(elem_data['selector']) % 10000}",
                        rule_id="color-contrast",
                        wcag_criteria=["1.4.3"],
                        wcag_level=WCAGLevel.AA,
                        impact=Impact.SERIOUS,
                        description=f"Color contrast ratio {contrast_ratio:.2f}:1 is below WCAG AA requirement of {min_ratio_aa}:1",
                        help_text=f"Foreground: {elem_data['color']}, Background: {elem_data['backgroundColor']}. Increase contrast to at least {min_ratio_aa}:1.",
                        detected_by=["contrast"],
                        instances=[ViolationInstance(
                            html=elem_data.get("html", ""),
                            selector=elem_data.get("selector", ""),
                            fix_suggestion=f"Current ratio: {contrast_ratio:.2f}:1. Need at least {min_ratio_aa}:1 for AA compliance."
                        )],
                        tags=["contrast", "wcag1.4.3"]
                    ))
                elif contrast_ratio < min_ratio_aaa:
                    # Log AAA failures but don't include as violations by default
                    logger.debug(
                        f"AAA contrast fail at {elem_data['selector']}: "
                        f"{contrast_ratio:.2f}:1 < {min_ratio_aaa}:1"
                    )

            except Exception as e:
                logger.debug(f"Error checking contrast for element: {e}")
                continue

        return violations

    def _parse_color(self, color_str: str) -> Optional[Tuple[int, int, int]]:
        """Parse a color string to RGB tuple."""
        if not color_str:
            return None

        # Handle rgb/rgba format
        match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color_str)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))

        # Handle hex format
        if color_str.startswith("#"):
            hex_color = color_str.lstrip("#")
            if len(hex_color) == 3:
                hex_color = "".join([c * 2 for c in hex_color])
            if len(hex_color) == 6:
                return (
                    int(hex_color[0:2], 16),
                    int(hex_color[2:4], 16),
                    int(hex_color[4:6], 16)
                )

        return None

    def _calculate_contrast(self, fg: Tuple[int, int, int], bg: Tuple[int, int, int]) -> float:
        """
        Calculate contrast ratio between two colors.

        Uses WCAG relative luminance formula.
        """
        def get_luminance(rgb: Tuple[int, int, int]) -> float:
            def adjust(c: int) -> float:
                c_srgb = c / 255
                if c_srgb <= 0.03928:
                    return c_srgb / 12.92
                return ((c_srgb + 0.055) / 1.055) ** 2.4

            r, g, b = rgb
            return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

        l1 = get_luminance(fg)
        l2 = get_luminance(bg)

        lighter = max(l1, l2)
        darker = min(l1, l2)

        return (lighter + 0.05) / (darker + 0.05)
