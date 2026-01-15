"""Main CLI entry point."""

import click

from scanner_v2.cli.commands.server import server
from scanner_v2.cli.commands.auth import auth
from scanner_v2.cli.commands.project import project
from scanner_v2.cli.commands.scan import scan
from scanner_v2.cli.commands.report import report
from scanner_v2.cli.commands.dashboard import dashboard


@click.group()
@click.version_option(version="2.0.0", prog_name="WCAG Scanner V2")
def cli():
    """
    WCAG Scanner V2 - Command Line Interface

    Production-ready WCAG compliance scanner with FastAPI backend.
    """
    pass


# Add command groups
cli.add_command(server)
cli.add_command(auth)
cli.add_command(project)
cli.add_command(scan)
cli.add_command(report)
cli.add_command(dashboard)


if __name__ == "__main__":
    cli()
