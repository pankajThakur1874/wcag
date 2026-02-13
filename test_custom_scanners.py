#!/usr/bin/env python3
"""Test script for custom WCAG 2.2 scanners."""

import asyncio
import sys
from src.scanners import get_scanner
from src.utils.browser import BrowserManager


async def test_custom_scanners(url: str):
    """Test all custom scanners on a URL."""
    print(f"\n🔍 Testing Custom WCAG 2.2 Scanners")
    print(f"URL: {url}\n")

    browser_manager = BrowserManager()
    await browser_manager.start()

    custom_scanners = [
        ("color_only", "Use of Color (1.4.1)"),
        ("hover_content", "Content on Hover/Focus (1.4.13)"),
        ("multiple_ways", "Multiple Ways (2.4.5)"),
        ("pointer_gestures", "Pointer Gestures (2.5.1, 2.5.2, 2.5.7)"),
        ("consistent_navigation", "Consistent Navigation (3.2.3, 3.2.6)"),
        ("character_shortcuts", "Character Key Shortcuts (2.1.4)"),
        ("focus_obscured", "Focus Not Obscured (2.4.11)"),
        ("media_accessibility", "Media Accessibility (1.2.1, 1.2.2)")
    ]

    results = {}
    total_violations = 0

    for scanner_name, description in custom_scanners:
        print(f"{'='*70}")
        print(f"🔎 {description}")
        print(f"   Scanner: {scanner_name}")
        print('='*70)

        try:
            scanner_class = get_scanner(scanner_name)
            scanner = scanner_class(browser_manager)

            violations, status = await scanner.run(url)

            results[scanner_name] = {
                "violations": len(violations),
                "status": status.status,
                "rules_checked": status.rules_checked,
                "rules_passed": status.rules_passed,
                "rules_failed": status.rules_failed,
                "score": status.score
            }

            total_violations += len(violations)

            # Display results
            print(f"✓ Status: {status.status}")
            print(f"  Rules Checked: {status.rules_checked}")
            print(f"  Rules Passed: {status.rules_passed}")
            print(f"  Rules Failed: {status.rules_failed}")
            print(f"  Score: {status.score}%")
            print(f"  Violations: {len(violations)}")

            if violations:
                print(f"\n  📋 Top Violations:")
                for i, v in enumerate(violations[:3], 1):
                    print(f"\n  {i}. WCAG {', '.join(v.wcag_criteria)} - {v.impact.value.upper()}")
                    print(f"     {v.description}")
                    print(f"     💡 Fix: {v.help_text[:120]}...")

                if len(violations) > 3:
                    print(f"\n  ... and {len(violations) - 3} more violations")
            else:
                print(f"  ✅ No violations found!")

            print()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[scanner_name] = {"error": str(e)}

    await browser_manager.stop()

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY")
    print('='*70)

    print(f"\nScanner Results:")
    for name, data in results.items():
        if "error" in data:
            print(f"  ❌ {name}: Error - {data['error']}")
        else:
            status_icon = "✅" if data['violations'] == 0 else "⚠️"
            print(f"  {status_icon} {name}: {data['violations']} violations " +
                  f"({data['score']}% score, {data['status']})")

    print(f"\nOverall:")
    print(f"  Total Violations: {total_violations}")
    print(f"  Scanners Run: {len([r for r in results.values() if 'error' not in r])}/{len(custom_scanners)}")

    if total_violations == 0:
        print(f"\n🎉 Excellent! No violations found in custom scanners.")
    elif total_violations < 10:
        print(f"\n✅ Good! Few violations found. Review and fix.")
    elif total_violations < 25:
        print(f"\n⚠️  Moderate issues found. Prioritize critical/serious violations.")
    else:
        print(f"\n❌ Many violations found. Significant accessibility work needed.")

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_custom_scanners.py <url>")
        print("Example: python test_custom_scanners.py https://example.com")
        sys.exit(1)

    url = sys.argv[1]
    asyncio.run(test_custom_scanners(url))
