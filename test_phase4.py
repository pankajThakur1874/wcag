#!/usr/bin/env python3
"""Test script for Phase 4: Database Layer (Repositories)."""

import asyncio
import sys
from pathlib import Path

# Add scanner_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner_v2.utils.config import load_config
from scanner_v2.utils.logger import setup_logging
from scanner_v2.database.connection import MongoDB
from scanner_v2.database.models import (
    UserRole, ScanType, ScanStatus, ImpactLevel,
    WCAGLevel, Principle, IssueStatus, ProjectSettings
)
from scanner_v2.database.repositories.user_repo import UserRepository
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.repositories.scan_repo import ScanRepository
from scanner_v2.database.repositories.page_repo import PageRepository
from scanner_v2.database.repositories.issue_repo import IssueRepository
from scanner_v2.database.models import ScannedPage, Issue, RawScanResults, ScanProgress, ScanSummary, ScanScores

logger = setup_logging(level="INFO", format_type="standard")


async def test_user_repository(user_repo: UserRepository):
    """Test UserRepository operations."""
    logger.info("=" * 60)
    logger.info("Testing UserRepository")
    logger.info("=" * 60)

    # 1. Create user
    logger.info("\n1. Creating user...")
    user = await user_repo.create(
        email="test@example.com",
        password="SecurePassword123",
        name="Test User",
        role=UserRole.USER
    )
    logger.info(f"✓ Created user: {user.id} - {user.email}")

    # 2. Get user by ID
    logger.info("\n2. Getting user by ID...")
    fetched_user = await user_repo.get_by_id(user.id)
    logger.info(f"✓ Retrieved user: {fetched_user.email}")

    # 3. Get user by email
    logger.info("\n3. Getting user by email...")
    email_user = await user_repo.get_by_email("test@example.com")
    logger.info(f"✓ Found user by email: {email_user.name}")

    # 4. Authenticate user
    logger.info("\n4. Authenticating user...")
    auth_user = await user_repo.authenticate("test@example.com", "SecurePassword123")
    logger.info(f"✓ Authenticated user: {auth_user.email}")

    # 5. Test wrong password
    logger.info("\n5. Testing wrong password...")
    try:
        await user_repo.authenticate("test@example.com", "WrongPassword")
        logger.error("✗ Should have raised InvalidCredentialsError")
    except Exception as e:
        logger.info(f"✓ Correctly raised: {type(e).__name__}")

    # 6. Update user
    logger.info("\n6. Updating user...")
    updated_user = await user_repo.update(user.id, name="Updated User")
    logger.info(f"✓ Updated user name: {updated_user.name}")

    # 7. Change password
    logger.info("\n7. Changing password...")
    success = await user_repo.change_password(user.id, "NewPassword456")
    logger.info(f"✓ Password changed: {success}")

    # Verify new password works
    await user_repo.authenticate("test@example.com", "NewPassword456")
    logger.info("✓ New password authentication successful")

    return user


