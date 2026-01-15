"""Project management commands."""

import asyncio
import click

from scanner_v2.cli.utils import (
    api_request,
    print_error,
    print_success,
    print_info,
    format_project_table,
    format_project_detail,
    console
)


@click.group()
def project():
    """Project management commands."""
    pass


@project.command()
@click.option("--search", "-s", help="Search by name or URL")
@click.option("--limit", default=50, help="Number of projects to show")
def list(search: str, limit: int):
    """List all projects."""
    async def do_list():
        try:
            params = {"limit": limit}
            if search:
                params["search"] = search

            response = await api_request("GET", "/projects/", params=params)

            if response.status_code == 200:
                data = response.json()
                projects = data.get("projects", [])
                total = data.get("total", 0)

                if not projects:
                    print_info("No projects found")
                    return

                table = format_project_table(projects)
                console.print(table)
                print_info(f"Showing {len(projects)} of {total} projects")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to list projects: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to list projects: {e}")

    asyncio.run(do_list())


@project.command()
@click.argument("name")
@click.argument("url")
@click.option("--description", "-d", help="Project description")
@click.option("--max-depth", type=int, default=3, help="Maximum crawl depth")
@click.option("--max-pages", type=int, default=100, help="Maximum pages to scan")
def create(name: str, url: str, description: str, max_depth: int, max_pages: int):
    """Create a new project."""
    async def do_create():
        try:
            data = {
                "name": name,
                "base_url": url,
                "settings": {
                    "max_depth": max_depth,
                    "max_pages": max_pages
                }
            }

            if description:
                data["description"] = description

            response = await api_request("POST", "/projects/", data=data)

            if response.status_code == 201:
                project = response.json()
                print_success(f"Project created: {project['id']}")
                panel = format_project_detail(project)
                console.print(panel)
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                error_data = response.json()
                print_error(f"Failed to create project: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print_error(f"Failed to create project: {e}")

    asyncio.run(do_create())


@project.command()
@click.argument("project_id")
def show(project_id: str):
    """Show project details."""
    async def do_show():
        try:
            response = await api_request("GET", f"/projects/{project_id}")

            if response.status_code == 200:
                project = response.json()
                panel = format_project_detail(project)
                console.print(panel)
            elif response.status_code == 404:
                print_error(f"Project not found: {project_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to get project: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to get project: {e}")

    asyncio.run(do_show())


@project.command()
@click.argument("project_id")
@click.option("--name", help="New project name")
@click.option("--url", help="New base URL")
@click.option("--description", help="New description")
def update(project_id: str, name: str, url: str, description: str):
    """Update project."""
    async def do_update():
        try:
            data = {}
            if name:
                data["name"] = name
            if url:
                data["base_url"] = url
            if description:
                data["description"] = description

            if not data:
                print_error("No updates specified")
                print_info("Use --name, --url, or --description to specify updates")
                return

            response = await api_request("PUT", f"/projects/{project_id}", data=data)

            if response.status_code == 200:
                project = response.json()
                print_success("Project updated successfully")
                panel = format_project_detail(project)
                console.print(panel)
            elif response.status_code == 404:
                print_error(f"Project not found: {project_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                error_data = response.json()
                print_error(f"Failed to update project: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print_error(f"Failed to update project: {e}")

    asyncio.run(do_update())


@project.command()
@click.argument("project_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(project_id: str, yes: bool):
    """Delete a project."""
    async def do_delete():
        try:
            if not yes:
                confirm = click.confirm(f"Are you sure you want to delete project {project_id}?")
                if not confirm:
                    print_info("Cancelled")
                    return

            response = await api_request("DELETE", f"/projects/{project_id}")

            if response.status_code == 204:
                print_success(f"Project deleted: {project_id}")
            elif response.status_code == 404:
                print_error(f"Project not found: {project_id}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login first")
            else:
                print_error(f"Failed to delete project: {response.status_code}")
        except Exception as e:
            print_error(f"Failed to delete project: {e}")

    asyncio.run(do_delete())
