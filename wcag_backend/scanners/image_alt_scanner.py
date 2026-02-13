"""Image alt text quality scanner - finds poor or meaningless alt text."""

from typing import Optional
import re
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Patterns for bad alt text
BAD_ALT_PATTERNS = [
    r"^image$",
    r"^img$",
    r"^photo$",
    r"^picture$",
    r"^graphic$",
    r"^icon$",
    r"^logo$",
    r"^banner$",
    r"^placeholder$",
    r"^untitled$",
    r"^null$",
    r"^none$",
    r"^spacer$",
    r"^blank$",
    r"^\s*$",
]

# Patterns for filename-like alt text
FILENAME_PATTERNS = [
    r"\.jpg$",
    r"\.jpeg$",
    r"\.png$",
    r"\.gif$",
    r"\.svg$",
    r"\.webp$",
    r"\.bmp$",
    r"\.ico$",
    r"^img[-_]?\d+",
    r"^image[-_]?\d+",
    r"^dsc[-_]?\d+",
    r"^screenshot",
    r"^screen[-_]?shot",
    r"^photo[-_]?\d+",
    r"[-_]\d{3,}",  # Contains long number sequences typical of auto-generated names
]

# Redundant phrases that shouldn't be in alt text
REDUNDANT_PHRASES = [
    "image of",
    "picture of",
    "photo of",
    "graphic of",
    "icon of",
    "photograph of",
    "illustration of",
]