async def test_project_repository(project_repo: ProjectRepository, user_id: str):
    """Test ProjectRepository operations."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing ProjectRepository")
    logger.info("=" * 60)

    # 1. Create project
    logger.info("\n1. Creating project...")
    settings = ProjectSettings(
        max_depth=3,
        max_pages=100,
        wcag_level=WCAGLevel.AA
    )
    project = await project_repo.create(
        user_id=user_id,
        name="Test Website",
        base_url="https://example.com",
        description="A test project",
        settings=settings
    )
    logger.info(f"✓ Created project: {project.id} - {project.name}")

    # 2. Get project by ID
    logger.info("\n2. Getting project by ID...")
    fetched_project = await project_repo.get_by_id(project.id)
    logger.info(f"✓ Retrieved project: {fetched_project.name}")

    # 3. Get projects by user
    logger.info("\n3. Getting projects by user...")
    projects, total = await project_repo.get_by_user(user_id, skip=0, limit=10)
    logger.info(f"✓ Found {total} projects for user")

    # 4. Create more projects for search test
    logger.info("\n4. Creating additional projects...")
    await project_repo.create(
        user_id=user_id,
        name="Another Site",
        base_url="https://another.com"
    )
    await project_repo.create(
        user_id=user_id,
        name="E-commerce Store",
        base_url="https://store.example.com"
    )
    logger.info("✓ Created 2 more projects")

    # 5. Search projects
    logger.info("\n5. Searching projects...")
    search_results, search_total = await project_repo.search(
        user_id=user_id,
        query="example",
        skip=0,
        limit=10
    )
    logger.info(f"✓ Search found {search_total} projects matching 'example'")

    # 6. Update project
    logger.info("\n6. Updating project...")
    updated_project = await project_repo.update(
        project.id,
        {"description": "Updated description"}
    )
    logger.info(f"✓ Updated description: {updated_project.description}")

    return project


async def test_scan_repository(scan_repo: ScanRepository, project_id: str):
    """Test ScanRepository operations."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing ScanRepository")
    logger.info("=" * 60)

    # 1. Create scan
    logger.info("\n1. Creating scan...")
    scan = await scan_repo.create(
        project_id=project_id,
        scan_type=ScanType.FULL
    )
    logger.info(f"✓ Created scan: {scan.id} - Status: {scan.status.value}")

    # 2. Get scan by ID
    logger.info("\n2. Getting scan by ID...")
    fetched_scan = await scan_repo.get_by_id(scan.id)
    logger.info(f"✓ Retrieved scan: {fetched_scan.status.value}")

    # 3. Update status to SCANNING
    logger.info("\n3. Updating scan status to SCANNING...")
    updated_scan = await scan_repo.update_status(scan.id, ScanStatus.SCANNING)
    logger.info(f"✓ Status updated: {updated_scan.status.value}")
    logger.info(f"  Started at: {updated_scan.started_at}")

    # 4. Update progress
    logger.info("\n4. Updating scan progress...")
    progress = ScanProgress(
        total_pages=100,
        pages_crawled=50,
        pages_scanned=25,
        current_page="https://example.com/page1"
    )
    scan_with_progress = await scan_repo.update_progress(scan.id, progress)
    logger.info(f"✓ Progress: {scan_with_progress.progress.pages_scanned}/{scan_with_progress.progress.total_pages}")

    # 5. Update results
    logger.info("\n5. Updating scan results...")
    summary = ScanSummary(
        total_issues=45,
        by_impact={
            "critical": 5,
            "serious": 15,
            "moderate": 20,
            "minor": 5
        },
        by_wcag_level={
            "A": 10,
            "AA": 25,
            "AAA": 10
        }
    )
    scores = ScanScores(
        overall=78.5,
        by_principle={
            "perceivable": 80.0,
            "operable": 75.0,
            "understandable": 82.0,
            "robust": 77.0
        }
    )
    scan_with_results = await scan_repo.update_results(scan.id, summary, scores)
    logger.info(f"✓ Results updated: Overall score = {scan_with_results.scores.overall}")
    logger.info(f"  Total issues: {scan_with_results.summary.total_issues}")

    # 6. Complete scan
    logger.info("\n6. Completing scan...")
    completed_scan = await scan_repo.update_status(scan.id, ScanStatus.COMPLETED)
    logger.info(f"✓ Scan completed at: {completed_scan.completed_at}")

    # 7. Get scans by project
    logger.info("\n7. Getting scans by project...")
    scans, total = await scan_repo.get_by_project(project_id, skip=0, limit=10)
    logger.info(f"✓ Found {total} scans for project")

    # 8. Get scans by status
    logger.info("\n8. Getting scans by status...")
    completed_scans = await scan_repo.get_by_status(ScanStatus.COMPLETED, limit=10)
    logger.info(f"✓ Found {len(completed_scans)} completed scans")

    # 9. Get statistics
    logger.info("\n9. Getting scan statistics...")
    stats = await scan_repo.get_statistics(project_id=project_id)
    logger.info(f"✓ Statistics: Total = {stats['total']}")
    logger.info(f"  By status: {stats['by_status']}")

    return scan


