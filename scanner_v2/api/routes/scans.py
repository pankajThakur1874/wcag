"""Scan operation routes."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from scanner_v2.api.dependencies import (
    get_project_repository,
    get_scan_repository,
    get_page_repository,
    get_issue_repository,
    get_current_active_user,
    get_queue_manager
)
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.repositories.scan_repo import ScanRepository
from scanner_v2.database.repositories.page_repo import PageRepository
from scanner_v2.database.repositories.issue_repo import IssueRepository
from scanner_v2.database.models import User, ScanStatus, ScanConfig, ScanType
from scanner_v2.workers.queue_manager import QueueManager
from scanner_v2.schemas.scan import ScanCreateRequest, ScanResponse, ScanListResponse, JobType, JobPriority
from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import ProjectNotFoundException, ScanNotFoundException

logger = get_logger("api.routes.scans")

router = APIRouter(tags=["Scans"])


@router.post("/projects/{project_id}/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    project_id: str,
    request: ScanCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    queue_manager: Annotated[QueueManager, Depends(get_queue_manager)]
):
    """
    Create and enqueue a new scan.

    Args:
        project_id: Project ID
        request: Scan creation request
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        queue_manager: Queue manager

    Returns:
        Created scan

    Raises:
        HTTPException: If project not found or access denied
    """
    # Check project ownership
    try:
        project = await project_repo.get_by_id(project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )

    # Create scan config
    config = ScanConfig(
        scanners=request.scanners or ["axe"],
        max_depth=request.max_depth or project.settings.max_depth,
        max_pages=request.max_pages or project.settings.max_pages,
        exclude_patterns=request.exclude_patterns or project.settings.exclude_patterns,
        include_patterns=request.include_patterns or project.settings.include_patterns,
        viewport=request.viewport or project.settings.viewport,
        wait_time=request.wait_time or project.settings.wait_time,
        wcag_level=request.wcag_level or project.settings.wcag_level,
        screenshot_enabled=request.screenshot_enabled if request.screenshot_enabled is not None else True
    )

    # Create scan
    scan = await scan_repo.create(
        project_id=project_id,
        scan_type=request.scan_type or ScanType.FULL,
        config=config
    )

    # Enqueue scan job
    job_id = await queue_manager.enqueue_job(
        job_type=JobType.SCAN_ORCHESTRATION,
        payload={
            "scan_id": scan.id,
            "project_id": project_id,
            "base_url": project.base_url,
            "config": {
                "scanners": config.scanners,
                "max_depth": config.max_depth,
                "max_pages": config.max_pages,
                "exclude_patterns": config.exclude_patterns,
                "include_patterns": config.include_patterns,
                "viewport": config.viewport,
                "wait_time": config.wait_time,
                "wcag_level": config.wcag_level.value,
                "screenshot_enabled": config.screenshot_enabled
            }
        },
        priority=JobPriority.NORMAL.value
    )

    logger.info(f"Scan created and enqueued: {scan.id} for project {project_id}, job: {job_id}")

    return ScanResponse(
        id=scan.id,
        project_id=scan.project_id,
        scan_type=scan.scan_type,
        status=scan.status,
        config=scan.config,
        progress=scan.progress,
        summary=scan.summary,
        scores=scan.scores,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
        updated_at=scan.updated_at
    )


@router.get("/scans", response_model=ScanListResponse)
async def list_scans(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status_filter: Optional[ScanStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List scans.

    Args:
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        project_id: Optional project ID filter
        status_filter: Optional status filter
        skip: Number to skip
        limit: Maximum to return

    Returns:
        List of scans with pagination
    """
    if project_id:
        # Check project ownership
        try:
            project = await project_repo.get_by_id(project_id)
        except ProjectNotFoundException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if project.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project"
            )

        scans, total = await scan_repo.get_by_project(project_id, skip=skip, limit=limit)
    elif status_filter:
        # Get scans by status (need to filter by user projects)
        all_scans = await scan_repo.get_by_status(status_filter, limit=1000)
        user_projects, _ = await project_repo.get_by_user(current_user.id, limit=1000)
        user_project_ids = {p.id for p in user_projects}

        scans = [s for s in all_scans if s.project_id in user_project_ids]
        total = len(scans)
        scans = scans[skip:skip+limit]
    else:
        # Get recent scans for user
        recent_scans = await scan_repo.get_recent_scans(limit=1000)
        user_projects, _ = await project_repo.get_by_user(current_user.id, limit=1000)
        user_project_ids = {p.id for p in user_projects}

        scans = [s for s in recent_scans if s.project_id in user_project_ids]
        total = len(scans)
        scans = scans[skip:skip+limit]

    return ScanListResponse(
        scans=[
            ScanResponse(
                id=s.id,
                project_id=s.project_id,
                scan_type=s.scan_type,
                status=s.status,
                config=s.config,
                progress=s.progress,
                summary=s.summary,
                scores=s.scores,
                started_at=s.started_at,
                completed_at=s.completed_at,
                error_message=s.error_message,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in scans
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)]
):
    """
    Get scan details.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository

    Returns:
        Scan details

    Raises:
        HTTPException: If scan not found or access denied
    """
    try:
        scan = await scan_repo.get_by_id(scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {scan_id}"
        )

    # Check project ownership
    try:
        project = await project_repo.get_by_id(scan.project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {scan.project_id}"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan"
        )

    return ScanResponse(
        id=scan.id,
        project_id=scan.project_id,
        scan_type=scan.scan_type,
        status=scan.status,
        config=scan.config,
        progress=scan.progress,
        summary=scan.summary,
        scores=scan.scores,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
        updated_at=scan.updated_at
    )


