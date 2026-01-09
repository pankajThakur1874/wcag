"""CLI interface for WCAG Scanner."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core import ResultsAggregator, ReportGenerator
from src.scanners import SCANNERS
from src.utils.config import get_config

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="wcag-scanner")
def cli():
    """WCAG Accessibility Scanner - Scan websites for accessibility issues."""
    pass


@cli.command()
@click.argument("url")
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "html"]),
    default="json",
    help="Output format (default: json)"
)
@click.option(
    "--tools", "-t",
    multiple=True,
    type=click.Choice(list(SCANNERS.keys())),
    help="Tools to use (can specify multiple). Default: all"
)
@click.option(
    "--level", "-l",
    type=click.Choice(["A", "AA", "AAA"]),
    default="AA",
    help="WCAG conformance level (default: AA)"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Verbose output"
)
def scan(
    url: str,
    output: Optional[str],
    format: str,
    tools: tuple,
    level: str,
    verbose: bool
):
    """Scan a URL for accessibility issues.

    Example:
        wcag-scanner scan https://example.com
        wcag-scanner scan https://example.com -o report.html -f html
        wcag-scanner scan https://example.com -t axe -t pa11y
    """
    asyncio.run(_run_scan(url, output, format, tools, level, verbose))


async def _run_scan(
    url: str,
    output: Optional[str],
    format: str,
    tools: tuple,
    level: str,
    verbose: bool
):
    """Run the scan asynchronously."""
    console.print(Panel.fit(
        f"[bold blue]WCAG Accessibility Scanner[/bold blue]\n"
        f"Scanning: {url}",
        border_style="blue"
    ))

    # Determine tools to use
    tools_list = list(tools) if tools else None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Scanning...", total=None)

        try:
            # Run scan
            aggregator = ResultsAggregator(tools=tools_list)
            result = await aggregator.scan(url)

            progress.update(task, description="Scan complete!")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    # Display results
    _display_results(result, verbose)

    # Save report if output specified
    if output:
        generator = ReportGenerator()
        generator.save_report(result, output, format)
        console.print(f"\n[green]Report saved to: {output}[/green]")
    else:
        # Print JSON to stdout if no output file
        if format == "json":
            generator = ReportGenerator()
            console.print("\n[dim]JSON Output:[/dim]")
            print(generator.to_json(result))


def _display_results(result, verbose: bool):
    """Display scan results in the console."""
    # Summary table
    summary_table = Table(title="Scan Summary", show_header=False)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("URL", result.url)
    summary_table.add_row("Status", f"[green]{result.status.value}[/green]" if result.status.value == "completed" else f"[red]{result.status.value}[/red]")
    summary_table.add_row("Duration", f"{result.duration_seconds:.2f}s" if result.duration_seconds else "N/A")

    # Score with color
    score = result.scores.overall
    if score >= 90:
        score_color = "green"
    elif score >= 70:
        score_color = "yellow"
    elif score >= 50:
        score_color = "orange1"
    else:
        score_color = "red"
    summary_table.add_row("Score", f"[{score_color}]{score:.0f}/100[/{score_color}]")

    console.print(summary_table)

    # Violations summary
    violations_table = Table(title="Violations by Impact")
    violations_table.add_column("Impact", style="bold")
    violations_table.add_column("Count", justify="right")

    violations_table.add_row("[red]Critical[/red]", str(result.summary.by_impact.get("critical", 0)))
    violations_table.add_row("[orange1]Serious[/orange1]", str(result.summary.by_impact.get("serious", 0)))
    violations_table.add_row("[yellow]Moderate[/yellow]", str(result.summary.by_impact.get("moderate", 0)))
    violations_table.add_row("[green]Minor[/green]", str(result.summary.by_impact.get("minor", 0)))
    violations_table.add_row("[bold]Total[/bold]", f"[bold]{result.summary.total_violations}[/bold]")

    console.print(violations_table)

    # Tools used
    tools_table = Table(title="Tools Status")
    tools_table.add_column("Tool")
    tools_table.add_column("Status")
    tools_table.add_column("Duration")

    for name, status in result.tools_used.items():
        status_str = "[green]OK[/green]" if status.status == "success" else f"[red]{status.status}[/red]"
        duration_str = f"{status.duration_ms}ms" if status.duration_ms else "N/A"
        tools_table.add_row(name, status_str, duration_str)

    console.print(tools_table)

    # Detailed violations (if verbose or few violations)
    if verbose or result.summary.total_violations <= 10:
        if result.violations:
            console.print("\n[bold]Violations Detail:[/bold]")

            for i, v in enumerate(result.violations[:20], 1):  # Limit to 20
                impact_color = {
                    "critical": "red",
                    "serious": "orange1",
                    "moderate": "yellow",
                    "minor": "green"
                }.get(v.impact.value, "white")

                console.print(f"\n[{impact_color}]{i}. [{v.impact.value.upper()}] {v.description}[/{impact_color}]")
                console.print(f"   WCAG: {', '.join(v.wcag_criteria) or 'N/A'}")
                console.print(f"   Detected by: {', '.join(v.detected_by)}")

                if v.instances and verbose:
                    console.print(f"   Affected elements: {len(v.instances)}")
                    for inst in v.instances[:3]:  # Show first 3
                        console.print(f"   - {inst.selector}")

                if v.help_url:
                    console.print(f"   [dim]Learn more: {v.help_url}[/dim]")


@cli.command()
def tools():
    """List available scanning tools."""
    table = Table(title="Available Scanners")
    table.add_column("Name", style="cyan")
    table.add_column("Description")

    tool_descriptions = {
        "axe": "axe-core accessibility engine - comprehensive WCAG testing",
        "pa11y": "Pa11y automated accessibility testing tool",
        "lighthouse": "Google Lighthouse accessibility audits",
        "html_validator": "HTML structure and semantic validation",
        "contrast": "Color contrast ratio checker"
    }

    for name in SCANNERS:
        table.add_row(name, tool_descriptions.get(name, ""))

    console.print(table)


@cli.command()
def config():
    """Show current configuration."""
    cfg = get_config()

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Browser Headless", str(cfg.browser.headless))
    table.add_row("Browser Timeout", f"{cfg.browser.timeout}ms")
    table.add_row("Scan Timeout", f"{cfg.scan.timeout}s")
    table.add_row("Default WCAG Level", cfg.scan.wcag_level)
    table.add_row("Default Tools", ", ".join(cfg.scan.tools))
    table.add_row("Log Level", cfg.log_level)

    console.print(table)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