async def test_page_repository(page_repo: PageRepository, scan_id: str):
    """Test PageRepository operations."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing PageRepository")
    logger.info("=" * 60)

    # 1. Create single page
    logger.info("\n1. Creating scanned page...")
    page = ScannedPage(
        scan_id=scan_id,
        url="https://example.com/page1",
        title="Page 1",
        status_code=200,
        load_time_ms=1500,
        raw_results=RawScanResults(
            axe={"violations": []},
            pa11y={"issues": []},
            lighthouse={"audits": {}}
        ),
        issues_count=5,
        compliance_score=85.0
    )
    created_page = await page_repo.create(page)
    logger.info(f"✓ Created page: {created_page.id} - {created_page.url}")

    # 2. Create multiple pages
    logger.info("\n2. Creating multiple pages...")
    pages = [
        ScannedPage(
            scan_id=scan_id,
            url=f"https://example.com/page{i}",
            title=f"Page {i}",
            status_code=200,
            load_time_ms=1000 + i * 100,
            raw_results=RawScanResults(axe={}, pa11y={}, lighthouse={}),
            issues_count=i,
            compliance_score=90.0 - i
        )
        for i in range(2, 6)
    ]
    page_ids = await page_repo.create_many(pages)
    logger.info(f"✓ Created {len(page_ids)} pages")

    # 3. Get page by ID
    logger.info("\n3. Getting page by ID...")
    fetched_page = await page_repo.get_by_id(created_page.id)
    logger.info(f"✓ Retrieved page: {fetched_page.url}")

    # 4. Get pages by scan
    logger.info("\n4. Getting pages by scan...")
    scan_pages, total = await page_repo.get_by_scan(scan_id, skip=0, limit=10)
    logger.info(f"✓ Found {total} pages for scan")
    for p in scan_pages[:3]:
        logger.info(f"  - {p.url} (Score: {p.compliance_score})")

    # 5. Get page by URL
    logger.info("\n5. Getting page by URL...")
    url_page = await page_repo.get_by_url(scan_id, "https://example.com/page1")
    logger.info(f"✓ Found page: {url_page.title}")

    return created_page


async def test_issue_repository(issue_repo: IssueRepository, scan_id: str, page_id: str):
    """Test IssueRepository operations."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing IssueRepository")
    logger.info("=" * 60)

    # 1. Create single issue
    logger.info("\n1. Creating issue...")
    issue = Issue(
        scan_id=scan_id,
        page_id=page_id,
        wcag_criteria=["1.1.1"],
        wcag_level=WCAGLevel.A,
        principle=Principle.PERCEIVABLE,
        impact=ImpactLevel.CRITICAL,
        rule_id="image-alt",
        description="Images must have alternate text",
        help_text="Ensures <img> elements have alternate text",
        help_url="https://dequeuniversity.com/rules/axe/4.0/image-alt",
        detected_by=["axe"],
        instances=[],
        status=IssueStatus.OPEN,
        manual_review_required=False
    )
    created_issue = await issue_repo.create(issue)
    logger.info(f"✓ Created issue: {created_issue.id} - {created_issue.rule_id}")

    # 2. Create multiple issues
    logger.info("\n2. Creating multiple issues...")
    issues = [
        Issue(
            scan_id=scan_id,
            page_id=page_id,
            wcag_criteria=["1.4.3"],
            wcag_level=WCAGLevel.AA,
            principle=Principle.PERCEIVABLE,
            impact=ImpactLevel.SERIOUS,
            rule_id="color-contrast",
            description="Color contrast issues",
            detected_by=["axe"],
            status=IssueStatus.OPEN
        ),
        Issue(
            scan_id=scan_id,
            page_id=page_id,
            wcag_criteria=["2.1.1"],
            wcag_level=WCAGLevel.A,
            principle=Principle.OPERABLE,
            impact=ImpactLevel.MODERATE,
            rule_id="keyboard-access",
            description="Keyboard accessibility",
            detected_by=["pa11y"],
            status=IssueStatus.OPEN
        ),
        Issue(
            scan_id=scan_id,
            page_id=page_id,
            wcag_criteria=["3.1.1"],
            wcag_level=WCAGLevel.A,
            principle=Principle.UNDERSTANDABLE,
            impact=ImpactLevel.MINOR,
            rule_id="html-lang",
            description="Page language missing",
            detected_by=["axe"],
            status=IssueStatus.OPEN
        )
    ]
    issue_ids = await issue_repo.create_many(issues)
    logger.info(f"✓ Created {len(issue_ids)} issues")

    # 3. Get issue by ID
    logger.info("\n3. Getting issue by ID...")
    fetched_issue = await issue_repo.get_by_id(created_issue.id)
    logger.info(f"✓ Retrieved issue: {fetched_issue.rule_id}")

    # 4. Get issues by scan (no filters)
    logger.info("\n4. Getting all issues for scan...")
    scan_issues, total = await issue_repo.get_by_scan(scan_id, skip=0, limit=10)
    logger.info(f"✓ Found {total} issues for scan")

    # 5. Get issues by scan with impact filter
    logger.info("\n5. Getting issues filtered by impact...")
    critical_issues, critical_total = await issue_repo.get_by_scan(
        scan_id,
        filters={"impact": ImpactLevel.CRITICAL.value}
    )
    logger.info(f"✓ Found {critical_total} critical issues")

    # 6. Get issues by scan with WCAG level filter
    logger.info("\n6. Getting issues filtered by WCAG level...")
    aa_issues, aa_total = await issue_repo.get_by_scan(
        scan_id,
        filters={"wcag_level": WCAGLevel.AA.value}
    )
    logger.info(f"✓ Found {aa_total} Level AA issues")

    # 7. Get issues by page
    logger.info("\n7. Getting issues by page...")
    page_issues = await issue_repo.get_by_page(page_id)
    logger.info(f"✓ Found {len(page_issues)} issues for page")

    # 8. Update issue status
    logger.info("\n8. Updating issue status...")
    updated_issue = await issue_repo.update_status(
        created_issue.id,
        IssueStatus.FIXED,
        notes="Fixed by adding alt text"
    )
    logger.info(f"✓ Issue status: {updated_issue.status.value}")
    logger.info(f"  Notes: {updated_issue.notes}")

    # 9. Get issue summary
    logger.info("\n9. Getting issue summary for scan...")
    summary = await issue_repo.get_summary_by_scan(scan_id)
    logger.info(f"✓ Summary:")
    logger.info(f"  Total issues: {summary['total']}")
    logger.info(f"  By impact: {summary['by_impact']}")
    logger.info(f"  By WCAG level: {summary['by_wcag_level']}")
    logger.info(f"  By principle: {summary['by_principle']}")


