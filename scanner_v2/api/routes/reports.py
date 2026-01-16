"""Report generation routes."""

from typing import Annotated
import csv
import io
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader

from scanner_v2.api.dependencies import (
    get_project_repository,
    get_scan_repository,
    get_page_repository,
    get_issue_repository,
    get_current_active_user
)
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.repositories.scan_repo import ScanRepository
from scanner_v2.database.repositories.page_repo import PageRepository
from scanner_v2.database.repositories.issue_repo import IssueRepository
from scanner_v2.database.models import User
from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import ProjectNotFoundException, ScanNotFoundException
from scanner_v2.utils.fix_guides import get_fix_guide, get_rule_category, get_category_icon

logger = get_logger("api.routes.reports")

# Setup Jinja2 environment
templates_dir = Path(__file__).parent.parent.parent / "report_templates"
jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))

router = APIRouter(prefix="/scans/{scan_id}/reports", tags=["Reports"])


@router.get("/json")
async def get_json_report(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    page_repo: Annotated[PageRepository, Depends(get_page_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)]
):
    """
    Get JSON report for a scan.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        page_repo: Page repository
        issue_repo: Issue repository

    Returns:
        Comprehensive JSON report

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

    # Get pages
    pages, pages_total = await page_repo.get_by_scan(scan_id, skip=0, limit=10000)

    # Get issues
    issues, issues_total = await issue_repo.get_by_scan(scan_id, skip=0, limit=10000)

    # Get issue summary
    issue_summary = await issue_repo.get_summary_by_scan(scan_id)

    # Build report
    report = {
        "scan": {
            "id": scan.id,
            "project_id": scan.project_id,
            "scan_type": scan.scan_type.value,
            "status": scan.status.value,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "duration_seconds": (
                (scan.completed_at - scan.started_at).total_seconds()
                if scan.started_at and scan.completed_at
                else None
            ),
            "config": {
                "scanners": scan.config.scanners if scan.config else [],
                "max_depth": scan.config.max_depth if scan.config else None,
                "max_pages": scan.config.max_pages if scan.config else None,
                "wcag_level": scan.config.wcag_level.value if scan.config else None,
            },
        },
        "project": {
            "id": project.id,
            "name": project.name,
            "base_url": project.base_url,
            "description": project.description,
        },
        "summary": {
            "total_pages": pages_total,
            "total_issues": issues_total,
            "by_impact": issue_summary.get("by_impact", {}),
            "by_wcag_level": issue_summary.get("by_wcag_level", {}),
            "by_principle": issue_summary.get("by_principle", {}),
        },
        "scores": {
            "overall": scan.scores.overall if scan.scores else None,
            "by_principle": scan.scores.by_principle if scan.scores else {},
        },
        "pages": [
            {
                "url": p.url,
                "title": p.title,
                "status_code": p.status_code,
                "load_time_ms": p.load_time_ms,
                "issues_count": p.issues_count,
                "compliance_score": p.compliance_score,
            }
            for p in pages
        ],
        "issues": [
            {
                "id": i.id,
                "rule_id": i.rule_id,
                "category": get_rule_category(i.rule_id),
                "description": i.description,
                "impact": i.impact.value,
                "wcag_level": i.wcag_level.value,
                "wcag_criteria": i.wcag_criteria,
                "principle": i.principle.value,
                "detected_by": i.detected_by,
                "help_text": i.help_text,
                "help_url": i.help_url,
                "instances_count": len(i.instances) if i.instances else 0,
                "status": i.status.value,
                "manual_review_required": i.manual_review_required,
                "fix_guide": get_fix_guide(i.rule_id),
            }
            for i in issues
        ],
        "metadata": {
            "generated_at": "now",
            "report_version": "1.0",
            "scanner_version": "2.0",
        },
    }

    logger.info(f"JSON report generated for scan: {scan_id}")

    return JSONResponse(content=report)


@router.get("/html")
async def get_html_report(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    page_repo: Annotated[PageRepository, Depends(get_page_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)]
):
    """
    Get HTML report for a scan.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        page_repo: Page repository
        issue_repo: Issue repository

    Returns:
        Formatted HTML report

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

    # Get pages
    pages, pages_total = await page_repo.get_by_scan(scan_id, skip=0, limit=10000)

    # Get issues
    issues, issues_total = await issue_repo.get_by_scan(scan_id, skip=0, limit=10000)

    # Enhance issues with fix guides and categories
    enhanced_issues = []
    for issue in issues:
        issue_dict = {
            "issue": issue,
            "category": get_rule_category(issue.rule_id),
            "category_icon": get_category_icon(get_rule_category(issue.rule_id)),
            "fix_guide": get_fix_guide(issue.rule_id)
        }
        enhanced_issues.append(issue_dict)

    # Group issues by impact
    issues_by_impact = {
        "critical": [],
        "serious": [],
        "moderate": [],
        "minor": []
    }
    for enhanced_issue in enhanced_issues:
        issue = enhanced_issue["issue"]
        impact = issue.impact.value if hasattr(issue.impact, 'value') else str(issue.impact)
        if impact in issues_by_impact:
            issues_by_impact[impact].append(enhanced_issue)

    # Also group by category for easier reference
    issues_by_category = {}
    for enhanced_issue in enhanced_issues:
        category = enhanced_issue["category"]
        if category not in issues_by_category:
            issues_by_category[category] = []
        issues_by_category[category].append(enhanced_issue)

    # Group issues by WCAG criteria
    issues_by_wcag = {}
    for issue in issues:
        for criterion in issue.wcag_criteria:
            if criterion not in issues_by_wcag:
                issues_by_wcag[criterion] = []
            issues_by_wcag[criterion].append(issue)

    # Sort WCAG criteria
    issues_by_wcag = dict(sorted(issues_by_wcag.items()))

    # Build WCAG checklist
    wcag_checklist = {
        "level_a": [],
        "level_aa": [],
        "level_aaa": []
    }

    # Get unique WCAG criteria from all issues
    all_criteria = set()
    for issue in issues:
        all_criteria.update(issue.wcag_criteria)

    # Organize by level (simplified - in production would use wcag_reference data)
    for criterion in sorted(all_criteria):
        criterion_issues = [i for i in issues if criterion in i.wcag_criteria]
        level = criterion_issues[0].wcag_level.value if criterion_issues else "A"

        checklist_item = {
            "id": criterion,
            "name": f"WCAG {criterion}",
            "passed": len(criterion_issues) == 0,
            "issue_count": len(criterion_issues)
        }

        if level == "A":
            wcag_checklist["level_a"].append(checklist_item)
        elif level == "AA":
            wcag_checklist["level_aa"].append(checklist_item)
        else:
            wcag_checklist["level_aaa"].append(checklist_item)

    # Read CSS file
    css_path = templates_dir / "styles.css"
    inline_css = ""
    if css_path.exists():
        with open(css_path, 'r') as f:
            inline_css = f.read()

    # Prepare template data
    template_data = {
        "project": project,
        "scan": scan,
        "pages": pages,
        "issues_by_impact": issues_by_impact,
        "issues_by_category": issues_by_category,
        "issues_by_wcag": issues_by_wcag,
        "wcag_checklist": wcag_checklist,
        "generated_at": datetime.utcnow(),
        "inline_css": inline_css
    }

    # Render template
    template = jinja_env.get_template("html_report.jinja2")
    html_content = template.render(**template_data)

    logger.info(f"HTML report generated for scan: {scan_id}")

    return HTMLResponse(content=html_content)


