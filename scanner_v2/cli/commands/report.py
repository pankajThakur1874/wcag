"""Report generation commands."""

import asyncio
import json
from pathlib import Path
import click

from scanner_v2.cli.utils import (
    api_request,
    print_error,
    print_success,
    print_info,
    format_issue_table,
    console
)


@click.group()
def report():
    """Report generation commands."""
    pass


@report.command()
@click.argument("scan_id")
@click.option("--format", "-f", type=click.Choice(["json", "text"]), default="text", help="Output format")
def view(scan_id: str, format: str):
    """View scan report."""
    async def do_view():
        try:
            # Get JSON report
            response = await api_request("GET", f"/scans/{scan_id}/reports/json")

            if response.status_code == 200:
                report = response.json()

                if format == "json":
                    # Print JSON
                    console.print_json(data=report)
                else:
                    # Print formatted text report
                    print_text_report(report)
            elif response.status_code == 404:
                print_error(f"Scan not found: {scan_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to get report: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to get report: {e}")

    asyncio.run(do_view())


def print_text_report(report: dict):
    """Print formatted text report."""
    scan = report.get("scan", {})
    project = report.get("project", {})
    summary = report.get("summary", {})
    scores = report.get("scores", {})

    # Header
    console.print("\n")
    console.rule(f"[bold cyan]WCAG Scan Report[/bold cyan]")
    console.print()

    # Project info
    console.print(f"[cyan]Project:[/cyan] {project.get('name')}")
    console.print(f"[cyan]URL:[/cyan] {project.get('base_url')}")
    console.print(f"[cyan]Scan ID:[/cyan] {scan.get('id')}")
    console.print(f"[cyan]Status:[/cyan] {scan.get('status')}")
    console.print()

    # Summary
    console.rule("[bold]Summary[/bold]")
    console.print()
    console.print(f"[cyan]Total Pages:[/cyan] {summary.get('total_pages', 0)}")
    console.print(f"[cyan]Total Issues:[/cyan] {summary.get('total_issues', 0)}")
    console.print()

    # Issues by impact
    by_impact = summary.get("by_impact", {})
    if by_impact:
        console.print("[cyan]Issues by Impact:[/cyan]")
        console.print(f"  [red bold]Critical:[/red bold] {by_impact.get('critical', 0)}")
        console.print(f"  [red]Serious:[/red] {by_impact.get('serious', 0)}")
        console.print(f"  [yellow]Moderate:[/yellow] {by_impact.get('moderate', 0)}")
        console.print(f"  [blue]Minor:[/blue] {by_impact.get('minor', 0)}")
        console.print()

    # Issues by WCAG level
    by_wcag = summary.get("by_wcag_level", {})
    if by_wcag:
        console.print("[cyan]Issues by WCAG Level:[/cyan]")
        console.print(f"  Level A: {by_wcag.get('A', 0)}")
        console.print(f"  Level AA: {by_wcag.get('AA', 0)}")
        console.print(f"  Level AAA: {by_wcag.get('AAA', 0)}")
        console.print()

    # Scores
    if scores:
        console.rule("[bold]Compliance Scores[/bold]")
        console.print()
        overall = scores.get("overall", 0)

        # Color based on score
        if overall >= 90:
            color = "green"
        elif overall >= 70:
            color = "yellow"
        else:
            color = "red"

        console.print(f"[cyan]Overall Score:[/cyan] [{color}]{overall:.1f}/100[/{color}]")

        by_principle = scores.get("by_principle", {})
        if by_principle:
            console.print()
            console.print("[cyan]By Principle:[/cyan]")
            for principle, score in by_principle.items():
                console.print(f"  {principle.title()}: {score:.1f}/100")

    console.print()
    console.rule("[dim]End of Report[/dim]")
    console.print()


@report.command()
@click.argument("scan_id")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--format", "-f", type=click.Choice(["json", "html", "csv"]), default="json", help="Output format")
def export(scan_id: str, output: str, format: str):
    """Export scan report to file."""
    async def do_export():
        try:
            # Determine endpoint based on format
            if format == "json":
                endpoint = f"/scans/{scan_id}/reports/json"
            elif format == "html":
                endpoint = f"/scans/{scan_id}/reports/html"
            elif format == "csv":
                endpoint = f"/scans/{scan_id}/reports/csv"
            else:
                print_error(f"Unsupported format: {format}")
                return

            # Get report
            response = await api_request("GET", endpoint)

            if response.status_code == 200:
                # Write to file
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if format == "json":
                    report = response.json()
                    with open(output_path, "w") as f:
                        json.dump(report, f, indent=2)
                elif format == "html":
                    with open(output_path, "w") as f:
                        f.write(response.text)
                elif format == "csv":
                    with open(output_path, "w") as f:
                        f.write(response.text)

                print_success(f"Report exported to: {output_path}")
                print_info(f"Format: {format.upper()}")

                if format == "html":
                    print_info(f"Open in browser: file://{output_path.absolute()}")
            elif response.status_code == 404:
                print_error(f"Scan not found: {scan_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to export report: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to export report: {e}")

    asyncio.run(do_export())


@report.command()
@click.argument("scan_id")
@click.option("--impact", help="Filter by impact (critical, serious, moderate, minor)")
@click.option("--wcag-level", help="Filter by WCAG level (A, AA, AAA)")
@click.option("--limit", default=50, help="Number of issues to show")
def issues(scan_id: str, impact: str, wcag_level: str, limit: int):
    """List issues for a scan."""
    async def do_issues():
        try:
            params = {"scan_id": scan_id, "limit": limit}
            if impact:
                params["impact"] = impact
            if wcag_level:
                params["wcag_level"] = wcag_level

            response = await api_request("GET", "/issues/", params=params)

            if response.status_code == 200:
                data = response.json()
                issue_list = data.get("issues", [])
                total = data.get("total", 0)

                if not issue_list:
                    print_info("No issues found")
                    return

                table = format_issue_table(issue_list)
                console.print(table)
                print_info(f"Showing {len(issue_list)} of {total} issues")
            elif response.status_code == 404:
                print_error(f"Scan not found: {scan_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to list issues: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to list issues: {e}")

    asyncio.run(do_issues())
