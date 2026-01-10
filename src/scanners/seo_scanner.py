"""SEO and meta accessibility scanner implementation."""

from typing import Optional
from bs4 import BeautifulSoup

from src.scanners.base import BaseScanner
from src.models import Violation, ViolationInstance, Impact, WCAGLevel
from src.utils.browser import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SEOAccessibilityScanner(BaseScanner):
    """Scanner for SEO and meta tag accessibility issues."""

    name = "seo"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check SEO and meta accessibility.

        Args:
            url: URL to scan
            html_content: Pre-fetched HTML content

        Returns:
            List of violations
        """
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

        soup = BeautifulSoup(html_content, "lxml")
        violations = []

        # This scanner checks 8 rules
        self._rules_checked = 8

        # Track which checks fail
        checks = [
            ("viewport", self._check_viewport(soup)),
            ("meta_description", self._check_meta_description(soup)),
            ("canonical", self._check_canonical(soup)),
            ("opengraph", self._check_opengraph(soup)),
            ("twitter_cards", self._check_twitter_cards(soup)),
            ("structured_data", self._check_structured_data(soup, html_content)),
            ("robots", self._check_robots(soup)),
            ("language", self._check_language(soup)),
        ]

        failed_rules = 0
        for check_name, check_violations in checks:
            if check_violations:
                failed_rules += 1
            violations.extend(check_violations)

        self._rules_failed = failed_rules
        self._rules_passed = self._rules_checked - failed_rules

        return violations

    def _check_viewport(self, soup: BeautifulSoup) -> list[Violation]:
        """Check viewport meta tag."""
        violations = []
        viewport = soup.find("meta", attrs={"name": "viewport"})

        if not viewport:
            violations.append(Violation(
                id="seo-missing-viewport",
                rule_id="meta-viewport",
                wcag_criteria=["1.4.4", "1.4.10"],
                wcag_level=WCAGLevel.AA,
                impact=Impact.SERIOUS,
                description="Missing viewport meta tag",
                help_text="Add <meta name='viewport' content='width=device-width, initial-scale=1'>",
                detected_by=["seo"],
                instances=[ViolationInstance(
                    html="<head>...</head>",
                    selector="head",
                    fix_suggestion="Add viewport meta tag for responsive design"
                )],
                tags=["viewport", "wcag1.4.4", "wcag1.4.10"]
            ))
        else:
            content = viewport.get("content", "")

            # Check for user-scalable=no
            if "user-scalable=no" in content.lower() or "user-scalable=0" in content:
                violations.append(Violation(
                    id="seo-viewport-no-scale",
                    rule_id="meta-viewport-scale",
                    wcag_criteria=["1.4.4"],
                    wcag_level=WCAGLevel.AA,
                    impact=Impact.CRITICAL,
                    description="Viewport disables user scaling (user-scalable=no)",
                    help_text="Remove user-scalable=no to allow users to zoom",
                    detected_by=["seo"],
                    instances=[ViolationInstance(
                        html=str(viewport),
                        selector="meta[name='viewport']",
                        fix_suggestion="Remove user-scalable=no from viewport"
                    )],
                    tags=["viewport", "wcag1.4.4"]
                ))

            # Check for maximum-scale < 2
            if "maximum-scale=" in content.lower():
                try:
                    import re
                    match = re.search(r'maximum-scale=(\d+\.?\d*)', content.lower())
                    if match:
                        max_scale = float(match.group(1))
                        if max_scale < 2:
                            violations.append(Violation(
                                id="seo-viewport-max-scale",
                                rule_id="meta-viewport-scale",
                                wcag_criteria=["1.4.4"],
                                wcag_level=WCAGLevel.AA,
                                impact=Impact.SERIOUS,
                                description=f"Viewport restricts zoom (maximum-scale={max_scale})",
                                help_text="Set maximum-scale to at least 2 or remove it",
                                detected_by=["seo"],
                                instances=[ViolationInstance(
                                    html=str(viewport),
                                    selector="meta[name='viewport']",
                                    fix_suggestion="Increase or remove maximum-scale"
                                )],
                                tags=["viewport", "wcag1.4.4"]
                            ))
                except:
                    pass

        return violations

    def _check_meta_description(self, soup: BeautifulSoup) -> list[Violation]:
        """Check meta description."""
        violations = []
        description = soup.find("meta", attrs={"name": "description"})

        if not description:
            violations.append(Violation(
                id="seo-missing-description",
                rule_id="meta-description",
                wcag_criteria=[],
                wcag_level=None,
                impact=Impact.MINOR,
                description="Missing meta description",
                help_text="Add <meta name='description' content='...'>",
                detected_by=["seo"],
                instances=[ViolationInstance(
                    html="<head>...</head>",
                    selector="head",
                    fix_suggestion="Add meta description for search engines and screen readers"
                )],
                tags=["seo", "meta"]
            ))
        else:
            content = description.get("content", "")
            if len(content) < 50:
                violations.append(Violation(
                    id="seo-short-description",
                    rule_id="meta-description-length",
                    wcag_criteria=[],
                    wcag_level=None,
                    impact=Impact.MINOR,
                    description=f"Meta description too short ({len(content)} chars)",
                    help_text="Meta description should be 50-160 characters",
                    detected_by=["seo"],
                    instances=[ViolationInstance(
                        html=str(description),
                        selector="meta[name='description']",
                        fix_suggestion="Expand meta description to 50-160 characters"
                    )],
                    tags=["seo", "meta"]
                ))

        return violations

    def _check_canonical(self, soup: BeautifulSoup) -> list[Violation]:
        """Check canonical URL."""
        violations = []
        canonical = soup.find("link", attrs={"rel": "canonical"})

        if not canonical:
            violations.append(Violation(
                id="seo-missing-canonical",
                rule_id="canonical-url",
                wcag_criteria=[],
                wcag_level=None,
                impact=Impact.MINOR,
                description="Missing canonical URL",
                help_text="Add <link rel='canonical' href='...'>",
                detected_by=["seo"],
                instances=[ViolationInstance(
                    html="<head>...</head>",
                    selector="head",
                    fix_suggestion="Add canonical link to prevent duplicate content issues"
                )],
                tags=["seo", "canonical"]
            ))

        return violations

    def _check_opengraph(self, soup: BeautifulSoup) -> list[Violation]:
        """Check Open Graph meta tags."""
        violations = []

        og_tags = {
            "og:title": soup.find("meta", attrs={"property": "og:title"}),
            "og:description": soup.find("meta", attrs={"property": "og:description"}),
            "og:image": soup.find("meta", attrs={"property": "og:image"}),
        }

        missing = [tag for tag, el in og_tags.items() if not el]

        if missing:
            violations.append(Violation(
                id="seo-missing-og",
                rule_id="opengraph",
                wcag_criteria=[],
                wcag_level=None,
                impact=Impact.MINOR,
                description=f"Missing Open Graph tags: {', '.join(missing)}",
                help_text="Add Open Graph meta tags for social sharing",
                detected_by=["seo"],
                instances=[ViolationInstance(
                    html="<head>...</head>",
                    selector="head",
                    fix_suggestion=f"Add {', '.join(missing)} meta tags"
                )],
                tags=["seo", "opengraph"]
            ))

        # Check og:image alt text
        og_image = og_tags.get("og:image")
        if og_image:
            og_image_alt = soup.find("meta", attrs={"property": "og:image:alt"})
            if not og_image_alt:
                violations.append(Violation(
                    id="seo-missing-og-image-alt",
                    rule_id="opengraph-image-alt",
                    wcag_criteria=["1.1.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description="Open Graph image missing alt text",
                    help_text="Add <meta property='og:image:alt' content='...'>",
                    detected_by=["seo"],
                    instances=[ViolationInstance(
                        html=str(og_image),
                        selector="meta[property='og:image']",
                        fix_suggestion="Add og:image:alt meta tag for image description"
                    )],
                    tags=["seo", "opengraph", "wcag1.1.1"]
                ))

        return violations

    def _check_twitter_cards(self, soup: BeautifulSoup) -> list[Violation]:
        """Check Twitter Card meta tags."""
        violations = []

        twitter_card = soup.find("meta", attrs={"name": "twitter:card"})

        if not twitter_card:
            violations.append(Violation(
                id="seo-missing-twitter-card",
                rule_id="twitter-card",
                wcag_criteria=[],
                wcag_level=None,
                impact=Impact.MINOR,
                description="Missing Twitter Card meta tag",
                help_text="Add <meta name='twitter:card' content='summary_large_image'>",
                detected_by=["seo"],
                instances=[ViolationInstance(
                    html="<head>...</head>",
                    selector="head",
                    fix_suggestion="Add Twitter Card meta tags for social sharing"
                )],
                tags=["seo", "twitter"]
            ))

        return violations

    def _check_structured_data(self, soup: BeautifulSoup, html: str) -> list[Violation]:
        """Check for structured data."""
        violations = []

        # Check for JSON-LD
        json_ld = soup.find("script", attrs={"type": "application/ld+json"})

        # Check for microdata
        has_microdata = bool(soup.find(attrs={"itemscope": True}))

        if not json_ld and not has_microdata:
            violations.append(Violation(
                id="seo-missing-structured-data",
                rule_id="structured-data",
                wcag_criteria=[],
                wcag_level=None,
                impact=Impact.MINOR,
                description="No structured data found (JSON-LD or microdata)",
                help_text="Add structured data for better search engine understanding",
                detected_by=["seo"],
                instances=[ViolationInstance(
                    html="",
                    selector="head",
                    fix_suggestion="Add JSON-LD structured data (Organization, WebPage, etc.)"
                )],
                tags=["seo", "structured-data"]
            ))

        return violations

    def _check_robots(self, soup: BeautifulSoup) -> list[Violation]:
        """Check robots meta tag."""
        violations = []

        robots = soup.find("meta", attrs={"name": "robots"})

        if robots:
            content = robots.get("content", "").lower()
            if "noindex" in content:
                violations.append(Violation(
                    id="seo-noindex",
                    rule_id="robots-noindex",
                    wcag_criteria=[],
                    wcag_level=None,
                    impact=Impact.MINOR,
                    description="Page is set to noindex",
                    help_text="This page will not appear in search results",
                    detected_by=["seo"],
                    instances=[ViolationInstance(
                        html=str(robots),
                        selector="meta[name='robots']",
                        fix_suggestion="Remove noindex if this page should be indexed"
                    )],
                    tags=["seo", "robots"]
                ))

        return violations

    def _check_language(self, soup: BeautifulSoup) -> list[Violation]:
        """Check language attributes."""
        violations = []

        html_tag = soup.find("html")

        if html_tag:
            lang = html_tag.get("lang", "")
            xml_lang = html_tag.get("xml:lang", "")

            # Check if lang and xml:lang conflict
            if lang and xml_lang and lang.lower() != xml_lang.lower():
                violations.append(Violation(
                    id="seo-lang-mismatch",
                    rule_id="html-lang-mismatch",
                    wcag_criteria=["3.1.1"],
                    wcag_level=WCAGLevel.A,
                    impact=Impact.MODERATE,
                    description=f"lang ('{lang}') and xml:lang ('{xml_lang}') attributes don't match",
                    help_text="Ensure lang and xml:lang attributes have the same value",
                    detected_by=["seo"],
                    instances=[ViolationInstance(
                        html=str(html_tag)[:200],
                        selector="html",
                        fix_suggestion="Make lang and xml:lang attributes consistent"
                    )],
                    tags=["language", "wcag3.1.1"]
                ))

        return violations
