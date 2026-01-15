"""Issue management routes."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from scanner_v2.api.dependencies import (
    get_project_repository,
    get_scan_repository,
    get_issue_repository,
    get_current_active_user
)
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.repositories.scan_repo import ScanRepository
from scanner_v2.database.repositories.issue_repo import IssueRepository
from scanner_v2.database.models import User, ImpactLevel, WCAGLevel, Principle, IssueStatus
from scanner_v2.schemas.issue import IssueResponse, IssueListResponse, IssueUpdateRequest
from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import ProjectNotFoundException, ScanNotFoundException, IssueNotFoundException

logger = get_logger("api.routes.issues")

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("/", response_model=IssueListResponse)
async def list_issues(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)],
    scan_id: str = Query(..., description="Scan ID to filter by"),
    impact: Optional[ImpactLevel] = Query(None, description="Filter by impact level"),
    wcag_level: Optional[WCAGLevel] = Query(None, description="Filter by WCAG level"),
    principle: Optional[Principle] = Query(None, description="Filter by WCAG principle"),
    status_filter: Optional[IssueStatus] = Query(None, description="Filter by status"),
    manual_review_required: Optional[bool] = Query(None, description="Filter by manual review flag"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    List issues with filters.

    Args:
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        issue_repo: Issue repository
        scan_id: Scan ID
        impact: Optional impact filter
        wcag_level: Optional WCAG level filter
        principle: Optional principle filter
        status_filter: Optional status filter
        manual_review_required: Optional manual review filter
        skip: Number to skip
        limit: Maximum to return

    Returns:
        List of issues with pagination

    Raises:
        HTTPException: If scan not found or access denied
    """
    # Check scan ownership
    try:
        scan = await scan_repo.get_by_id(scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {scan_id}"
        )

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

    # Build filters
    filters = {}
    if impact:
        filters["impact"] = impact.value
    if wcag_level:
        filters["wcag_level"] = wcag_level.value
    if principle:
        filters["principle"] = principle.value
    if status_filter:
        filters["status"] = status_filter.value
    if manual_review_required is not None:
        filters["manual_review_required"] = manual_review_required

    # Get issues
    issues, total = await issue_repo.get_by_scan(
        scan_id=scan_id,
        skip=skip,
        limit=limit,
        filters=filters if filters else None
    )

    return IssueListResponse(
        issues=[
            IssueResponse(
                id=i.id,
                scan_id=i.scan_id,
                page_id=i.page_id,
                wcag_criteria=i.wcag_criteria,
                wcag_level=i.wcag_level,
                principle=i.principle,
                impact=i.impact,
                rule_id=i.rule_id,
                description=i.description,
                help_text=i.help_text,
                help_url=i.help_url,
                detected_by=i.detected_by,
                instances=i.instances,
                status=i.status,
                manual_review_required=i.manual_review_required,
                fix_suggestion=i.fix_suggestion,
                notes=i.notes,
                created_at=i.created_at
            )
            for i in issues
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)]
):
    """
    Get issue details.

    Args:
        issue_id: Issue ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        issue_repo: Issue repository

    Returns:
        Issue details

    Raises:
        HTTPException: If issue not found or access denied
    """
    try:
        issue = await issue_repo.get_by_id(issue_id)
    except IssueNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue not found: {issue_id}"
        )

    # Check scan ownership
    try:
        scan = await scan_repo.get_by_id(issue.scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {issue.scan_id}"
        )

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
            detail="Access denied to this issue"
        )

    return IssueResponse(
        id=issue.id,
        scan_id=issue.scan_id,
        page_id=issue.page_id,
        wcag_criteria=issue.wcag_criteria,
        wcag_level=issue.wcag_level,
        principle=issue.principle,
        impact=issue.impact,
        rule_id=issue.rule_id,
        description=issue.description,
        help_text=issue.help_text,
        help_url=issue.help_url,
        detected_by=issue.detected_by,
        instances=issue.instances,
        status=issue.status,
        manual_review_required=issue.manual_review_required,
        fix_suggestion=issue.fix_suggestion,
        notes=issue.notes,
        created_at=issue.created_at
    )


@router.put("/{issue_id}/status", response_model=IssueResponse)
async def update_issue_status(
    issue_id: str,
    request: IssueUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)]
):
    """
    Update issue status.

    Args:
        issue_id: Issue ID
        request: Update request
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        issue_repo: Issue repository

    Returns:
        Updated issue

    Raises:
        HTTPException: If issue not found or access denied
    """
    try:
        issue = await issue_repo.get_by_id(issue_id)
    except IssueNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue not found: {issue_id}"
        )

    # Check scan ownership
    try:
        scan = await scan_repo.get_by_id(issue.scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {issue.scan_id}"
        )

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
            detail="Access denied to this issue"
        )

    # Update status
    updated_issue = await issue_repo.update_status(
        issue_id=issue_id,
        status=request.status,
        notes=request.notes
    )

    logger.info(f"Issue status updated: {issue_id} -> {request.status.value} by user {current_user.email}")

    return IssueResponse(
        id=updated_issue.id,
        scan_id=updated_issue.scan_id,
        page_id=updated_issue.page_id,
        wcag_criteria=updated_issue.wcag_criteria,
        wcag_level=updated_issue.wcag_level,
        principle=updated_issue.principle,
        impact=updated_issue.impact,
        rule_id=updated_issue.rule_id,
        description=updated_issue.description,
        help_text=updated_issue.help_text,
        help_url=updated_issue.help_url,
        detected_by=updated_issue.detected_by,
        instances=updated_issue.instances,
        status=updated_issue.status,
        manual_review_required=updated_issue.manual_review_required,
        fix_suggestion=updated_issue.fix_suggestion,
        notes=updated_issue.notes,
        created_at=updated_issue.created_at
    )


@router.get("/scans/{scan_id}/summary")
async def get_issue_summary(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)]
):
    """
    Get issue summary for a scan.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        issue_repo: Issue repository

    Returns:
        Issue summary statistics

    Raises:
        HTTPException: If scan not found or access denied
    """
    # Check scan ownership
    try:
        scan = await scan_repo.get_by_id(scan_id)
    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan not found: {scan_id}"
        )

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

    # Get summary
    summary = await issue_repo.get_summary_by_scan(scan_id)

    return summary
