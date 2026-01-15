"""Scan management commands."""

import asyncio
import time
import click
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from scanner_v2.cli.utils import (
    api_request,
    print_error,
    print_success,
    print_info,
    print_warning,
    format_scan_table,
    format_scan_detail,
    console
)


@click.group()
def scan():
    """Scan management commands."""
    pass


@scan.command()
@click.option("--project-id", "-p", help="Filter by project ID")
@click.option("--status", "-s", help="Filter by status")
@click.option("--limit", default=50, help="Number of scans to show")
def list(project_id: str, status: str, limit: int):
    """List scans."""
    async def do_list():
        try:
            params = {"limit": limit}
            if project_id:
                params["project_id"] = project_id
            if status:
                params["status_filter"] = status

            response = await api_request("GET", "/scans", params=params)

            if response.status_code == 200:
                data = response.json()
                scans = data.get("scans", [])
                total = data.get("total", 0)

                if not scans:
                    print_info("No scans found")
                    return

                table = format_scan_table(scans)
                console.print(table)
                print_info(f"Showing {len(scans)} of {total} scans")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to list scans: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to list scans: {e}")

    asyncio.run(do_list())


@scan.command()
@click.argument("project_id")
@click.option("--max-pages", type=int, default=10, help="Maximum pages to scan")
@click.option("--max-depth", type=int, default=2, help="Maximum crawl depth")
@click.option("--scanners", multiple=True, default=["axe"], help="Scanners to use")
@click.option("--wait", is_flag=True, help="Wait for scan to complete")
def start(project_id: str, max_pages: int, max_depth: int, scanners: tuple, wait: bool):
    """Start a new scan."""
    async def do_start():
        try:
            data = {
                "max_pages": max_pages,
                "max_depth": max_depth,
                "scanners": list(scanners)
            }

            response = await api_request(
                "POST",
                f"/projects/{project_id}/scans",
                data=data
            )

            if response.status_code == 201:
                scan = response.json()
                scan_id = scan["id"]
                print_success(f"Scan created: {scan_id}")
                print_info(f"Status: {scan['status']}")
                print_info(f"Use 'wcag-v2 scan show {scan_id}' to check progress")

                if wait:
                    print_info("\nWaiting for scan to complete...")
                    await wait_for_scan(scan_id)
            elif response.status_code == 404:
                print_error(f"Project not found: {project_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                error_data = response.json()
                print_error(f"Failed to start scan: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print_error(f"Failed to start scan: {e}")

    asyncio.run(do_start())


async def wait_for_scan(scan_id: str):
    """Wait for scan to complete with progress bar."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Scanning...", total=100)

        while True:
            try:
                response = await api_request("GET", f"/scans/{scan_id}/status")

                if response.status_code == 200:
                    data = response.json()
                    status = data["status"]
                    prog = data.get("progress", {})

                    # Update progress bar
                    total_pages = prog.get("total_pages", 0)
                    pages_scanned = prog.get("pages_scanned", 0)

                    if total_pages > 0:
                        percent = (pages_scanned / total_pages) * 100
                        progress.update(
                            task,
                            completed=percent,
                            description=f"Scanning... ({pages_scanned}/{total_pages} pages)"
                        )
                    else:
                        progress.update(task, description=f"Status: {status}")

                    # Check if completed
                    if status in ["completed", "failed", "cancelled"]:
                        if status == "completed":
                            progress.update(task, completed=100, description="✓ Scan completed")
                            print_success(f"\nScan completed successfully")

                            # Get full scan details
                            scan_response = await api_request("GET", f"/scans/{scan_id}")
                            if scan_response.status_code == 200:
                                scan = scan_response.json()
                                panel = format_scan_detail(scan)
                                console.print(panel)
                        elif status == "failed":
                            progress.update(task, description="✗ Scan failed")
                            print_error(f"\nScan failed: {data.get('error_message', 'Unknown error')}")
                        else:
                            progress.update(task, description="⚠ Scan cancelled")
                            print_warning("\nScan was cancelled")
                        break

                    await asyncio.sleep(2)
                else:
                    print_error("Failed to get scan status")
                    break
            except Exception as e:
                print_error(f"Error waiting for scan: {e}")
                break


@scan.command()
@click.argument("scan_id")
def show(scan_id: str):
    """Show scan details."""
    async def do_show():
        try:
            response = await api_request("GET", f"/scans/{scan_id}")

            if response.status_code == 200:
                scan = response.json()
                panel = format_scan_detail(scan)
                console.print(panel)
            elif response.status_code == 404:
                print_error(f"Scan not found: {scan_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to get scan: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to get scan: {e}")

    asyncio.run(do_show())


@scan.command()
@click.argument("scan_id")
@click.option("--follow", "-f", is_flag=True, help="Follow scan progress")
def status(scan_id: str, follow: bool):
    """Check scan status."""
    async def do_status():
        try:
            if follow:
                # Follow mode - continuously update
                await wait_for_scan(scan_id)
            else:
                # One-time status check
                response = await api_request("GET", f"/scans/{scan_id}/status")

                if response.status_code == 200:
                    data = response.json()
                    status_val = data["status"]
                    prog = data.get("progress", {})

                    console.print(f"[cyan]Scan ID:[/cyan] {scan_id}")
                    console.print(f"[cyan]Status:[/cyan] {status_val}")

                    if prog:
                        console.print(f"[cyan]Progress:[/cyan]")
                        console.print(f"  Pages Crawled: {prog.get('pages_crawled', 0)}")
                        console.print(f"  Pages Scanned: {prog.get('pages_scanned', 0)}")
                        console.print(f"  Total Pages: {prog.get('total_pages', 0)}")
                        if prog.get("current_page"):
                            console.print(f"  Current: {prog['current_page']}")

                    if data.get("started_at"):
                        console.print(f"[cyan]Started:[/cyan] {data['started_at']}")
                    if data.get("completed_at"):
                        console.print(f"[cyan]Completed:[/cyan] {data['completed_at']}")
                    if data.get("error_message"):
                        console.print(f"[red]Error:[/red] {data['error_message']}")
                elif response.status_code == 404:
                    print_error(f"Scan not found: {scan_id}")
                elif response.status_code == 401:
                    print_error("Not authenticated")
                    print_info("Use 'wcag-v2 auth login' to login first")
                else:
                    print_error(f"Failed to get scan status: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to get scan status: {e}")

    asyncio.run(do_status())


@scan.command()
@click.argument("scan_id")
def cancel(scan_id: str):
    """Cancel a running scan."""
    async def do_cancel():
        try:
            response = await api_request("POST", f"/scans/{scan_id}/cancel")

            if response.status_code == 200:
                print_success(f"Scan cancelled: {scan_id}")
            elif response.status_code == 400:
                error_data = response.json()
                print_error(f"Cannot cancel scan: {error_data.get('detail', 'Unknown error')}")
            elif response.status_code == 404:
                print_error(f"Scan not found: {scan_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to cancel scan: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to cancel scan: {e}")

    asyncio.run(do_cancel())


@scan.command()
@click.argument("scan_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(scan_id: str, yes: bool):
    """Delete a scan."""
    async def do_delete():
        try:
            if not yes:
                confirm = click.confirm(f"Are you sure you want to delete scan {scan_id}?")
                if not confirm:
                    print_info("Cancelled")
                    return

            response = await api_request("DELETE", f"/scans/{scan_id}")

            if response.status_code == 204:
                print_success(f"Scan deleted: {scan_id}")
            elif response.status_code == 404:
                print_error(f"Scan not found: {scan_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to delete scan: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to delete scan: {e}")

    asyncio.run(do_delete())
