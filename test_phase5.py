#!/usr/bin/env python3
"""Test script for Phase 5: FastAPI Application."""

import asyncio
import httpx
import sys
from pathlib import Path

# Add scanner_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner_v2.utils.logger import setup_logging

logger = setup_logging(level="INFO", format_type="standard")

BASE_URL = "http://localhost:8000/api/v1"

# Test data
test_user = {
    "email": "test@example.com",
    "password": "TestPassword123",
    "name": "Test User"
}

test_project = {
    "name": "Test Website",
    "base_url": "https://example.com",
    "description": "A test project for Phase 5"
}


async def test_health_check():
    """Test health check endpoint."""
    logger.info("=" * 60)
    logger.info("Testing Health Check")
    logger.info("=" * 60)

    async with httpx.AsyncClient() as client:
        # Basic health check
        logger.info("\n1. Basic health check...")
        response = await client.get(f"{BASE_URL}/health/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy"
        logger.info(f"✓ Health check: {data}")

        # System status
        logger.info("\n2. System status...")
        response = await client.get(f"{BASE_URL}/health/status")
        assert response.status_code == 200
        data = response.json()
        logger.info(f"✓ System status: {data['status']}")
        logger.info(f"  Database: {data['components']['database']['status']}")
        logger.info(f"  Queue: {data['components']['queue']['status']}")


async def test_auth():
    """Test authentication endpoints."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Authentication")
    logger.info("=" * 60)

    async with httpx.AsyncClient() as client:
        # Register user
        logger.info("\n1. Registering user...")
        response = await client.post(
            f"{BASE_URL}/auth/register",
            json=test_user
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        user_data = response.json()
        logger.info(f"✓ User registered: {user_data['email']}")

        # Login
        logger.info("\n2. Logging in...")
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        assert response.status_code == 200
        login_data = response.json()
        access_token = login_data["access_token"]
        logger.info(f"✓ Logged in: {login_data['user']['email']}")
        logger.info(f"  Token: {access_token[:20]}...")

        # Get current user
        logger.info("\n3. Getting current user info...")
        response = await client.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        logger.info(f"✓ Current user: {me_data['email']}")

        return access_token, user_data["id"]


async def test_projects(access_token: str):
    """Test project endpoints."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Projects")
    logger.info("=" * 60)

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create project
        logger.info("\n1. Creating project...")
        response = await client.post(
            f"{BASE_URL}/projects/",
            json=test_project,
            headers=headers
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        project_data = response.json()
        project_id = project_data["id"]
        logger.info(f"✓ Project created: {project_id}")
        logger.info(f"  Name: {project_data['name']}")
        logger.info(f"  URL: {project_data['base_url']}")

        # Get project
        logger.info("\n2. Getting project...")
        response = await client.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=headers
        )
        assert response.status_code == 200
        logger.info(f"✓ Project retrieved: {response.json()['name']}")

        # List projects
        logger.info("\n3. Listing projects...")
        response = await client.get(
            f"{BASE_URL}/projects/",
            headers=headers
        )
        assert response.status_code == 200
        projects_data = response.json()
        logger.info(f"✓ Found {projects_data['total']} projects")

        # Update project
        logger.info("\n4. Updating project...")
        response = await client.put(
            f"{BASE_URL}/projects/{project_id}",
            json={"description": "Updated description"},
            headers=headers
        )
        assert response.status_code == 200
        updated_data = response.json()
        logger.info(f"✓ Project updated: {updated_data['description']}")

        # Search projects
        logger.info("\n5. Searching projects...")
        response = await client.get(
            f"{BASE_URL}/projects/?search=example",
            headers=headers
        )
        assert response.status_code == 200
        search_data = response.json()
        logger.info(f"✓ Search found {search_data['total']} projects")

        return project_id


