"""Reports API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse
import math
from urllib.parse import urlparse
from datetime import datetime

from wcag_backend.schemas.report import ReportListItemResponse
from wcag_backend.schemas.common import PaginatedResponse, PaginationMetadata
from wcag_backend.database.repositories.scan_repo import ScanRepository
from wcag_backend.database.repositories.issue_repo import IssueRepository
from wcag_backend.core.report_generator import ReportGenerator
from wcag_backend.api.dependencies import CurrentUser
from wcag_backend.utils.exceptions import ScanNotFoundException
from motor.motor_asyncio import AsyncIOMotorDatabase
from wcag_backend.database.connection import get_db


router = APIRouter(prefix="/reports", tags=["Reports"])


def get_scan_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> ScanRepository:
    """Get scan repository instance."""
    return ScanRepository(db)


def get_issue_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> IssueRepository:
    """Get issue repository instance."""
    return IssueRepository(db)


@router.get("", response_model=PaginatedResponse[ReportListItemResponse])
async def list_reports(
    current_user: CurrentUser,
    scan_repo: ScanRepository = Depends(get_scan_repository),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    projectId: Optional[str] = Query(None, alias="projectId")
):
    """
    List reports (completed scans).

    Reports are scans with status=completed. Used by:
    - Reports page table
    - Issues page "Select Report" dropdown

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - projectId: Filter by project
    """
    # Get completed scans only
    scans, total_count = await scan_repo.list_with_filters(
        user_id=current_user.id,
        project_id=projectId,
        status="completed",
        page=page,
        limit=limit
    )

    # Convert to report format (same as scan for now)
    reports = []
    for scan in scans:
        reports.append({
            "id": scan["id"],
            "scanId": scan["id"],
            "projectId": scan.get("projectId"),
            "projectName": scan.get("projectName"),
            "url": scan["url"],
            "type": scan["type"],
            "score": scan.get("score"),
            "issuesCount": scan.get("issuesCount", 0),
            "status": scan["status"],
            "createdAt": scan["createdAt"],
            "completedAt": scan.get("completedAt")  # Fixed: use camelCase
        })

    # Calculate pagination
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    return PaginatedResponse(
        success=True,
        data=reports,
        pagination=PaginationMetadata(
            page=page,
            limit=limit,
            totalPages=total_pages,
            totalItems=total_count
        )
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: CurrentUser,
    format: str = Query("html", pattern="^(html|json|csv)$"),
    scan_repo: ScanRepository = Depends(get_scan_repository),
    issue_repo: IssueRepository = Depends(get_issue_repository)
):
    """
    Download report in specified format.

    Query Parameters:
    - format: Report format (html, json, csv) - default: html

    Returns file for download with appropriate Content-Type and Content-Disposition headers.
    """
    try:
        # Get scan (verify ownership)
        scan = await scan_repo.get_by_id(report_id)
        if scan.get("user_id") != current_user.id:
            raise ScanNotFoundException(report_id)

        # Check if scan is completed
        if scan.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "SCAN_NOT_COMPLETED",
                        "message": f"Scan not completed. Status: {scan.get('status')}"
                    }
                }
            )

        # Get all issues for this scan
        issues, _ = await issue_repo.list_with_filters(
            scan_id=report_id,
            page=1,
            limit=10000  # Get all issues
        )

        # Generate report
        generator = ReportGenerator()

        # Extract domain from URL for filename
        try:
            domain = urlparse(scan.get("url", "")).netloc.replace(".", "_")
        except:
            domain = "report"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "html":
            content = generator.generate_html(scan, issues)
            filename = f"wcag_report_{domain}_{timestamp}.html"
            media_type = "text/html"

        elif format == "json":
            content = generator.generate_json(scan, issues)
            filename = f"wcag_report_{domain}_{timestamp}.json"
            media_type = "application/json"

        else:  # csv
            content = generator.generate_csv(issues)
            filename = f"wcag_report_{domain}_{timestamp}.csv"
            media_type = "text/csv"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ScanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Report not found."
                }
            }
        )
