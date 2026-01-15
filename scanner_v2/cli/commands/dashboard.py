"""Dashboard command."""

import click
from scanner_v2.cli.utils import print_info, print_error


@click.command()
def dashboard():
    """Launch interactive TUI dashboard."""
    try:
        print_info("Launching dashboard...")
        print_info("Press 'q' to quit, 'r' to refresh")
        print_info("")

        from scanner_v2.cli.tui.app import run_dashboard
        run_dashboard()

    except KeyboardInterrupt:
        print_info("\nDashboard closed")
    except Exception as e:
        print_error(f"Failed to launch dashboard: {e}")