async def test_scans(access_token: str, project_id: str):
    """Test scan endpoints."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Scans")
    logger.info("=" * 60)

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create scan
        logger.info("\n1. Creating scan...")
        response = await client.post(
            f"{BASE_URL}/projects/{project_id}/scans",
            json={
                "scan_type": "full",
                "max_pages": 5,
                "max_depth": 1,
                "scanners": ["axe"]
            },
            headers=headers
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        scan_data = response.json()
        scan_id = scan_data["id"]
        logger.info(f"✓ Scan created: {scan_id}")
        logger.info(f"  Status: {scan_data['status']}")
        logger.info(f"  Type: {scan_data['scan_type']}")

        # Get scan
        logger.info("\n2. Getting scan...")
        response = await client.get(
            f"{BASE_URL}/scans/{scan_id}",
            headers=headers
        )
        assert response.status_code == 200
        logger.info(f"✓ Scan retrieved: {response.json()['status']}")

        # Get scan status
        logger.info("\n3. Getting scan status...")
        response = await client.get(
            f"{BASE_URL}/scans/{scan_id}/status",
            headers=headers
        )
        assert response.status_code == 200
        status_data = response.json()
        logger.info(f"✓ Scan status: {status_data['status']}")
        logger.info(f"  Progress: {status_data['progress']}")

        # List scans
        logger.info("\n4. Listing scans...")
        response = await client.get(
            f"{BASE_URL}/scans",
            headers=headers
        )
        assert response.status_code == 200
        scans_data = response.json()
        logger.info(f"✓ Found {scans_data['total']} scans")

        # Wait a bit for scan to potentially start
        logger.info("\n5. Waiting 2 seconds for scan processing...")
        await asyncio.sleep(2)

        # Check status again
        response = await client.get(
            f"{BASE_URL}/scans/{scan_id}/status",
            headers=headers
        )
        status_data = response.json()
        logger.info(f"✓ Updated status: {status_data['status']}")

        return scan_id


async def test_reports(access_token: str, scan_id: str):
    """Test report endpoints."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Reports")
    logger.info("=" * 60)

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get JSON report
        logger.info("\n1. Getting JSON report...")
        response = await client.get(
            f"{BASE_URL}/scans/{scan_id}/reports/json",
            headers=headers
        )
        assert response.status_code == 200
        report_data = response.json()
        logger.info(f"✓ JSON report generated")
        logger.info(f"  Scan ID: {report_data['scan']['id']}")
        logger.info(f"  Project: {report_data['project']['name']}")
        logger.info(f"  Total pages: {report_data['summary']['total_pages']}")
        logger.info(f"  Total issues: {report_data['summary']['total_issues']}")


async def test_cleanup(access_token: str, scan_id: str, project_id: str, user_email: str):
    """Cleanup test data."""
    logger.info("\n" + "=" * 60)
    logger.info("Cleaning up test data...")
    logger.info("=" * 60)

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}

        # Delete scan
        logger.info("\n1. Deleting scan...")
        response = await client.delete(
            f"{BASE_URL}/scans/{scan_id}",
            headers=headers
        )
        assert response.status_code == 204
        logger.info(f"✓ Scan deleted")

        # Delete project
        logger.info("\n2. Deleting project...")
        response = await client.delete(
            f"{BASE_URL}/projects/{project_id}",
            headers=headers
        )
        assert response.status_code == 204
        logger.info(f"✓ Project deleted")

        # Note: User deletion not implemented in API (would need admin endpoint)
        logger.info(f"\n  Note: User {user_email} should be manually deleted from database")


async def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("PHASE 5 TEST: FastAPI Application")
    logger.info("=" * 60)
    logger.info("\nMake sure the API server is running:")
    logger.info("  python main_v2.py")
    logger.info("\nStarting tests in 3 seconds...\n")
    await asyncio.sleep(3)

    try:
        # Test health
        await test_health_check()

        # Test auth
        access_token, user_id = await test_auth()

        # Test projects
        project_id = await test_projects(access_token)

        # Test scans
        scan_id = await test_scans(access_token, project_id)

        # Test reports
        await test_reports(access_token, scan_id)

        # Cleanup
        await test_cleanup(access_token, scan_id, project_id, test_user["email"])

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 5 TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("\nPhase 5 Complete - FastAPI application is working!")
        logger.info("\nWhat's been tested:")
        logger.info("  ✓ Health check endpoints")
        logger.info("  ✓ User registration and authentication")
        logger.info("  ✓ JWT token generation and validation")
        logger.info("  ✓ Project CRUD operations")
        logger.info("  ✓ Scan creation and management")
        logger.info("  ✓ Scan status tracking")
        logger.info("  ✓ JSON report generation")
        logger.info("\nNext: Phase 6 - CLI Commands")

    except AssertionError as e:
        logger.error(f"\n✗ Test failed: {e}")
        raise
    except httpx.ConnectError:
        logger.error("\n✗ Cannot connect to API server!")
        logger.error("Make sure the server is running: python main_v2.py")
        raise
    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
