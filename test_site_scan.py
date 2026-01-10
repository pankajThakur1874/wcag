"""
Test script to demonstrate site-wide WCAG scanning.

This script shows how to use the built-in site scanner to:
1. Crawl all pages on a website
2. Scan each discovered page with all 14 scanners
3. Generate comprehensive reports with aggregated violations
"""

import asyncio
import json
from src.core import SiteScanner

async def scan_entire_website():
    """Scan an entire website and generate comprehensive report."""

    # Configure the site scanner
    scanner = SiteScanner(
        max_pages=50,        # Maximum number of pages to scan
        max_depth=3,         # How deep to crawl (0 = only homepage)
        tools=None,          # None = use all 14 scanners
        concurrent_scans=3   # Scan 3 pages at a time for speed
    )

    # Optional: Set up progress callback to monitor progress
    def on_progress(phase, current, total, message):
        print(f"[{phase.upper()}] {current}/{total}: {message}")

    scanner.set_progress_callback(on_progress)

    # Run the scan
    print("Starting site-wide scan...")
    result = await scanner.scan_site("https://www.britishairways.com/")

    # Print summary
    print("\n" + "="*80)
    print("SCAN COMPLETE")
    print("="*80)
    print(f"Website: {result.base_url}")
    print(f"Duration: {result.duration_seconds}s")
    print(f"Pages discovered: {result.pages_discovered}")
    print(f"Pages scanned: {result.pages_scanned}")
    print(f"Pages failed: {result.pages_failed}")
    print(f"Overall score: {result.overall_score}%")
    print(f"Total rules checked: {result.total_rules_checked}")
    print(f"Total rules passed: {result.total_rules_passed}")
    print(f"Total rules failed: {result.total_rules_failed}")
    print(f"Unique violations: {len(result.unique_violations)}")
    print(f"Total violation instances: {len(result.all_violations)}")

    # Show violations by impact
    print("\nViolations by Impact:")
    for impact, count in result.summary["by_impact"].items():
        print(f"  {impact.capitalize()}: {count}")

    # Show worst pages
    print("\nPages with Most Issues:")
    for page in result.summary["worst_pages"]:
        print(f"  {page['url']}: {page['violations']} violations (Score: {page['score']}%)")

    # Show best pages
    print("\nBest Performing Pages:")
    for page in result.summary["best_pages"]:
        print(f"  {page['url']}: {page['violations']} violations (Score: {page['score']}%)")

    # Save detailed JSON report
    with open("site_wide_report.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)

    print(f"\nDetailed report saved to: site_wide_report.json")

    return result

if __name__ == "__main__":
    asyncio.run(scan_entire_website())
