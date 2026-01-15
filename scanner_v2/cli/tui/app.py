"""Main TUI application."""

import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Button
from textual.binding import Binding
from textual import on

from scanner_v2.cli.utils import api_request, console


class WCAGDashboardApp(App):
    """WCAG Scanner V2 TUI Dashboard."""

    CSS = """
    Screen {
        background: $surface;
    }

    #stats-panel {
        height: 8;
        background: $boost;
        border: solid $primary;
        padding: 1;
    }

    #scans-table {
        height: 1fr;
        border: solid $accent;
    }

    #projects-panel {
        width: 35%;
        border: solid $secondary;
    }

    .stat-label {
        color: $text;
        text-style: bold;
    }

    .stat-value {
        color: $accent;
        text-style: bold;
    }

    .status-completed {
        color: green;
    }

    .status-failed {
        color: red;
    }

    .status-scanning {
        color: yellow;
    }

    .status-queued {
        color: blue;
    }

    Button {
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "show_scans", "Scans"),
        Binding("p", "show_projects", "Projects"),
        ("d", "show_dashboard", "Dashboard"),
    ]

    def __init__(self):
        super().__init__()
        self.scans_data = []
        self.projects_data = []
        self.stats_data = {}
        self.auto_refresh_task = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        # Stats panel
        with Container(id="stats-panel"):
            yield Static("Loading statistics...", id="stats-content")

        # Main content
        with Horizontal():
            # Scans table
            with Vertical(id="scans-container"):
                yield Static("Recent Scans", classes="section-title")
                scans_table = DataTable(id="scans-table")
                scans_table.cursor_type = "row"
                scans_table.zebra_stripes = True
                yield scans_table

            # Projects panel
            with Vertical(id="projects-panel"):
                yield Static("Projects", classes="section-title")
                projects_table = DataTable(id="projects-table")
                projects_table.cursor_type = "row"
                projects_table.zebra_stripes = True
                yield projects_table

        # Action buttons
        with Horizontal(id="actions"):
            yield Button("Refresh (r)", variant="primary", id="btn-refresh")
            yield Button("Quit (q)", variant="error", id="btn-quit")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the dashboard."""
        # Setup scans table
        scans_table = self.query_one("#scans-table", DataTable)
        scans_table.add_columns("ID", "Project", "Status", "Progress", "Issues", "Score")

        # Setup projects table
        projects_table = self.query_one("#projects-table", DataTable)
        projects_table.add_columns("ID", "Name")

        # Initial load
        await self.refresh_data()

        # Start auto-refresh
        self.auto_refresh_task = asyncio.create_task(self.auto_refresh())

    async def auto_refresh(self):
        """Auto-refresh data every 5 seconds."""
        while True:
            await asyncio.sleep(5)
            try:
                await self.refresh_data()
            except Exception:
                pass

    async def refresh_data(self):
        """Refresh all data from API."""
        try:
            # Fetch scans
            scans_response = await api_request("GET", "/scans", params={"limit": 20})
            if scans_response.status_code == 200:
                data = scans_response.json()
                self.scans_data = data.get("scans", [])

            # Fetch projects
            projects_response = await api_request("GET", "/projects/", params={"limit": 10})
            if projects_response.status_code == 200:
                data = projects_response.json()
                self.projects_data = data.get("projects", [])

            # Update UI
            self.update_scans_table()
            self.update_projects_table()
            self.update_stats()

        except Exception as e:
            self.notify(f"Error refreshing data: {e}", severity="error")

    def update_scans_table(self):
        """Update scans table."""
        scans_table = self.query_one("#scans-table", DataTable)
        scans_table.clear()

        for scan in self.scans_data:
            # Format data
            scan_id = scan["id"][:8]
            project_id = scan["project_id"][:8]
            status = scan["status"]

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
            score_str = f"{scores.get('overall', 0):.0f}" if scores else "-"

            # Add row with status color
            scans_table.add_row(
                scan_id,
                project_id,
                f"[{self.get_status_color(status)}]{status}[/]",
                progress_str,
                issues_str,
                score_str,
                key=scan["id"]
            )

    def update_projects_table(self):
        """Update projects table."""
        projects_table = self.query_one("#projects-table", DataTable)
        projects_table.clear()

        for project in self.projects_data:
            projects_table.add_row(
                project["id"][:8],
                project["name"][:30],
                key=project["id"]
            )

    def update_stats(self):
        """Update statistics panel."""
        total_scans = len(self.scans_data)
        completed = len([s for s in self.scans_data if s["status"] == "completed"])
        scanning = len([s for s in self.scans_data if s["status"] == "scanning"])
        failed = len([s for s in self.scans_data if s["status"] == "failed"])
        total_projects = len(self.projects_data)

        # Calculate total issues
        total_issues = sum(
            scan.get("summary", {}).get("total_issues", 0)
            for scan in self.scans_data
            if scan.get("summary")
        )

        stats_text = f"""[bold cyan]Dashboard Statistics[/bold cyan]

[stat-label]Projects:[/stat-label] [stat-value]{total_projects}[/stat-value]  |  [stat-label]Total Scans:[/stat-label] [stat-value]{total_scans}[/stat-value]  |  [stat-label]Total Issues:[/stat-label] [stat-value]{total_issues}[/stat-value]

[stat-label]Scans:[/stat-label] [green]{completed} Completed[/green]  |  [yellow]{scanning} Scanning[/yellow]  |  [red]{failed} Failed[/red]
"""

        stats_content = self.query_one("#stats-content", Static)
        stats_content.update(stats_text)

    def get_status_color(self, status: str) -> str:
        """Get color for status."""
        color_map = {
            "completed": "green",
            "failed": "red",
            "scanning": "yellow",
            "queued": "blue",
            "cancelled": "dim"
        }
        return color_map.get(status, "white")

    @on(Button.Pressed, "#btn-refresh")
    async def handle_refresh_button(self):
        """Handle refresh button."""
        await self.action_refresh()

    @on(Button.Pressed, "#btn-quit")
    def handle_quit_button(self):
        """Handle quit button."""
        self.action_quit()

    async def action_refresh(self):
        """Refresh data."""
        self.notify("Refreshing data...")
        await self.refresh_data()
        self.notify("Data refreshed", severity="information")

    def action_show_scans(self):
        """Show scans screen."""
        self.notify("Scans view")

    def action_show_projects(self):
        """Show projects screen."""
        self.notify("Projects view")

    def action_show_dashboard(self):
        """Show dashboard screen."""
        self.notify("Dashboard view")

    async def on_unmount(self):
        """Cleanup when app closes."""
        if self.auto_refresh_task:
            self.auto_refresh_task.cancel()


def run_dashboard():
    """Run the TUI dashboard."""
    app = WCAGDashboardApp()
    app.run()


if __name__ == "__main__":
    run_dashboard()
