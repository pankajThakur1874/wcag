"""CLI utilities for API calls and formatting."""

import httpx
import json
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

# Configuration file path
CONFIG_FILE = Path.home() / ".wcag-scanner" / "config.json"


def load_cli_config() -> Dict[str, Any]:
    """
    Load CLI configuration.

    Returns:
        Configuration dictionary
    """
    if not CONFIG_FILE.exists():
        return {
            "api_url": "http://localhost:8000/api/v1",
            "token": None
        }

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "api_url": "http://localhost:8000/api/v1",
            "token": None
        }


def save_cli_config(config: Dict[str, Any]) -> None:
    """
    Save CLI configuration.

    Args:
        config: Configuration dictionary
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_api_url() -> str:
    """Get API URL from config."""
    config = load_cli_config()
    return config.get("api_url", "http://localhost:8000/api/v1")


def get_token() -> Optional[str]:
    """Get auth token from config."""
    config = load_cli_config()
    return config.get("token")


def save_token(token: str) -> None:
    """Save auth token to config."""
    config = load_cli_config()
    config["token"] = token
    save_cli_config(config)


def clear_token() -> None:
    """Clear auth token from config."""
    config = load_cli_config()
    config["token"] = None
    save_cli_config(config)


def get_headers() -> Dict[str, str]:
    """
    Get HTTP headers with auth token.

    Returns:
        Headers dictionary
    """
    headers = {"Content-Type": "application/json"}
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> httpx.Response:
    """
    Make API request.

    Args:
        method: HTTP method
        endpoint: API endpoint
        data: Request data
        params: Query parameters

    Returns:
        Response object

    Raises:
        httpx.HTTPError: If request fails
    """
    api_url = get_api_url()
    url = f"{api_url}{endpoint}"
    headers = get_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response


def print_error(message: str) -> None:
    """
    Print error message.

    Args:
        message: Error message
    """
    console.print(f"[red]✗ Error:[/red] {message}")


def print_success(message: str) -> None:
    """
    Print success message.

    Args:
        message: Success message
    """
    console.print(f"[green]✓[/green] {message}")


def print_info(message: str) -> None:
    """
    Print info message.

    Args:
        message: Info message
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str) -> None:
    """
    Print warning message.

    Args:
        message: Warning message
    """
    console.print(f"[yellow]⚠[/yellow] {message}")


def format_project_table(projects: list) -> Table:
    """
    Format projects as table.

    Args:
        projects: List of projects

    Returns:
        Rich table
    """
    table = Table(title="Projects", box=box.ROUNDED)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Base URL", style="blue")
    table.add_column("Description")
    table.add_column("Created", style="dim")

    for project in projects:
        table.add_row(
            project["id"][:8],
            project["name"],
            project["base_url"],
            project.get("description", "")[:50] or "-",
            project["created_at"][:10]
        )

    return table


