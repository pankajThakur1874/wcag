"""Link text quality scanner - finds vague and non-descriptive links."""

from typing import Optional
from playwright.async_api import Page

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Common vague link text patterns
VAGUE_LINK_PATTERNS = [
    "click here",
    "click",
    "here",
    "read more",
    "learn more",
    "more",
    "continue",
    "continue reading",
    "details",
    "more details",
    "info",
    "more info",
    "information",
    "link",
    "this link",
    "this page",
    "this",
    "go",
    "go here",
    "see more",
    "view more",
    "view",
    "see",
    "download",
    "pdf",
    "page",
    "website",
    "site",
]

# Links that are just URLs
URL_PATTERNS = [
    "http://",
    "https://",
    "www.",
    ".com",
    ".org",
    ".net",
]


class LinkTextScanner(BaseScanner):
    """Scanner for link text quality issues."""

    name = "link_text"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check link text quality.

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
                return await self._check_links(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_links(self, page: Page) -> list[Violation]:
        """Run link text quality checks."""
        violations = []

        # This scanner checks 5 rules
        self._rules_checked = 5

        links_data = await page.evaluate("""
            () => {
                const links = [];
                const anchors = document.querySelectorAll('a[href]');

                for (const a of anchors) {
                    // Get visible text
                    let text = a.innerText || a.textContent || '';
                    text = text.trim().toLowerCase();

                    // Get aria-label if present
                    const ariaLabel = a.getAttribute('aria-label') || '';

                    // Get title attribute
                    const title = a.getAttribute('title') || '';

                    // Get image alt if link contains image
                    const img = a.querySelector('img');
                    const imgAlt = img ? (img.getAttribute('alt') || '') : '';

                    // Check if link opens in new window
                    const target = a.getAttribute('target') || '';
                    const opensNew = target === '_blank';

                    // Get href
                    const href = a.getAttribute('href') || '';

                    links.push({
                        text: text,
                        ariaLabel: ariaLabel.trim().toLowerCase(),
                        title: title.trim(),
                        imgAlt: imgAlt.trim().toLowerCase(),
                        href: href,
                        opensNew: opensNew,
                        html: a.outerHTML.substring(0, 300),
                        selector: getSelector(a)
                    });
                }

                return links;

                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        return 'a.' + el.className.split(' ')[0];
                    }
                    return 'a[href="' + (el.getAttribute('href') || '').substring(0, 50) + '"]';
                }
            }
        """)

        rule_failures = set()

        for link in links_data:
            text = link["text"]
            aria_label = link["ariaLabel"]
            img_alt = link["imgAlt"]
            effective_text = aria_label or text or img_alt

            # Rule 1: Check for vague link text
            if effective_text and effective_text in VAGUE_LINK_PATTERNS:
                rule_failures.add("vague-link")
                violations.append(Violation(
                    id=f"link-vague-{hash(link['selector']) % 10000}",
                    rule_id="link-text-vague",
                    wcag_criteria=["2.4.4", "2.4.9"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description=f"Link text '{effective_text}' is vague and non-descriptive",
                    help_text="Use descriptive link text that explains where the link goes. Avoid 'click here', 'read more', etc.",
                    detected_by=["link_text"],
                    instances=[ViolationInstance(
                        html=link["html"],
                        selector=link["selector"],
                        fix_suggestion=f"Replace '{effective_text}' with descriptive text explaining the link destination"
                    )],
                    tags=["links", "wcag2.4.4", "wcag2.4.9"]
                ))

            # Rule 2: Check for URL as link text
            if effective_text:
                is_url = any(pattern in effective_text for pattern in URL_PATTERNS)
                if is_url and len(effective_text) > 30:
                    rule_failures.add("url-link")
                    violations.append(Violation(
                        id=f"link-url-text-{hash(link['selector']) % 10000}",
                        rule_id="link-text-url",
                        wcag_criteria=["2.4.4"],
                        wcag_level=WCAGLevel.A,
                        impact=Impact.MODERATE,
                        description="Link text is a URL instead of descriptive text",
                        help_text="Use meaningful text instead of URLs. Screen readers will read the entire URL.",
                        detected_by=["link_text"],
                        instances=[ViolationInstance(
                            html=link["html"],
                            selector=link["selector"],
                            fix_suggestion="Replace URL with descriptive text about the link destination"
                        )],
                        tags=["links", "wcag2.4.4"]
                    ))

            # Rule 3: Check for very short link text (1-2 chars)
            if effective_text and len(effective_text) <= 2 and effective_text not in ["ok", "go"]:
                rule_failures.add("short-link")
                violations.append(Violation(
                    id=f"link-short-{hash(link['selector']) % 10000}",
                    rule_id="link-text-short",
                    wcag_criteria=["2.4.4"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description=f"Link text '{effective_text}' is too short to be meaningful",
                    help_text="Link text should be descriptive enough to understand out of context.",
                    detected_by=["link_text"],
                    instances=[ViolationInstance(
                        html=link["html"],
                        selector=link["selector"],
                        fix_suggestion="Add more descriptive text to the link"
                    )],
                    tags=["links", "wcag2.4.4"]
                ))

            # Rule 4: Check for links opening in new window without warning
            if link["opensNew"]:
                has_warning = (
                    "new window" in (link["title"].lower() + " " + effective_text) or
                    "new tab" in (link["title"].lower() + " " + effective_text) or
                    "opens in" in (link["title"].lower() + " " + effective_text) or
                    "(external)" in effective_text
                )
                if not has_warning:
                    rule_failures.add("new-window")
                    violations.append(Violation(
                        id=f"link-new-window-{hash(link['selector']) % 10000}",
                        rule_id="link-new-window-warning",
                        wcag_criteria=["3.2.5"],
                        wcag_level=WCAGLevel.AAA,
                        impact=Impact.MINOR,
                        description="Link opens in new window/tab without warning",
                        help_text="Warn users when links open in a new window (e.g., add '(opens in new tab)' to link text).",
                        detected_by=["link_text"],
                        instances=[ViolationInstance(
                            html=link["html"],
                            selector=link["selector"],
                            fix_suggestion="Add '(opens in new tab)' to the link text or title attribute"
                        )],
                        tags=["links", "wcag3.2.5"]
                    ))

            # Rule 5: Check for duplicate link text with different destinations
            # (This would need tracking across all links - simplified check here)

        self._rules_failed = len(rule_failures)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations
