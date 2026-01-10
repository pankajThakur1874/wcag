"""Test site-wide scanning."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.site_scanner import SiteScanner


async def main():
    url = "https://www.ascendons.in/"

    print(f"\n{'='*60}")
    print(f"Site-Wide WCAG Scan: {url}")
    print(f"{'='*60}\n")

    scanner = SiteScanner(
        max_pages=10,  # Limit to 10 pages for testing
        max_depth=2,
        tools=["axe", "html_validator", "contrast", "aria", "forms"],
        concurrent_scans=2
    )

    def progress_callback(phase, current, total, message):
        print(f"[{phase.upper()}] ({current}/{total}) {message}")

    scanner.set_progress_callback(progress_callback)

    result = await scanner.scan_site(url)

    print(f"\n{'='*60}")
    print("SCAN RESULTS")
    print(f"{'='*60}")
    print(f"Status: {result.status.value}")
    print(f"Duration: {result.duration_seconds}s")
    print(f"Pages discovered: {result.pages_discovered}")
    print(f"Pages scanned: {result.pages_scanned}")
    print(f"Pages failed: {result.pages_failed}")
    print(f"\nOverall Score: {result.overall_score}%")
    print(f"Total rules checked: {result.total_rules_checked}")
    print(f"Total rules passed: {result.total_rules_passed}")
    print(f"Total rules failed: {result.total_rules_failed}")

    print(f"\n{'='*60}")
    print("PAGE RESULTS")
    print(f"{'='*60}")
    for page in result.page_results:
        status_icon = "✓" if page.status == "completed" else "✗"
        print(f"{status_icon} {page.url}")
        print(f"   Score: {page.score}% | Violations: {page.violations_count} | Tests: {page.rules_passed}/{page.rules_checked}")

    print(f"\n{'='*60}")
    print("VIOLATIONS SUMMARY")
    print(f"{'='*60}")
    print(f"Total violations (all pages): {len(result.all_violations)}")
    print(f"Unique violations: {len(result.unique_violations)}")

    if result.summary:
        print(f"\nBy Impact:")
        for impact, count in result.summary.get("by_impact", {}).items():
            print(f"  - {impact}: {count}")

        print(f"\nWorst Pages:")
        for page in result.summary.get("worst_pages", [])[:3]:
            print(f"  - {page['url']}: {page['violations']} violations (score: {page['score']}%)")

    print(f"\n{'='*60}")
    print("TOP VIOLATIONS (by frequency)")
    print(f"{'='*60}")
    # Count violations by rule_id
    violation_counts = {}
    for v in result.all_violations:
        if v.rule_id not in violation_counts:
            violation_counts[v.rule_id] = {"count": 0, "desc": v.description, "impact": v.impact.value}
        violation_counts[v.rule_id]["count"] += 1

    sorted_violations = sorted(violation_counts.items(), key=lambda x: x[1]["count"], reverse=True)
    for rule_id, data in sorted_violations[:10]:
        print(f"  [{data['impact'].upper()}] {rule_id}: {data['count']} occurrences")
        print(f"      {data['desc'][:80]}...")


if __name__ == "__main__":
    asyncio.run(main())
