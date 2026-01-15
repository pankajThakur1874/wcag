"""Authentication commands."""

import asyncio
import click
from rich.prompt import Prompt

from scanner_v2.cli.utils import (
    api_request,
    save_token,
    clear_token,
    print_error,
    print_success,
    print_info
)


@click.group()
def auth():
    """Authentication commands."""
    pass


@auth.command()
@click.option("--email", prompt=True, help="Email address")
@click.option("--password", prompt=True, hide_input=True, help="Password")
@click.option("--name", prompt=True, help="Full name")
def register(email: str, password: str, name: str):
    """Register a new user."""
    async def do_register():
        try:
            response = await api_request(
                "POST",
                "/auth/register",
                data={
                    "email": email,
                    "password": password,
                    "name": name
                }
            )

            if response.status_code == 201:
                user_data = response.json()
                print_success(f"User registered successfully: {user_data['email']}")
                print_info("You can now login with: wcag-v2 auth login")
            else:
                error_data = response.json()
                print_error(f"Registration failed: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print_error(f"Registration failed: {e}")

    asyncio.run(do_register())


@auth.command()
@click.option("--email", prompt=True, help="Email address")
@click.option("--password", prompt=True, hide_input=True, help="Password")
def login(email: str, password: str):
    """Login and save authentication token."""
    async def do_login():
        try:
            response = await api_request(
                "POST",
                "/auth/login",
                data={
                    "email": email,
                    "password": password
                }
            )

            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                user = data["user"]

                # Save token
                save_token(token)

                print_success(f"Logged in as: {user['email']}")
                print_info("Token saved to ~/.wcag-scanner/config.json")
            else:
                error_data = response.json()
                print_error(f"Login failed: {error_data.get('detail', 'Invalid credentials')}")
        except Exception as e:
            print_error(f"Login failed: {e}")

    asyncio.run(do_login())


@auth.command()
def logout():
    """Logout and clear authentication token."""
    clear_token()
    print_success("Logged out successfully")
    print_info("Token cleared from ~/.wcag-scanner/config.json")


@auth.command()
def whoami():
    """Show current authenticated user."""
    async def do_whoami():
        try:
            response = await api_request("GET", "/auth/me")

            if response.status_code == 200:
                user = response.json()
                print_info(f"Logged in as: {user['email']}")
                print_info(f"Name: {user.get('name', 'N/A')}")
                print_info(f"Role: {user.get('role', 'user')}")
            elif response.status_code == 401:
                print_error("Not authenticated")
                print_info("Use 'wcag-v2 auth login' to login")
            else:
                print_error("Failed to get user info")
        except Exception as e:
            print_error(f"Failed to get user info: {e}")

    asyncio.run(do_whoami())
