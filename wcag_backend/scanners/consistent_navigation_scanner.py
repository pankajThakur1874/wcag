"""Consistent Navigation Scanner - WCAG 3.2.3, 3.2.6 (Level AA/A)

Checks if navigation mechanisms are repeated in the same relative order across
multiple pages and if help mechanisms appear in consistent locations.
"""

from typing import Optional, List, Dict, Any, Tuple
from playwright.async_api import Page
from urllib.parse import urljoin, urlparse
import hashlib

from wcag_backend.scanners.base import BaseScanner
from wcag_backend.models_src import Violation, ViolationInstance, Impact, WCAGLevel
from wcag_backend.utils_src.browser import BrowserManager
from wcag_backend.utils.logger import get_logger

logger = get_logger(__name__)


class ConsistentNavigationScanner(BaseScanner):
    """Scanner for consistent navigation across pages."""

    name = "consistent-navigation"
    version = "1.0.0"

    def __init__(self, browser_manager: Optional[BrowserManager] = None, max_pages: int = 5):
        super().__init__()
        self._browser_manager = browser_manager
        self._owns_browser = browser_manager is None
        self.max_pages = max_pages  # Limit pages to scan for performance

    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Check navigation consistency across pages.

        Args:
            url: URL to scan
            html_content: Ignored, needs live pages

        Returns:
            List of violations
        """
        if self._browser_manager is None:
            self._browser_manager = BrowserManager()
            await self._browser_manager.start()

        try:
            async with self._browser_manager.get_page(url) as page:
                return await self._check_consistent_navigation(page, url)
        finally:
            if self._owns_browser and self._browser_manager:
                await self._browser_manager.stop()
                self._browser_manager = None

    async def _check_consistent_navigation(self, page: Page, start_url: str) -> list[Violation]:
        """Run consistent navigation checks across multiple pages."""
        violations = []

        # This scanner checks 3 rules
        self._rules_checked = 3

        # Extract navigation structure from multiple pages
        pages_data = []

        # Scan the starting page
        start_data = await self._extract_page_structure(page)
        start_data["url"] = start_url
        pages_data.append(start_data)

        # Find internal links to scan additional pages
        internal_links = await self._find_internal_links(page, start_url)
        logger.info(f"Found {len(internal_links)} internal links")

        # Scan up to max_pages additional pages
        scanned_count = 1
        for link_url in internal_links[:self.max_pages - 1]:
            try:
                await page.goto(link_url, wait_until="domcontentloaded", timeout=10000)
                page_data = await self._extract_page_structure(page)
                page_data["url"] = link_url
                pages_data.append(page_data)
                scanned_count += 1
                logger.info(f"Scanned page {scanned_count}/{min(self.max_pages, len(internal_links) + 1)}: {link_url}")
            except Exception as e:
                logger.debug(f"Error scanning {link_url}: {e}")
                continue

        if len(pages_data) < 2:
            logger.warning("Could not scan multiple pages - consistency check requires at least 2 pages")
            self._rules_checked = 0
            return violations

        # Analyze consistency
        issues = self._analyze_consistency(pages_data)

        # Convert issues to violations
        rule_types_failed = set()
        for issue in issues:
            violation = self._create_violation(issue, pages_data)
            if violation:
                violations.append(violation)
                rule_types_failed.add(issue.get("wcag"))

        # Update rules failed count
        self._rules_failed = len(rule_types_failed)
        self._rules_passed = self._rules_checked - self._rules_failed

        return violations

    async def _find_internal_links(self, page: Page, base_url: str) -> List[str]:
        """Find internal links on the current page."""
        base_domain = urlparse(base_url).netloc

        links = await page.evaluate("""
            (baseDomain) => {
                const links = [];
                const anchors = document.querySelectorAll('a[href]');

                for (const anchor of anchors) {
                    try {
                        const url = new URL(anchor.href);

                        // Only include same-domain links
                        if (url.hostname === baseDomain) {
                            // Exclude anchors, duplicates, and common non-content pages
                            if (!url.hash &&
                                !url.pathname.match(/\\.(pdf|jpg|png|gif|zip|doc)$/i) &&
                                !url.pathname.match(/\\/search|\\/login|\\/logout|\\/cart/)) {
                                links.push(url.href);
                            }
                        }
                    } catch (e) {
                        // Invalid URL
                    }
                }

                // Return unique links
                return [...new Set(links)];
            }
        """, base_domain)

        return links

    async def _extract_page_structure(self, page: Page) -> Dict[str, Any]:
        """Extract navigation structure from a page."""
        structure = await page.evaluate("""
            () => {
                const data = {
                    navigation: [],
                    help: [],
                    search: null,
                    breadcrumbs: null
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

                // Extract navigation links and their order
                const navElements = document.querySelectorAll(
                    'nav, [role="navigation"], header nav, .navbar, #nav'
                );

                for (const nav of navElements) {
                    const links = nav.querySelectorAll('a');
                    const navData = {
                        selector: getSelector(nav),
                        position: {
                            top: nav.getBoundingClientRect().top,
                            left: nav.getBoundingClientRect().left
                        },
                        links: []
                    };

                    for (const link of links) {
                        navData.links.push({
                            text: link.textContent.trim(),
                            href: link.href,
                            order: Array.from(links).indexOf(link)
                        });
                    }

                    if (navData.links.length > 0) {
                        data.navigation.push(navData);
                    }
                }

                // Find help mechanisms
                const helpPatterns = [
                    'a[href*="help"]',
                    'a[href*="support"]',
                    'a[href*="contact"]',
                    'a[href*="faq"]',
                    '[aria-label*="help"]',
                    '[class*="help"]'
                ];

                for (const pattern of helpPatterns) {
                    const elements = document.querySelectorAll(pattern);
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        const text = el.textContent.trim().toLowerCase();

                        if (text.includes('help') || text.includes('support') ||
                            text.includes('contact') || text.includes('faq')) {
                            data.help.push({
                                selector: getSelector(el),
                                text: el.textContent.trim(),
                                position: {
                                    top: rect.top,
                                    left: rect.left
                                },
                                href: el.href || null
                            });
                        }
                    }
                }

                // Find search
                const searchInput = document.querySelector(
                    'input[type="search"], input[name*="search"], [role="search"] input'
                );

                if (searchInput) {
                    const rect = searchInput.getBoundingClientRect();
                    data.search = {
                        selector: getSelector(searchInput),
                        position: {
                            top: rect.top,
                            left: rect.left
                        }
                    };
                }

                // Find breadcrumbs
                const breadcrumb = document.querySelector('[aria-label*="breadcrumb"], .breadcrumb');
                if (breadcrumb) {
                    const rect = breadcrumb.getBoundingClientRect();
                    data.breadcrumbs = {
                        selector: getSelector(breadcrumb),
                        position: {
                            top: rect.top,
                            left: rect.left
                        }
                    };
                }

                return data;
            }
        """)

        return structure

    def _analyze_consistency(self, pages_data: List[Dict]) -> List[Dict]:
        """Analyze consistency across pages."""
        issues = []

        # Check navigation consistency (3.2.3)
        nav_links_by_page = []
        for page_data in pages_data:
            for nav in page_data.get("navigation", []):
                # Extract link texts in order
                link_texts = [link["text"] for link in nav["links"]]
                nav_links_by_page.append({
                    "url": page_data["url"],
                    "links": link_texts,
                    "selector": nav["selector"]
                })

        # Compare navigation order across pages
        if len(nav_links_by_page) >= 2:
            # Find common navigation links
            common_links = set(nav_links_by_page[0]["links"])
            for nav_data in nav_links_by_page[1:]:
                common_links &= set(nav_data["links"])

            # Check if common links appear in same order
            inconsistencies = []
            for link_text in common_links:
                positions = []
                for nav_data in nav_links_by_page:
                    if link_text in nav_data["links"]:
                        positions.append({
                            "url": nav_data["url"],
                            "position": nav_data["links"].index(link_text)
                        })

                # Check if positions are consistent (allowing for items before/after)
                if len(positions) >= 2:
                    # Get relative positions compared to other common links
                    for i in range(len(positions) - 1):
                        if abs(positions[i]["position"] - positions[i+1]["position"]) > 2:
                            inconsistencies.append({
                                "link": link_text,
                                "positions": positions
                            })
                            break

            if inconsistencies:
                issues.append({
                    "type": "navigation-order-inconsistent",
                    "wcag": "3.2.3",
                    "details": inconsistencies,
                    "pages": [p["url"] for p in pages_data]
                })

        # Check help mechanism consistency (3.2.6)
        help_positions = []
        for page_data in pages_data:
            help_items = page_data.get("help", [])
            if help_items:
                # Get the primary help link (usually first one)
                primary_help = help_items[0]
                help_positions.append({
                    "url": page_data["url"],
                    "position": primary_help["position"],
                    "text": primary_help["text"]
                })

        if len(help_positions) >= 2:
            # Check if help appears in same relative position
            # Allow 50px tolerance for position differences
            tolerance = 50
            reference_pos = help_positions[0]["position"]

            inconsistent_help = []
            for help_data in help_positions[1:]:
                top_diff = abs(help_data["position"]["top"] - reference_pos["top"])
                left_diff = abs(help_data["position"]["left"] - reference_pos["left"])

                if top_diff > tolerance or left_diff > tolerance:
                    inconsistent_help.append(help_data)

            if inconsistent_help:
                issues.append({
                    "type": "help-position-inconsistent",
                    "wcag": "3.2.6",
                    "reference": help_positions[0],
                    "inconsistent": inconsistent_help,
                    "pages": [p["url"] for p in pages_data]
                })

        # Check search position consistency
        search_positions = []
        for page_data in pages_data:
            search = page_data.get("search")
            if search:
                search_positions.append({
                    "url": page_data["url"],
                    "position": search["position"]
                })

        if len(search_positions) >= 2:
            tolerance = 50
            reference_pos = search_positions[0]["position"]

            for search_data in search_positions[1:]:
                top_diff = abs(search_data["position"]["top"] - reference_pos["top"])
                left_diff = abs(search_data["position"]["left"] - reference_pos["left"])

                if top_diff > tolerance or left_diff > tolerance:
                    issues.append({
                        "type": "search-position-inconsistent",
                        "wcag": "3.2.3",
                        "reference": search_positions[0],
                        "inconsistent": search_data,
                        "pages": [p["url"] for p in pages_data]
                    })
                    break

        return issues

    def _create_violation(self, issue: dict, pages_data: List[Dict]) -> Optional[Violation]:
        """Create violation from issue data."""
        issue_type = issue.get("type")

        violation_configs = {
            "navigation-order-inconsistent": {
                "id": "nav-order-inconsistent",
                "rule_id": "consistent-navigation",
                "wcag": ["3.2.3"],
                "level": WCAGLevel.AA,
                "impact": Impact.MODERATE,
                "description": f"Navigation links appear in different order across {len(pages_data)} pages",
                "help": "Keep navigation links in the same relative order on all pages. Links can be added/removed but existing links should maintain order"
            },
            "help-position-inconsistent": {
                "id": "help-position-inconsistent",
                "rule_id": "consistent-help",
                "wcag": ["3.2.6"],
                "level": WCAGLevel.A,
                "impact": Impact.MODERATE,
                "description": "Help mechanism appears in different locations across pages",
                "help": "Place help links/buttons in the same relative position on each page (e.g., always top-right, always in footer)"
            },
            "search-position-inconsistent": {
                "id": "search-position-inconsistent",
                "rule_id": "consistent-navigation",
                "wcag": ["3.2.3"],
                "level": WCAGLevel.AA,
                "impact": Impact.MODERATE,
                "description": "Search functionality appears in different locations across pages",
                "help": "Place search in the same position on all pages for predictable navigation"
            }
        }

        config = violation_configs.get(issue_type)
        if not config:
            return None

        # Build detailed description
        pages_list = "\n".join([f"  - {url}" for url in issue.get("pages", [])[:5]])
        help_text = f"{config['help']}\n\nAffected pages:\n{pages_list}"

        return Violation(
            id=f"{config['id']}-{hashlib.md5(str(issue.get('pages', [])).encode()).hexdigest()[:8]}",
            rule_id=config["rule_id"],
            wcag_criteria=config["wcag"],
            wcag_level=config["level"],
            impact=config["impact"],
            description=config["description"],
            help_text=help_text,
            help_url=f"https://www.w3.org/WAI/WCAG22/Understanding/{config['wcag'][0].replace('.', '')}.html",
            detected_by=["consistent-navigation"],
            instances=[ViolationInstance(
                html="<body>",
                selector="body",
                fix_suggestion=config["help"]
            )],
            tags=["navigation", "consistency", f"wcag{config['wcag'][0].replace('.', '')}"]
        )