def format_scan_table(scans: list) -> Table:
    """
    Format scans as table.

    Args:
        scans: List of scans

    Returns:
        Rich table
    """
    table = Table(title="Scans", box=box.ROUNDED)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Project ID", style="dim", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="yellow")
    table.add_column("Progress")
    table.add_column("Issues", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Created", style="dim")

    for scan in scans:
        # Status color
        status = scan["status"]
        if status == "completed":
            status_color = "green"
        elif status == "failed":
            status_color = "red"
        elif status == "scanning":
            status_color = "yellow"
        else:
            status_color = "blue"

        # Progress
        progress = scan.get("progress")
        if progress:
            progress_str = f"{progress.get('pages_scanned', 0)}/{progress.get('total_pages', 0)}"
        else:
            progress_str = "-"

        # Issues
        summary = scan.get("summary")
        issues_str = str(summary.get("total_issues", 0)) if summary else "-"

        # Score
        scores = scan.get("scores")
        score_str = f"{scores.get('overall', 0):.1f}" if scores else "-"

        table.add_row(
            scan["id"][:8],
            scan["project_id"][:8],
            scan["scan_type"],
            f"[{status_color}]{status}[/{status_color}]",
            progress_str,
            issues_str,
            score_str,
            scan["created_at"][:10]
        )

    return table


def format_issue_table(issues: list) -> Table:
    """
    Format issues as table.

    Args:
        issues: List of issues

    Returns:
        Rich table
    """
    table = Table(title="Issues", box=box.ROUNDED)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Rule", style="magenta")
    table.add_column("Impact", style="red")
    table.add_column("WCAG", style="yellow")
    table.add_column("Description")
    table.add_column("Status", style="green")

    for issue in issues:
        # Impact color
        impact = issue["impact"]
        if impact == "critical":
            impact_color = "red bold"
        elif impact == "serious":
            impact_color = "red"
        elif impact == "moderate":
            impact_color = "yellow"
        else:
            impact_color = "blue"

        table.add_row(
            issue["id"][:8],
            issue["rule_id"],
            f"[{impact_color}]{impact}[/{impact_color}]",
            issue["wcag_level"],
            issue["description"][:60] + "..." if len(issue["description"]) > 60 else issue["description"],
            issue["status"]
        )

    return table


def format_project_detail(project: Dict) -> Panel:
    """
    Format project details as panel.

    Args:
        project: Project data

    Returns:
        Rich panel
    """
    content = f"""
[cyan]ID:[/cyan] {project['id']}
[cyan]Name:[/cyan] {project['name']}
[cyan]Base URL:[/cyan] {project['base_url']}
[cyan]Description:[/cyan] {project.get('description', 'N/A')}

[cyan]Settings:[/cyan]
  Max Depth: {project['settings']['max_depth']}
  Max Pages: {project['settings']['max_pages']}
  WCAG Level: {project['settings']['wcag_level']}

[cyan]Timestamps:[/cyan]
  Created: {project['created_at']}
  Updated: {project['updated_at']}
    """.strip()

    return Panel(content, title=f"Project: {project['name']}", border_style="green")


def format_scan_detail(scan: Dict) -> Panel:
    """
    Format scan details as panel.

    Args:
        scan: Scan data

    Returns:
        Rich panel
    """
    # Status color
    status = scan["status"]
    if status == "completed":
        status_color = "green"
    elif status == "failed":
        status_color = "red"
    elif status == "scanning":
        status_color = "yellow"
    else:
        status_color = "blue"

    # Build content
    lines = [
        f"[cyan]ID:[/cyan] {scan['id']}",
        f"[cyan]Project ID:[/cyan] {scan['project_id']}",
        f"[cyan]Type:[/cyan] {scan['scan_type']}",
        f"[cyan]Status:[/cyan] [{status_color}]{status}[/{status_color}]",
    ]

    # Progress
    if scan.get("progress"):
        progress = scan["progress"]
        lines.append(f"\n[cyan]Progress:[/cyan]")
        lines.append(f"  Pages Crawled: {progress.get('pages_crawled', 0)}")
        lines.append(f"  Pages Scanned: {progress.get('pages_scanned', 0)}")
        lines.append(f"  Total Pages: {progress.get('total_pages', 0)}")
        if progress.get("current_page"):
            lines.append(f"  Current: {progress['current_page']}")

    # Summary
    if scan.get("summary"):
        summary = scan["summary"]
        lines.append(f"\n[cyan]Summary:[/cyan]")
        lines.append(f"  Total Issues: {summary.get('total_issues', 0)}")
        if summary.get("by_impact"):
            by_impact = summary["by_impact"]
            lines.append(f"  Critical: {by_impact.get('critical', 0)}")
            lines.append(f"  Serious: {by_impact.get('serious', 0)}")
            lines.append(f"  Moderate: {by_impact.get('moderate', 0)}")
            lines.append(f"  Minor: {by_impact.get('minor', 0)}")

    # Scores
    if scan.get("scores"):
        scores = scan["scores"]
        lines.append(f"\n[cyan]Scores:[/cyan]")
        lines.append(f"  Overall: {scores.get('overall', 0):.1f}/100")

    # Timestamps
    lines.append(f"\n[cyan]Timestamps:[/cyan]")
    lines.append(f"  Created: {scan['created_at']}")
    if scan.get("started_at"):
        lines.append(f"  Started: {scan['started_at']}")
    if scan.get("completed_at"):
        lines.append(f"  Completed: {scan['completed_at']}")

    # Error
    if scan.get("error_message"):
        lines.append(f"\n[red]Error:[/red] {scan['error_message']}")

    content = "\n".join(lines)

    return Panel(content, title=f"Scan: {scan['id'][:12]}...", border_style="cyan")
