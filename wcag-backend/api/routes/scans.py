"""Scan API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
import math

from wcag_backend.schemas.scan import (
    QuickScanRequest,
    ProjectScanRequest,
    ScanResponse,
    ScanSuccessResponse,
    ScanStatusResponse,
    ScanProgressResponse,
    ScanListItemResponse,
    ScanDetailResponse
)
from wcag_backend.schemas.common import PaginatedResponse, PaginationMetadata
from wcag_backend.database.repositories.scan_repo import ScanRepository
from wcag_backend.database.repositories.project_repo import ProjectRepository
from wcag_backend.workers.queue_manager import get_queue_manager, JobType, JobPriority
from wcag_backend.api.dependencies import CurrentUser
from wcag_backend.utils.exceptions import ScanNotFoundException, ProjectNotFoundException
from motor.motor_asyncio import AsyncIOMotorDatabase
from wcag_backend.database.connection import get_db


router = APIRouter(prefix="/scans", tags=["Scans"])


def get_scan_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> ScanRepository:
    """Get scan repository instance."""
    return ScanRepository(db)


def get_project_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> ProjectRepository:
    """Get project repository instance."""
    return ProjectRepository(db)


@router.post("/quick", response_model=ScanSuccessResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_quick_scan(
    request: QuickScanRequest,
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository)
):
    """
    Start a quick scan (single page or site-wide).

    Returns 202 Accepted with scan ID. Use /scans/:id/status to poll for results.
    """
    # Create scan record
    scan_type = "full" if request.siteWide else "quick"
    config = {
        "max_pages": request.maxPages,
        "max_depth": request.maxDepth,
        "scanners": request.scanners
    }

    scan = await scan_repo.create(
        user_id=current_user.id,
        url=str(request.url),
        scan_type=scan_type,
        config=config
    )

    # Enqueue job
    queue_manager = get_queue_manager()
    job_type = JobType.SITE_SCAN if request.siteWide else JobType.SCAN

    await queue_manager.enqueue_job(
        job_type=job_type,
        payload={
            "scan_id": scan.id,
            "url": str(request.url),
            "max_pages": request.maxPages,
            "max_depth": request.maxDepth,
            "scanners": request.scanners
        },
        priority=JobPriority.NORMAL
    )

    # Return response
    scan_response = ScanResponse(
        scanId=scan.id,
        url=scan.url,
        type=scan.type.value,
        status=scan.status.value,
        createdAt=scan.created_at
    )

    return ScanSuccessResponse(
        success=True,
        data=scan_response,
        message=f"Scan has been queued and will begin shortly."
    )


@router.post("/project", response_model=ScanSuccessResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_project_scan(
    request: ProjectScanRequest,
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository),
    project_repo: ProjectRepository = Depends(get_project_repo)
):
    """
    Start a project scan.

    Scans the project's URL with specified configuration.
    Returns 202 Accepted with scan ID.
    """
    try:
        # Verify project exists and user owns it
        project = await project_repo.get_by_id(request.projectId, current_user.id)

        # Create scan record
        config = {
            "max_pages": request.maxPages,
            "max_depth": request.maxDepth,
            "scanners": request.scanners
        }

        scan = await scan_repo.create(
            user_id=current_user.id,
            url=project.url,
            scan_type="full",
            config=config,
            project_id=project.id
        )

        # Enqueue job
        queue_manager = get_queue_manager()

        await queue_manager.enqueue_job(
            job_type=JobType.SITE_SCAN,
            payload={
                "scan_id": scan.id,
                "url": project.url,
                "max_pages": request.maxPages,
                "max_depth": request.maxDepth,
                "scanners": request.scanners
            },
            priority=JobPriority.NORMAL
        )

        # Return response
        scan_response = ScanResponse(
            scanId=scan.id,
            url=scan.url,
            type=scan.type.value,
            status=scan.status.value,
            createdAt=scan.created_at
        )

        return ScanSuccessResponse(
            success=True,
            data=scan_response,
            message="Project scan has been queued."
        )

    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Project not found."
                }
            }
        )


@router.get("/{scan_id}/status")
async def get_scan_status(
    scan_id: str,
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository)
):
    """
    Get real-time scan status and progress.

    Use this endpoint to poll for scan progress and results.
    """
    try:
        scan = await scan_repo.get_by_id(scan_id)

        # Check ownership
        if scan.get("user_id") != current_user.id:
            raise ScanNotFoundException(scan_id)

        # Return different response based on status
        if scan["status"] in ["queued", "scanning"]:
            progress = scan.get("progress", {})
            return {
                "success": True,
                "data": {
                    "scanId": scan_id,
                    "status": scan["status"],
                    "progress": {
                        "pagesScanned": progress.get("pages_scanned", 0),
                        "totalPages": progress.get("total_pages", 0),
                        "currentUrl": progress.get("current_url"),
                        "percentage": progress.get("percentage", 0)
                    },
                    "startedAt": scan.get("started_at")
                }
            }

        # Completed
        return {
            "success": True,
            "data": {
                "scanId": scan_id,
                "status": scan["status"],
                "progress": 100,
                "pagesScanned": scan.get("progress", {}).get("pages_scanned", 0),
                "totalPages": scan.get("progress", {}).get("total_pages", 0),
                "score": scan.get("score"),
                "issuesCount": scan.get("issues_count", 0),
                "duration": scan.get("duration"),
                "completedAt": scan.get("completed_at")
            }
        }

    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Scan not found."
                }
            }
        )


@router.get("", response_model=PaginatedResponse[ScanListItemResponse])
async def list_scans(
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    projectId: Optional[str] = Query(None, alias="projectId"),
    status: Optional[str] = Query(None, pattern="^(queued|scanning|completed|failed)$")
):
    """
    List scans with pagination and filtering.

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - projectId: Filter by project
    - status: Filter by status
    """
    # Get scans
    scans, total_count = await scan_repo.list_with_filters(
        user_id=current_user.id,
        project_id=projectId,
        status=status,
        page=page,
        limit=limit
    )

    # Calculate pagination
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    return PaginatedResponse(
        success=True,
        data=scans,
        pagination=PaginationMetadata(
            page=page,
            limit=limit,
            totalPages=total_pages,
            totalItems=total_count
        )
    )


@router.get("/{scan_id}")
async def get_scan(
    scan_id: str,
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository)
):
    """
    Get detailed scan information.

    Returns full scan details including configuration and results.
    """
    try:
        scan_detail = await scan_repo.get_detail(scan_id, current_user.id)

        return {
            "success": True,
            "data": scan_detail
        }

    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Scan not found."
                }
            }
        )
