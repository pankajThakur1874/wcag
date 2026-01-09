"""HTML validator scanner implementation."""

import re
from typing import Optional
from bs4 import BeautifulSoup

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HTMLValidatorScanner(BaseScanner):
    """Scanner for HTML validation and structure checks."""

    name = "html_validator"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Validate HTML for accessibility issues.

        Args:
            url: URL to scan
            html_content: Pre-fetched HTML content

        Returns:
            List of violations
        """
        # Get HTML content if not provided
        if html_content is None:
            if self._browser_manager is None:
                self._browser_manager = BrowserManager()
                await self._browser_manager.start()

            try:
                html_content = await self._browser_manager.get_page_content(url)
            finally:
                if self._owns_browser and self._browser_manager:
                    await self._browser_manager.stop()
                    self._browser_manager = None

        # Parse HTML
        soup = BeautifulSoup(html_content, "lxml")

        violations = []

        # Run all checks
        violations.extend(self._check_lang_attribute(soup))
        violations.extend(self._check_page_title(soup))
        violations.extend(self._check_heading_hierarchy(soup))
        violations.extend(self._check_images_alt(soup))
        violations.extend(self._check_form_labels(soup))
        violations.extend(self._check_links(soup))
        violations.extend(self._check_tables(soup))
        violations.extend(self._check_landmarks(soup))
        violations.extend(self._check_skip_link(soup))

        return violations

    def _check_lang_attribute(self, soup: BeautifulSoup) -> list[Violation]:
        """Check for lang attribute on html element."""
        violations = []
        html_tag = soup.find("html")

        if html_tag and not html_tag.get("lang"):
            violations.append(Violation(
                id="html-validator-missing-lang",
                rule_id="html-has-lang",
                wcag_criteria=["3.1.1"],
                wcag_level=WCAGLevel.A,
                impact=Impact.SERIOUS,
                description="The <html> element must have a lang attribute",
                help_text="Add a lang attribute to the <html> element to indicate the language of the page content.",
                detected_by=["html_validator"],
                instances=[ViolationInstance(
                    html=str(html_tag)[:200] if html_tag else "<html>",
                    selector="html",
                    fix_suggestion="Add lang='en' or appropriate language code to the <html> element"
                )],
                tags=["language", "wcag3.1.1"]
            ))

        return violations

    def _check_page_title(self, soup: BeautifulSoup) -> list[Violation]:
        """Check for page title."""
        violations = []
        title = soup.find("title")

        if not title or not title.get_text(strip=True):
            violations.append(Violation(
                id="html-validator-missing-title",
                rule_id="document-title",
                wcag_criteria=["2.4.2"],
                wcag_level=WCAGLevel.A,
                impact=Impact.SERIOUS,
                description="Document must have a <title> element",
                help_text="Add a descriptive <title> element to the <head> of the document.",
                detected_by=["html_validator"],
                instances=[ViolationInstance(
                    html="<title></title>",
                    selector="head > title",
                    fix_suggestion="Add a descriptive title like <title>Page Title - Site Name</title>"
                )],
                tags=["title", "wcag2.4.2"]
            ))

        return violations

    def _check_heading_hierarchy(self, soup: BeautifulSoup) -> list[Violation]:
        """Check heading hierarchy."""
        violations = []
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        # Check for missing h1
        h1_tags = soup.find_all("h1")
        if not h1_tags:
            violations.append(Violation(
                id="html-validator-missing-h1",
                rule_id="missing-h1",
                wcag_criteria=["1.3.1"],
                wcag_level=WCAGLevel.A,
                impact=Impact.MODERATE,
                description="Page should have an <h1> heading",
                help_text="Add an <h1> element as the main heading of the page.",
                detected_by=["html_validator"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion="Add an <h1> element as the primary heading"
                )],
                tags=["headings", "wcag1.3.1"]
            ))
        elif len(h1_tags) > 1:
            for h1 in h1_tags[1:]:
                violations.append(Violation(
                    id="html-validator-multiple-h1",
                    rule_id="multiple-h1",
                    wcag_criteria=["1.3.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description="Page should have only one <h1> heading",
                    help_text="Use only one <h1> element per page.",
                    detected_by=["html_validator"],
                    instances=[ViolationInstance(
                        html=str(h1)[:200],
                        selector=self._get_selector(h1),
                        fix_suggestion="Consider changing this to <h2> or another appropriate level"
                    )],
                    tags=["headings", "wcag1.3.1"]
                ))

        # Check for skipped heading levels
        if headings:
            levels = []
            for h in headings:
                level = int(h.name[1])
                levels.append((level, h))

            for i in range(1, len(levels)):
                prev_level = levels[i - 1][0]
                curr_level = levels[i][0]

                if curr_level > prev_level + 1:
                    h = levels[i][1]
                    violations.append(Violation(
                        id=f"html-validator-skipped-heading-{i}",
                        rule_id="heading-order",
                        wcag_criteria=["1.3.1"],
                        wcag_level=WCAGLevel.A,
                        impact=Impact.MODERATE,
                        description=f"Heading levels should only increase by one (skipped from h{prev_level} to h{curr_level})",
                        help_text="Ensure heading levels don't skip (e.g., don't jump from <h2> to <h4>).",
                        detected_by=["html_validator"],
                        instances=[ViolationInstance(
                            html=str(h)[:200],
                            selector=self._get_selector(h),
                            fix_suggestion=f"Change to <h{prev_level + 1}> or restructure heading hierarchy"
                        )],
                        tags=["headings", "wcag1.3.1"]
                    ))

        return violations

    def _check_images_alt(self, soup: BeautifulSoup) -> list[Violation]:
        """Check images for alt attributes."""
        violations = []
        images = soup.find_all("img")

        for img in images:
            if not img.has_attr("alt"):
                violations.append(Violation(
                    id=f"html-validator-img-no-alt-{hash(str(img)) % 10000}",
                    rule_id="image-alt",
                    wcag_criteria=["1.1.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.CRITICAL,
                    description="Images must have an alt attribute",
                    help_text="Add an alt attribute to describe the image content, or use alt='' for decorative images.",
                    detected_by=["html_validator"],
                    instances=[ViolationInstance(
                        html=str(img)[:200],
                        selector=self._get_selector(img),
                        fix_suggestion="Add alt='description' or alt='' for decorative images"
                    )],
                    tags=["images", "wcag1.1.1"]
                ))

        return violations

    def _check_form_labels(self, soup: BeautifulSoup) -> list[Violation]:
        """Check form inputs for associated labels."""
        violations = []
        inputs = soup.find_all(["input", "select", "textarea"])

        for inp in inputs:
            input_type = inp.get("type", "text")

            # Skip inputs that don't need labels
            if input_type in ["hidden", "submit", "reset", "button", "image"]:
                continue

            input_id = inp.get("id")
            has_label = False

            # Check for associated label
            if input_id:
                label = soup.find("label", {"for": input_id})
                if label:
                    has_label = True

            # Check for wrapping label
            if not has_label:
                parent = inp.parent
                while parent:
                    if parent.name == "label":
                        has_label = True
                        break
                    parent = parent.parent

            # Check for aria-label or aria-labelledby
            if inp.get("aria-label") or inp.get("aria-labelledby"):
                has_label = True

            if not has_label:
                violations.append(Violation(
                    id=f"html-validator-input-no-label-{hash(str(inp)) % 10000}",
                    rule_id="label",
                    wcag_criteria=["1.3.1", "4.1.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.CRITICAL,
                    description="Form inputs must have associated labels",
                    help_text="Add a <label> element with a 'for' attribute matching the input's id.",
                    detected_by=["html_validator"],
                    instances=[ViolationInstance(
                        html=str(inp)[:200],
                        selector=self._get_selector(inp),
                        fix_suggestion="Add <label for='input-id'>Label text</label> or aria-label attribute"
                    )],
                    tags=["forms", "wcag1.3.1", "wcag4.1.2"]
                ))

        return violations

    def _check_links(self, soup: BeautifulSoup) -> list[Violation]:
        """Check links for accessibility."""
        violations = []
        links = soup.find_all("a")

        for link in links:
            # Check for empty links
            link_text = link.get_text(strip=True)
            aria_label = link.get("aria-label", "")

            if not link_text and not aria_label and not link.find("img"):
                violations.append(Violation(
                    id=f"html-validator-empty-link-{hash(str(link)) % 10000}",
                    rule_id="link-name",
                    wcag_criteria=["2.4.4", "4.1.2"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description="Links must have discernible text",
                    help_text="Add text content, aria-label, or an image with alt text to the link.",
                    detected_by=["html_validator"],
                    instances=[ViolationInstance(
                        html=str(link)[:200],
                        selector=self._get_selector(link),
                        fix_suggestion="Add descriptive text inside the link or use aria-label"
                    )],
                    tags=["links", "wcag2.4.4", "wcag4.1.2"]
                ))

        return violations

    def _check_tables(self, soup: BeautifulSoup) -> list[Violation]:
        """Check tables for accessibility."""
        violations = []
        tables = soup.find_all("table")

        for table in tables:
            # Check for header cells
            th_cells = table.find_all("th")
            if not th_cells:
                violations.append(Violation(
                    id=f"html-validator-table-no-headers-{hash(str(table)) % 10000}",
                    rule_id="th-has-data-cells",
                    wcag_criteria=["1.3.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.SERIOUS,
                    description="Data tables should have header cells",
                    help_text="Use <th> elements for table header cells.",
                    detected_by=["html_validator"],
                    instances=[ViolationInstance(
                        html=str(table)[:200],
                        selector=self._get_selector(table),
                        fix_suggestion="Add <th> elements for column/row headers"
                    )],
                    tags=["tables", "wcag1.3.1"]
                ))

        return violations

    def _check_landmarks(self, soup: BeautifulSoup) -> list[Violation]:
        """Check for proper landmark regions."""
        violations = []

        # Check for main landmark
        main = soup.find("main") or soup.find(attrs={"role": "main"})
        if not main:
            violations.append(Violation(
                id="html-validator-missing-main",
                rule_id="landmark-main",
                wcag_criteria=["1.3.1"],
                wcag_level=WCAGLevel.A,
                impact=Impact.MODERATE,
                description="Page should have a <main> landmark",
                help_text="Add a <main> element to contain the primary content.",
                detected_by=["html_validator"],
                instances=[ViolationInstance(
                    html="",
                    selector="body",
                    fix_suggestion="Wrap main content in <main> element"
                )],
                tags=["landmarks", "wcag1.3.1"]
            ))

        return violations

    def _check_skip_link(self, soup: BeautifulSoup) -> list[Violation]:
        """Check for skip navigation link."""
        violations = []

        # Look for skip link
        skip_link = None
        links = soup.find_all("a", href=True)

        for link in links[:10]:  # Check first 10 links
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()
            if href.startswith("#") and ("skip" in text or "main" in text):
                skip_link = link
                break

        if not skip_link:
            violations.append(Violation(
                id="html-validator-missing-skip-link",
                rule_id="bypass",
                wcag_criteria=["2.4.1"],
                wcag_level=WCAGLevel.A,
                impact=Impact.MODERATE,
                description="Page should have a skip navigation link",
                help_text="Add a 'Skip to main content' link as the first focusable element.",
                detected_by=["html_validator"],
                instances=[ViolationInstance(
                    html="",
                    selector="body > a:first-of-type",
                    fix_suggestion="Add <a href='#main-content'>Skip to main content</a> at the start of the page"
                )],
                tags=["navigation", "wcag2.4.1"]
            ))

        return violations

    def _get_selector(self, element) -> str:
        """Generate a CSS selector for an element."""
        parts = []
        for parent in element.parents:
            if parent.name == "[document]":
                break
            sibling_count = 0
            for sibling in parent.children:
                if sibling.name == element.name:
                    sibling_count += 1
            parts.append(f"{parent.name}")

        parts.reverse()
        parts.append(element.name)

        if element.get("id"):
            return f"#{element.get('id')}"
        elif element.get("class"):
            return f"{element.name}.{'.'.join(element.get('class')[:2])}"

        return " > ".join(parts[-3:])