class ImageAltScanner(BaseScanner):
    """Scanner for image alt text quality issues."""

    name = "image_alt"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check image alt text quality.

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
                return await self._check_images(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_images(self, page: Page) -> list[Violation]:
        """Run image alt text quality checks."""
        violations = []

        # This scanner checks 6 rules
        self._rules_checked = 6

        images_data = await page.evaluate("""
            () => {
                const images = [];
                const imgs = document.querySelectorAll('img');

                for (const img of imgs) {
                    const alt = img.getAttribute('alt');
                    const src = img.getAttribute('src') || '';
                    const role = img.getAttribute('role') || '';
                    const ariaHidden = img.getAttribute('aria-hidden') === 'true';
                    const isDecorative = alt === '' || role === 'presentation' || ariaHidden;

                    // Get dimensions
                    const rect = img.getBoundingClientRect();
                    const width = rect.width;
                    const height = rect.height;

                    // Check if image is visible
                    const isVisible = width > 0 && height > 0;

                    // Check if it's a functional image (in a link or button)
                    const inLink = !!img.closest('a');
                    const inButton = !!img.closest('button');
                    const isFunctional = inLink || inButton;

                    images.push({
                        alt: alt,
                        src: src,
                        role: role,
                        ariaHidden: ariaHidden,
                        isDecorative: isDecorative,
                        isVisible: isVisible,
                        isFunctional: isFunctional,
                        width: width,
                        height: height,
                        html: img.outerHTML.substring(0, 300),
                        selector: getSelector(img)
                    });
                }

                return images;

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        return 'img.' + el.className.split(' ')[0];
                    }
                    const src = el.getAttribute('src') || '';
                    const filename = src.split('/').pop().split('?')[0];
                    return 'img[src*="' + filename.substring(0, 30) + '"]';
                }
            }
        """)

        rule_failures = set()

        for img in images_data:
            # Skip invisible images
            if not img["isVisible"]:
                continue

            alt = img["alt"]
            src = img["src"].lower()
            is_decorative = img["isDecorative"]
            is_functional = img["isFunctional"]

            # Rule 1: Check for missing alt attribute (null, not empty string)
            if alt is None:
                rule_failures.add("missing-alt")
                violations.append(Violation(
                    id=f"img-no-alt-{hash(img['selector']) % 10000}",
                    rule_id="image-alt-missing",
                    wcag_criteria=["1.1.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.CRITICAL,
                    description="Image is missing alt attribute entirely",
                    help_text="Add alt attribute. Use alt='' for decorative images or descriptive text for meaningful images.",
                    detected_by=["image_alt"],
                    instances=[ViolationInstance(
                        html=img["html"],
                        selector=img["selector"],
                        fix_suggestion="Add alt='description' or alt='' for decorative images"
                    )],
                    tags=["images", "wcag1.1.1"]
                ))
                continue

            alt_lower = alt.lower().strip()

            # Skip decorative images (empty alt is intentional)
            if is_decorative and alt == '':
                continue

            # Rule 2: Check for generic/meaningless alt text
            for pattern in BAD_ALT_PATTERNS:
                if re.match(pattern, alt_lower):
                    rule_failures.add("generic-alt")
                    violations.append(Violation(
                        id=f"img-generic-alt-{hash(img['selector']) % 10000}",
                        rule_id="image-alt-generic",
                        wcag_criteria=["1.1.1"],
                        wcag_level=WCAGLevel.A,
                        impact=Impact.SERIOUS,
                        description=f"Image alt text '{alt}' is generic and not descriptive",
                        help_text="Alt text should describe the image content, not just say 'image' or 'photo'.",
                        detected_by=["image_alt"],
                        instances=[ViolationInstance(
                            html=img["html"],
                            selector=img["selector"],
                            fix_suggestion="Replace with descriptive alt text explaining what the image shows"
                        )],
                        tags=["images", "wcag1.1.1"]
                    ))
                    break

            # Rule 3: Check for filename as alt text
            for pattern in FILENAME_PATTERNS:
                if re.search(pattern, alt_lower):
                    rule_failures.add("filename-alt")
                    violations.append(Violation(
                        id=f"img-filename-alt-{hash(img['selector']) % 10000}",
                        rule_id="image-alt-filename",
                        wcag_criteria=["1.1.1"],
                        wcag_level=WCAGLevel.A,
                        impact=Impact.SERIOUS,
                        description=f"Image alt text '{alt}' appears to be a filename",
                        help_text="Alt text should describe the image, not be the filename.",
                        detected_by=["image_alt"],
                        instances=[ViolationInstance(
                            html=img["html"],
                            selector=img["selector"],
                            fix_suggestion="Replace filename with meaningful description of the image"
                        )],
                        tags=["images", "wcag1.1.1"]
                    ))
                    break

            # Rule 4: Check for redundant phrases
            for phrase in REDUNDANT_PHRASES:
                if alt_lower.startswith(phrase):
                    rule_failures.add("redundant-alt")
                    violations.append(Violation(
                        id=f"img-redundant-alt-{hash(img['selector']) % 10000}",
                        rule_id="image-alt-redundant",
                        wcag_criteria=["1.1.1"],
                        wcag_level=WCAGLevel.A,
                        impact=Impact.MINOR,
                        description=f"Image alt text starts with redundant phrase '{phrase}'",
                        help_text="Don't start alt text with 'image of', 'photo of', etc. Screen readers already announce it's an image.",
                        detected_by=["image_alt"],
                        instances=[ViolationInstance(
                            html=img["html"],
                            selector=img["selector"],
                            fix_suggestion=f"Remove '{phrase}' from the beginning of the alt text"
                        )],
                        tags=["images", "wcag1.1.1"]
                    ))
                    break

            # Rule 5: Check for very long alt text
            if len(alt) > 150:
                rule_failures.add("long-alt")
                violations.append(Violation(
                    id=f"img-long-alt-{hash(img['selector']) % 10000}",
                    rule_id="image-alt-long",
                    wcag_criteria=["1.1.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MINOR,
                    description=f"Image alt text is very long ({len(alt)} characters)",
                    help_text="Alt text should be concise. For complex images, use longdesc or describe in surrounding text.",
                    detected_by=["image_alt"],
                    instances=[ViolationInstance(
                        html=img["html"],
                        selector=img["selector"],
                        fix_suggestion="Shorten alt text or use aria-describedby for detailed descriptions"
                    )],
                    tags=["images", "wcag1.1.1"]
                ))

            # Rule 6: Functional image without descriptive alt
            if is_functional and alt == '':
                rule_failures.add("functional-no-alt")
                violations.append(Violation(
                    id=f"img-functional-no-alt-{hash(img['selector']) % 10000}",
                    rule_id="image-functional-alt",
                    wcag_criteria=["1.1.1", "2.4.4"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.CRITICAL,
                    description="Functional image (in link/button) has empty alt text",
                    help_text="Images that are links or buttons must have alt text describing their function.",
                    detected_by=["image_alt"],
                    instances=[ViolationInstance(
                        html=img["html"],
                        selector=img["selector"],
                        fix_suggestion="Add alt text describing what happens when clicking the image"
                    )],
                    tags=["images", "wcag1.1.1", "wcag2.4.4"]
                ))

        self._rules_failed = len(rule_failures)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations
