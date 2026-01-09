#!/usr/bin/env python3
"""
Test script for WCAG Accessibility Scanner.

Run this to thoroughly test all scanner functionality:
    python test_scanner.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core import ResultsAggregator, ReportGenerator
from src.scanners import AxeScanner, HTMLValidatorScanner, ContrastChecker

console = Console()


async def test_individual_scanners():
    """Test each scanner individually."""
    console.print(Panel.fit("[bold blue]Testing Individual Scanners[/bold blue]"))

    url = "https://www.ascendons.in/"
    results = {}

    # Test Axe Scanner
    console.print("\n[yellow]1. Testing Axe Scanner...[/yellow]")
    try:
        scanner = AxeScanner()
        violations, status = await scanner.run(url)
        results["axe"] = {
            "status": status.status,
            "violations": len(violations),
            "duration": f"{status.duration_ms}ms"
        }
        console.print(f"   [green]✓[/green] Axe: {len(violations)} violations found ({status.duration_ms}ms)")
    except Exception as e:
        results["axe"] = {"status": "error", "error": str(e)}
        console.print(f"   [red]✗[/red] Axe failed: {e}")

    # Test HTML Validator
    console.print("\n[yellow]2. Testing HTML Validator...[/yellow]")
    try:
        scanner = HTMLValidatorScanner()
        violations, status = await scanner.run(url)
        results["html_validator"] = {
            "status": status.status,
            "violations": len(violations),
            "duration": f"{status.duration_ms}ms"
        }
        console.print(f"   [green]✓[/green] HTML Validator: {len(violations)} violations found ({status.duration_ms}ms)")
    except Exception as e:
        results["html_validator"] = {"status": "error", "error": str(e)}
        console.print(f"   [red]✗[/red] HTML Validator failed: {e}")

    # Test Contrast Checker
    console.print("\n[yellow]3. Testing Contrast Checker...[/yellow]")
    try:
        scanner = ContrastChecker()
        violations, status = await scanner.run(url)
        results["contrast"] = {
            "status": status.status,
            "violations": len(violations),
            "duration": f"{status.duration_ms}ms"
        }
        console.print(f"   [green]✓[/green] Contrast Checker: {len(violations)} violations found ({status.duration_ms}ms)")
    except Exception as e:
        results["contrast"] = {"status": "error", "error": str(e)}
        console.print(f"   [red]✗[/red] Contrast Checker failed: {e}")

    return results


async def test_aggregator():
    """Test the results aggregator with multiple tools."""
    console.print(Panel.fit("[bold blue]Testing Results Aggregator[/bold blue]"))

    url = "https://www.ascendons.in/"

    console.print(f"\n[yellow]Scanning {url} with all tools...[/yellow]")

    aggregator = ResultsAggregator(tools=["axe", "html_validator", "contrast"])
    result = await aggregator.scan(url)

    # Display results table
    table = Table(title="Scan Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("URL", result.url)
    table.add_row("Status", f"[green]{result.status.value}[/green]" if result.status.value == "completed" else f"[red]{result.status.value}[/red]")
    table.add_row("Duration", f"{result.duration_seconds:.2f}s")
    table.add_row("Overall Score", f"{result.scores.overall:.0f}/100")
    table.add_row("Total Violations", str(result.summary.total_violations))
    table.add_row("Critical", str(result.summary.by_impact.get("critical", 0)))
    table.add_row("Serious", str(result.summary.by_impact.get("serious", 0)))
    table.add_row("Moderate", str(result.summary.by_impact.get("moderate", 0)))
    table.add_row("Minor", str(result.summary.by_impact.get("minor", 0)))

    console.print(table)

    # Tools status
    tools_table = Table(title="Tools Status")
    tools_table.add_column("Tool")
    tools_table.add_column("Status")
    tools_table.add_column("Duration")

    for name, status in result.tools_used.items():
        status_str = "[green]OK[/green]" if status.status == "success" else f"[red]{status.status}[/red]"
        tools_table.add_row(name, status_str, f"{status.duration_ms}ms" if status.duration_ms else "N/A")

    console.print(tools_table)

    return result


async def test_report_generation(result):
    """Test report generation."""
    console.print(Panel.fit("[bold blue]Testing Report Generation[/bold blue]"))

    generator = ReportGenerator()

    # Test JSON report
    console.print("\n[yellow]1. Generating JSON report...[/yellow]")
    json_report = generator.to_json(result)
    console.print(f"   [green]✓[/green] JSON report generated ({len(json_report)} bytes)")

    # Test HTML report
    console.print("\n[yellow]2. Generating HTML report...[/yellow]")
    html_report = generator.to_html(result)
    console.print(f"   [green]✓[/green] HTML report generated ({len(html_report)} bytes)")

    # Save reports
    console.print("\n[yellow]3. Saving reports to files...[/yellow]")

    generator.save_report(result, "test_report.json", "json")
    console.print("   [green]✓[/green] Saved: test_report.json")

    generator.save_report(result, "test_report.html", "html")
    console.print("   [green]✓[/green] Saved: test_report.html")

    return True


async def test_multiple_urls():
    """Test scanning multiple URLs."""
    console.print(Panel.fit("[bold blue]Testing Multiple URLs[/bold blue]"))

    urls = [
        "https://www.ascendons.in/",
        "https://www.ascendons.in/about",  # Add more pages from your site
    ]

    results = []

    for url in urls:
        console.print(f"\n[yellow]Scanning: {url}[/yellow]")
        try:
            aggregator = ResultsAggregator(tools=["axe", "html_validator"])
            result = await aggregator.scan(url)
            results.append({
                "url": url,
                "status": result.status.value,
                "score": result.scores.overall,
                "violations": result.summary.total_violations
            })
            console.print(f"   [green]✓[/green] Score: {result.scores.overall:.0f}, Violations: {result.summary.total_violations}")
        except Exception as e:
            results.append({
                "url": url,
                "status": "error",
                "error": str(e)
            })
            console.print(f"   [red]✗[/red] Error: {e}")

    # Summary table
    table = Table(title="Multi-URL Scan Summary")
    table.add_column("URL")
    table.add_column("Status")
    table.add_column("Score")
    table.add_column("Violations")

    for r in results:
        if r["status"] == "completed":
            table.add_row(r["url"], "[green]OK[/green]", f"{r['score']:.0f}", str(r["violations"]))
        else:
            table.add_row(r["url"], "[red]Error[/red]", "-", "-")

    console.print(table)

    return results


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold green]WCAG Accessibility Scanner - Test Suite[/bold green]\n"
        "This will test all scanner components",
        border_style="green"
    ))

    try:
        # Test 1: Individual scanners
        await test_individual_scanners()

        # Test 2: Aggregator
        result = await test_aggregator()

        # Test 3: Report generation
        await test_report_generation(result)

        # Test 4: Multiple URLs
        await test_multiple_urls()

        console.print(Panel.fit(
            "[bold green]All tests completed successfully![/bold green]\n\n"
            "Generated files:\n"
            "  - test_report.json\n"
            "  - test_report.html\n\n"
            "Open test_report.html in a browser to see the visual report.",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"\n[red]Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