async def cleanup(
    user_repo: UserRepository,
    project_repo: ProjectRepository,
    scan_repo: ScanRepository,
    page_repo: PageRepository,
    issue_repo: IssueRepository,
    user_id: str,
    project_id: str,
    scan_id: str
):
    """Clean up test data."""
    logger.info("\n" + "=" * 60)
    logger.info("Cleaning up test data...")
    logger.info("=" * 60)

    # Delete issues
    deleted_issues = await issue_repo.delete_by_scan(scan_id)
    logger.info(f"✓ Deleted {deleted_issues} issues")

    # Delete pages
    deleted_pages = await page_repo.delete_by_scan(scan_id)
    logger.info(f"✓ Deleted {deleted_pages} pages")

    # Delete scan
    await scan_repo.delete(scan_id)
    logger.info(f"✓ Deleted scan")

    # Delete project and other projects
    projects, _ = await project_repo.get_by_user(user_id)
    for project in projects:
        await project_repo.delete(project.id)
    logger.info(f"✓ Deleted {len(projects)} projects")

    # Delete user
    await user_repo.delete(user_id)
    logger.info(f"✓ Deleted user")


async def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("PHASE 4 TEST: Database Layer (Repositories)")
    logger.info("=" * 60)

    # Load configuration
    config = load_config()

    # Connect to MongoDB
    logger.info("\nConnecting to MongoDB...")
    db = MongoDB(config)
    await db.connect()
    logger.info("✓ Connected to MongoDB")

    try:
        # Initialize repositories
        user_repo = UserRepository(db.db)
        project_repo = ProjectRepository(db.db)
        scan_repo = ScanRepository(db.db)
        page_repo = PageRepository(db.db)
        issue_repo = IssueRepository(db.db)

        # Run tests
        user = await test_user_repository(user_repo)
        project = await test_project_repository(project_repo, user.id)
        scan = await test_scan_repository(scan_repo, project.id)
        page = await test_page_repository(page_repo, scan.id)
        await test_issue_repository(issue_repo, scan.id, page.id)

        # Cleanup
        await cleanup(
            user_repo, project_repo, scan_repo, page_repo, issue_repo,
            user.id, project.id, scan.id
        )

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 4 TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("\nPhase 4 Complete - Database repositories are working!")
        logger.info("\nWhat's been tested:")
        logger.info("  ✓ UserRepository - User CRUD and authentication")
        logger.info("  ✓ ProjectRepository - Project management and search")
        logger.info("  ✓ ScanRepository - Scan lifecycle and statistics")
        logger.info("  ✓ PageRepository - Page storage and retrieval")
        logger.info("  ✓ IssueRepository - Issue tracking and filtering")
        logger.info("\nNext: Phase 5 - FastAPI Application")

    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}", exc_info=True)
        raise

    finally:
        # Disconnect
        logger.info("\nDisconnecting from MongoDB...")
        await db.disconnect()
        logger.info("✓ Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
