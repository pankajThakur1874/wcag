"""Issues API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
import math

from wcag_backend.schemas.issue import (
    UpdateIssueStatusRequest,
    IssueResponse,
    IssueStatusUpdateResponse
)
from wcag_backend.schemas.common import PaginatedResponse, PaginationMetadata
from wcag_backend.database.repositories.issue_repo import IssueRepository
from wcag_backend.database.repositories.scan_repo import ScanRepository
from wcag_backend.api.dependencies import CurrentUser
from wcag_backend.utils.exceptions import IssueNotFoundException, ScanNotFoundException
from motor.motor_asyncio import AsyncIOMotorDatabase
from wcag_backend.database.connection import get_db


router = APIRouter(tags=["Issues"])


def get_issue_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> IssueRepository:
    """Get issue repository instance."""
    return IssueRepository(db)


def get_scan_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> ScanRepository:
    """Get scan repository instance."""
    return ScanRepository(db)


@router.get("/scans/{scan_id}/issues", response_model=PaginatedResponse[IssueResponse])
async def list_issues(
    scan_id: str = Path(..., alias="scan_id"),
    current_user: CurrentUser = Depends(),
    issue_repo: IssueRepository = Depends(get_issue_repository),
    scan_repo: ScanRepository = Depends(get_scan_repository),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    impact: Optional[str] = Query(None, pattern="^(critical|serious|moderate|minor)$"),
    status: Optional[str] = Query(None, pattern="^(open|fixed|ignored)$")
):
    """
    List issues for a scan with pagination and filtering.

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - impact: Filter by impact level (critical, serious, moderate, minor)
    - status: Filter by status (open, fixed, ignored)
    """
    try:
        # Verify scan exists and user owns it
        scan = await scan_repo.get_by_id(scan_id)
        if scan.get("user_id") != current_user.id:
            raise ScanNotFoundException(scan_id)

        # Get issues
        issues, total_count = await issue_repo.list_with_filters(
            scan_id=scan_id,
            impact=impact,
            status=status,
            page=page,
            limit=limit
        )

        # Calculate pagination
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

        return PaginatedResponse(
            success=True,
            data=issues,
            pagination=PaginationMetadata(
                page=page,
                limit=limit,
                totalPages=total_pages,
                totalItems=total_count
            )
        )

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


@router.patch("/issues/{issue_id}", response_model=IssueStatusUpdateResponse)
async def update_issue_status(
    issue_id: str,
    request: UpdateIssueStatusRequest,
    current_user: CurrentUser,
    issue_repo: IssueRepository = Depends(get_issue_repository)
):
    """
    Update issue status.

    Allows changing status to: open, fixed, or ignored.
    """
    try:
        updated_issue = await issue_repo.update_status(
            issue_id=issue_id,
            new_status=request.status,
            user_id=current_user.id
        )

        return IssueStatusUpdateResponse(
            success=True,
            data=updated_issue
        )

    except IssueNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Issue not found."
                }
            }
        )
