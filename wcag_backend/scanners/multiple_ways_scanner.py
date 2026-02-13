"""Multiple Ways Scanner - WCAG 2.4.5 (Level AA)

Checks if there are multiple ways to locate pages within a set of web pages
(e.g., search, site map, table of contents, navigation menu).
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import Page

from wcag_backend.scanners.base import BaseScanner
from wcag_backend.models_src import Violation, ViolationInstance, Impact, WCAGLevel
from wcag_backend.utils_src.browser import BrowserManager
from wcag_backend.utils.logger import get_logger

logger = get_logger(__name__)


class MultipleWaysScanner(BaseScanner):
    """Scanner for multiple navigation mechanisms."""

    name = "multiple-ways"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check for multiple ways to find content.

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
                return await self._check_multiple_ways(page)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_multiple_ways(self, page: Page) -> list[Violation]:
        """Run multiple ways checks."""
        violations = []

        # This scanner checks for 5 different navigation mechanisms
        self._rules_checked = 5

        mechanisms = await page.evaluate("""
            () => {
                const found = {
                    search: false,
                    sitemap: false,
                    navigation: false,
                    breadcrumbs: false,
                    tableOfContents: false
                };

                const details = {
                    searchElements: [],
                    sitemapLinks: [],
                    navElements: [],
                    breadcrumbElements: [],
                    tocElements: []
                };

                // Helper function
                function getSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        return el.tagName.toLowerCase() + '.' + classes[0];
                    }
                    return el.tagName.toLowerCase();
                }

                // 1. Check for search functionality
                const searchInputs = document.querySelectorAll(
                    'input[type="search"], input[name*="search"], input[id*="search"], ' +
                    'input[placeholder*="search"], input[aria-label*="search"]'
                );

                const searchForms = document.querySelectorAll(
                    'form[role="search"], form[action*="search"], form[class*="search"]'
                );

                const searchButtons = document.querySelectorAll(
                    'button[type="submit"][aria-label*="search"], ' +
                    'button[class*="search"], a[class*="search-btn"]'
                );

                if (searchInputs.length > 0 || searchForms.length > 0 || searchButtons.length > 0) {
                    found.search = true;
                    details.searchElements = Array.from(searchInputs).map(el => ({
                        selector: getSelector(el),
                        type: el.type,
                        html: el.outerHTML.substring(0, 200)
                    }));
                }

                // 2. Check for sitemap links
                const sitemapLinks = Array.from(document.querySelectorAll('a')).filter(link => {
                    const href = link.href.toLowerCase();
                    const text = link.textContent.toLowerCase();
                    return href.includes('sitemap') ||
                           text.includes('sitemap') ||
                           text.includes('site map') ||
                           href.endsWith('sitemap.xml') ||
                           href.endsWith('sitemap.html');
                });

                if (sitemapLinks.length > 0) {
                    found.sitemap = true;
                    details.sitemapLinks = sitemapLinks.map(el => ({
                        selector: getSelector(el),
                        href: el.href,
                        text: el.textContent.trim(),
                        html: el.outerHTML.substring(0, 200)
                    }));
                }

                // 3. Check for navigation menus
                const navElements = document.querySelectorAll(
                    'nav, [role="navigation"], header nav, .navbar, .nav-menu, ' +
                    '.navigation, #nav, #navigation, .menu, [class*="nav"]'
                );

                // Count substantial navigation (more than 3 links)
                let substantialNav = 0;
                for (const nav of navElements) {
                    const links = nav.querySelectorAll('a');
                    if (links.length >= 3) {
                        substantialNav++;
                        details.navElements.push({
                            selector: getSelector(nav),
                            linkCount: links.length,
                            html: nav.outerHTML.substring(0, 200)
                        });
                    }
                }

                if (substantialNav > 0) {
                    found.navigation = true;
                }

                // 4. Check for breadcrumbs
                const breadcrumbElements = document.querySelectorAll(
                    '[aria-label*="breadcrumb"], [class*="breadcrumb"], ' +
                    'nav ol, nav ul, [role="navigation"] ol'
                );

                for (const elem of breadcrumbElements) {
                    // Check if it looks like breadcrumbs (has separators or ordered structure)
                    const text = elem.textContent;
                    const hasSeparators = text.includes('>') || text.includes('/') ||
                                         text.includes('»') || text.includes('›');
                    const listItems = elem.querySelectorAll('li');

                    if (hasSeparators || (listItems.length >= 2 && listItems.length <= 10)) {
                        found.breadcrumbs = true;
                        details.breadcrumbElements.push({
                            selector: getSelector(elem),
                            itemCount: listItems.length,
                            html: elem.outerHTML.substring(0, 200)
                        });
                        break;
                    }
                }

                // 5. Check for table of contents (for long pages)
                const tocElements = document.querySelectorAll(
                    '[class*="toc"], [class*="table-of-contents"], ' +
                    '[id*="toc"], [aria-label*="table of contents"]'
                );

                const tocLinks = document.querySelectorAll('a[href^="#"]');
                const anchorNavigation = tocLinks.length >= 3; // At least 3 anchor links

                if (tocElements.length > 0 || anchorNavigation) {
                    found.tableOfContents = true;
                    details.tocElements = Array.from(tocElements).map(el => ({
                        selector: getSelector(el),
                        html: el.outerHTML.substring(0, 200)
                    }));

                    if (anchorNavigation) {
                        details.tocElements.push({
                            type: 'anchor-links',
                            count: tocLinks.length
                        });
                    }
                }

                return {
                    found,
                    details,
                    count: Object.values(found).filter(v => v).length
                };
            }
        """)

        logger.info(f"Found {mechanisms['count']} navigation mechanisms")

        found = mechanisms["found"]
        details = mechanisms["details"]

        # WCAG 2.4.5 requires at least 2 different ways
        # Exception: If page is result of a process, only 1 way is needed
        mechanisms_count = mechanisms["count"]

        if mechanisms_count < 2:
            # Determine what's missing
            missing = []
            if not found["search"]:
                missing.append("search functionality")
            if not found["sitemap"]:
                missing.append("sitemap")
            if not found["navigation"]:
                missing.append("navigation menu")
            if not found["breadcrumbs"]:
                missing.append("breadcrumbs")
            if not found["tableOfContents"]:
                missing.append("table of contents (for long pages)")

            violation = Violation(
                id=f"multiple-ways-insufficient",
                rule_id="multiple-ways",
                wcag_criteria=["2.4.5"],
                wcag_level=WCAGLevel.AA,
                impact=Impact.MODERATE if mechanisms_count == 1 else Impact.SERIOUS,
                description=f"Only {mechanisms_count} way(s) found to locate content. WCAG 2.4.5 requires at least 2 ways.",
                help_text=f"Add one or more of the following: {', '.join(missing[:3])}. "
                         f"Found: {', '.join([k for k, v in found.items() if v]) or 'none'}",
                help_url="https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways.html",
                detected_by=["multiple-ways"],
                instances=[ViolationInstance(
                    html="<body>",
                    selector="body",
                    fix_suggestion=f"Implement at least one more navigation mechanism. "
                                  f"Suggested: {missing[0] if missing else 'search or sitemap'}"
                )],
                tags=["navigation", "wcag245", "level-aa"]
            )
            violations.append(violation)
            self._rules_failed = 1
        else:
            # Check quality of mechanisms
            quality_issues = []

            # Check search functionality quality
            if found["search"] and len(details["searchElements"]) > 0:
                search_elem = details["searchElements"][0]
                if "aria-label" not in search_elem["html"].lower():
                    quality_issues.append({
                        "type": "search-no-label",
                        "element": search_elem,
                        "message": "Search input should have aria-label for screen readers"
                    })

            # Check navigation quality
            if found["navigation"]:
                if len(details["navElements"]) > 0:
                    nav_elem = details["navElements"][0]
                    if nav_elem["linkCount"] < 3:
                        quality_issues.append({
                            "type": "nav-too-few-links",
                            "element": nav_elem,
                            "message": "Navigation menu has very few links, may not be comprehensive"
                        })

            # Report quality issues as minor violations
            for issue in quality_issues:
                violation = Violation(
                    id=f"multiple-ways-quality-{issue['type']}",
                    rule_id="multiple-ways-quality",
                    wcag_criteria=["2.4.5"],
                    wcag_level=WCAGLevel.AA,
                    impact=Impact.MINOR,
                    description=issue["message"],
                    help_text="While multiple ways exist, improving their quality enhances usability",
                    help_url="https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways.html",
                    detected_by=["multiple-ways"],
                    instances=[ViolationInstance(
                        html=issue["element"].get("html", ""),
                        selector=issue["element"].get("selector", ""),
                        fix_suggestion=issue["message"]
                    )],
                    tags=["navigation", "wcag245", "level-aa", "quality"]
                )
                violations.append(violation)

            self._rules_failed = len(quality_issues)

        self._rules_passed = self._rules_checked - self._rules_failed

        return violations
