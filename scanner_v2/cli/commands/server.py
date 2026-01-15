"""Server management commands."""

import asyncio
import subprocess
import signal
import time
from pathlib import Path
import psutil
import click
from rich.console import Console

from scanner_v2.cli.utils import print_error, print_success, print_info, api_request

console = Console()

PID_FILE = Path.home() / ".wcag-scanner" / "server.pid"


def get_server_pid() -> int:
    """
    Get server PID from file.

    Returns:
        PID or None
    """
    if not PID_FILE.exists():
        return None

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
            # Check if process exists
            if psutil.pid_exists(pid):
                return pid
            else:
                # Clean up stale PID file
                PID_FILE.unlink()
                return None
    except Exception:
        return None


def save_server_pid(pid: int) -> None:
    """Save server PID to file."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(pid))


def clear_server_pid() -> None:
    """Clear server PID file."""
    if PID_FILE.exists():
        PID_FILE.unlink()


@click.group()
def server():
    """Server management commands."""
    pass


@server.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def start(host: str, port: int, reload: bool):
    """Start the API server."""
    # Check if already running
    pid = get_server_pid()
    if pid:
        print_error(f"Server is already running (PID: {pid})")
        print_info(f"Use 'wcag-v2 server stop' to stop it first")
        return

    print_info(f"Starting API server on {host}:{port}...")

    # Start server process
    project_root = Path(__file__).parent.parent.parent.parent
    cmd = [
        "python",
        str(project_root / "main_v2.py"),
    ]

    # Set environment variables for server config
    import os
    env = os.environ.copy()
    env["SERVER_HOST"] = host
    env["SERVER_PORT"] = str(port)
    env["SERVER_RELOAD"] = str(reload).lower()

    try:
        # Start in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True
        )

        # Save PID
        save_server_pid(process.pid)

        # Wait a bit to check if it started successfully
        time.sleep(2)

        if process.poll() is None:
            print_success(f"Server started successfully (PID: {process.pid})")
            print_info(f"API: http://{host}:{port}/api/v1")
            print_info(f"Docs: http://{host}:{port}/docs")
            print_info(f"Use 'wcag-v2 server logs' to view logs")
            print_info(f"Use 'wcag-v2 server stop' to stop")
        else:
            stdout, stderr = process.communicate()
            print_error("Server failed to start")
            if stderr:
                console.print(f"[red]{stderr.decode()}[/red]")
            clear_server_pid()
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        clear_server_pid()


@server.command()
def stop():
    """Stop the API server."""
    pid = get_server_pid()

    if not pid:
        print_error("Server is not running")
        return

    print_info(f"Stopping server (PID: {pid})...")

    try:
        # Send SIGTERM for graceful shutdown
        process = psutil.Process(pid)
        process.terminate()

        # Wait for process to stop
        try:
            process.wait(timeout=10)
            print_success("Server stopped successfully")
        except psutil.TimeoutExpired:
            print_warning("Server did not stop gracefully, forcing...")
            process.kill()
            print_success("Server killed")

        clear_server_pid()
    except psutil.NoSuchProcess:
        print_error(f"Process {pid} not found")
        clear_server_pid()
    except Exception as e:
        print_error(f"Failed to stop server: {e}")


@server.command()
def status():
    """Check server status."""
    pid = get_server_pid()

    if not pid:
        print_info("Server is not running")
        return

    try:
        process = psutil.Process(pid)

        # Get process info
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(process.create_time()))

        print_success(f"Server is running (PID: {pid})")
        console.print(f"  Started: {create_time}")
        console.print(f"  CPU: {cpu_percent:.1f}%")
        console.print(f"  Memory: {memory_mb:.1f} MB")

        # Try to ping API
        async def check_api():
            try:
                response = await api_request("GET", "/health/")
                if response.status_code == 200:
                    data = response.json()
                    console.print(f"  API Status: [green]{data.get('status', 'unknown')}[/green]")
                else:
                    console.print(f"  API Status: [red]unreachable[/red]")
            except Exception:
                console.print(f"  API Status: [red]unreachable[/red]")

        asyncio.run(check_api())

    except psutil.NoSuchProcess:
        print_error(f"Process {pid} not found (stale PID file)")
        clear_server_pid()
    except Exception as e:
        print_error(f"Failed to get server status: {e}")


@server.command()
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(follow: bool):
    """View server logs (not implemented)."""
    print_warning("Log viewing not implemented yet")
    print_info("Run server in foreground to see logs: python main_v2.py")


@server.command()
def restart():
    """Restart the API server."""
    # Get current config before stopping
    pid = get_server_pid()
    if pid:
        print_info("Stopping current server...")
        ctx = click.get_current_context()
        ctx.invoke(stop)
        time.sleep(2)

    print_info("Starting server...")
    ctx = click.get_current_context()
    ctx.invoke(start)
