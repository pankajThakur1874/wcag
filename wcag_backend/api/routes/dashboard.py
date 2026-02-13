"""Dashboard API routes."""

from fastapi import APIRouter, Depends, Query
import math

from wcag_backend.schemas.dashboard import (
    DashboardStatsResponse,
    DashboardStatsSuccessResponse,
    IssuesByImpactResponse,
    ScannedPageResponse
)
from wcag_backend.schemas.common import PaginatedResponse, PaginationMetadata
from wcag_backend.database.repositories.scan_repo import ScanRepository
from wcag_backend.database.repositories.project_repo import ProjectRepository
from wcag_backend.database.repositories.issue_repo import IssueRepository
from wcag_backend.api.dependencies import CurrentUser
from motor.motor_asyncio import AsyncIOMotorDatabase
from wcag_backend.database.connection import get_db


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_scan_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> ScanRepository:
    """Get scan repository instance."""
    return ScanRepository(db)


def get_project_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> ProjectRepository:
    """Get project repository instance."""
    return ProjectRepository(db)


def get_issue_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> IssueRepository:
    """Get issue repository instance."""
    return IssueRepository(db)


@router.get("/stats", response_model=DashboardStatsSuccessResponse)
async def get_dashboard_stats(
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    issue_repo: IssueRepository = Depends(get_issue_repository)
):
    """
    Get dashboard statistics.

    Returns:
    - Total completed scans
    - Number of active projects
    - Count of open critical issues
    - Average scan score
    - Issues grouped by impact level
    """
    # Get total scans (completed only)
    total_scans = await scan_repo.count_by_user(
        user_id=current_user.id,
        status="completed"
    )

    # Get active projects count
    active_projects = await project_repo.count_by_user(
        user_id=current_user.id,
        status="active"
    )

    # Get critical issues count (open only)
    critical_issues = await issue_repo.count_by_user(
        user_id=current_user.id,
        impact="critical",
        status="open"
    )

    # Get average score
    avg_score = await scan_repo.average_score_by_user(user_id=current_user.id)

    # Get issues by impact
    issues_by_impact = await issue_repo.count_by_impact(user_id=current_user.id)

    # Build response
    stats = DashboardStatsResponse(
        totalScans=total_scans,
        activeProjects=active_projects,
        criticalIssues=critical_issues,
        avgScore=avg_score,
        issuesByImpact=IssuesByImpactResponse(**issues_by_impact)
    )

    return DashboardStatsSuccessResponse(success=True, data=stats)


@router.get("/pages", response_model=PaginatedResponse[ScannedPageResponse])
async def get_scanned_pages(
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("-createdAt", pattern="^-?(createdAt|score)$")
):
    """
    Get all scanned pages with pagination.

    This is used by the "All Scanned Pages" table on the dashboard.

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - sort: Sort field (createdAt, score; prefix with - for descending)
    """
    # Get scans (all statuses)
    scans, total_count = await scan_repo.list_with_filters(
        user_id=current_user.id,
        page=page,
        limit=limit
    )

    # Convert to scanned page response
    scanned_pages = []
    for scan in scans:
        scanned_pages.append({
            "id": scan["id"],
            "url": scan["url"],
            "projectName": scan.get("projectName"),
            "score": scan.get("score"),
            "issuesCount": scan.get("issuesCount", 0),
            "lastScanned": scan["createdAt"],
            "status": scan["status"]
        })

    # Calculate pagination
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    return PaginatedResponse(
        success=True,
        data=scanned_pages,
        pagination=PaginationMetadata(
            page=page,
            limit=limit,
            totalPages=total_pages,
            totalItems=total_count
        )
    )