@router.get("/scans/{scan_id}/status")
async def get_scan_status(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)]
):
    """
    Get real-time scan status.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository

    Returns:
        Scan status and progress

    Raises:
        HTTPException: If scan not found or access denied
    """
    try:
        scan = await scan_repo.get_by_id(scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {scan_id}"
        )

    # Check project ownership
    try:
        project = await project_repo.get_by_id(scan.project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {scan.project_id}"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan"
        )

    return {
        "scan_id": scan.id,
        "status": scan.status.value,
        "progress": {
            "total_pages": scan.progress.total_pages if scan.progress else 0,
            "pages_crawled": scan.progress.pages_crawled if scan.progress else 0,
            "pages_scanned": scan.progress.pages_scanned if scan.progress else 0,
            "current_page": scan.progress.current_page if scan.progress else None
        },
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "error_message": scan.error_message
    }


@router.post("/scans/{scan_id}/cancel")
async def cancel_scan(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)]
):
    """
    Cancel a running scan.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: If scan not found, access denied, or cannot be cancelled
    """
    try:
        scan = await scan_repo.get_by_id(scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {scan_id}"
        )

    # Check project ownership
    try:
        project = await project_repo.get_by_id(scan.project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {scan.project_id}"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan"
        )

    # Check if scan can be cancelled
    if scan.status not in [ScanStatus.QUEUED, ScanStatus.SCANNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel scan with status: {scan.status.value}"
        )

    # Update status to cancelled
    await scan_repo.update_status(scan_id, ScanStatus.CANCELLED)

    logger.info(f"Scan cancelled: {scan_id} by user {current_user.email}")

    return {
        "message": "Scan cancelled successfully",
        "scan_id": scan_id
    }


@router.delete("/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    page_repo: Annotated[PageRepository, Depends(get_page_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)]
):
    """
    Delete scan and all related data.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        page_repo: Page repository
        issue_repo: Issue repository

    Raises:
        HTTPException: If scan not found or access denied
    """
    try:
        scan = await scan_repo.get_by_id(scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {scan_id}"
        )

    # Check project ownership
    try:
        project = await project_repo.get_by_id(scan.project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {scan.project_id}"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan"
        )

    # Delete related data
    await issue_repo.delete_by_scan(scan_id)
    await page_repo.delete_by_scan(scan_id)
    await scan_repo.delete(scan_id)

    logger.info(f"Scan deleted: {scan_id} by user {current_user.email}")