@router.get("/csv")
async def get_csv_report(
    scan_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    page_repo: Annotated[PageRepository, Depends(get_page_repository)],
    issue_repo: Annotated[IssueRepository, Depends(get_issue_repository)]
):
    """
    Get CSV report for a scan.

    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        page_repo: Page repository
        issue_repo: Issue repository

    Returns:
        CSV file with issues data

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

    # Get pages
    pages_dict = {}
    pages, pages_total = await page_repo.get_by_scan(scan_id, skip=0, limit=10000)
    for page in pages:
        pages_dict[page.id] = page

    # Get issues
    issues, issues_total = await issue_repo.get_by_scan(scan_id, skip=0, limit=10000)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Issue ID",
        "Page URL",
        "Page Title",
        "Rule ID",
        "Description",
        "Impact",
        "WCAG Level",
        "WCAG Criteria",
        "Principle",
        "Help Text",
        "Help URL",
        "Detected By",
        "Instances Count",
        "Status",
        "Manual Review Required",
        "Fix Suggestion"
    ])

    # Write issue rows
    for issue in issues:
        # Get page info
        page = pages_dict.get(issue.page_id)
        page_url = page.url if page else "N/A"
        page_title = page.title if page else "N/A"

        # Format fields
        impact = issue.impact.value if hasattr(issue.impact, 'value') else str(issue.impact)
        wcag_level = issue.wcag_level.value if hasattr(issue.wcag_level, 'value') else str(issue.wcag_level)
        wcag_criteria = ", ".join(issue.wcag_criteria) if issue.wcag_criteria else ""
        principle = issue.principle.value if hasattr(issue.principle, 'value') else str(issue.principle)
        detected_by = ", ".join(issue.detected_by) if issue.detected_by else ""
        instances_count = len(issue.instances) if issue.instances else 0
        status = issue.status.value if hasattr(issue.status, 'value') else str(issue.status)

        writer.writerow([
            issue.id,
            page_url,
            page_title,
            issue.rule_id,
            issue.description,
            impact,
            wcag_level,
            wcag_criteria,
            principle,
            issue.help_text or "",
            issue.help_url or "",
            detected_by,
            instances_count,
            status,
            "Yes" if issue.manual_review_required else "No",
            issue.fix_suggestion or ""
        ])

    # Get CSV content
    csv_content = output.getvalue()
    output.close()

    logger.info(f"CSV report generated for scan: {scan_id}")

    # Return as streaming response
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=wcag_report_{scan_id}.csv"
        }
    )
