"""Pydantic schemas for issue API requests and responses."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from scanner_v2.database.models import ImpactLevel, WCAGLevel, Principle, IssueStatus


class IssueInstanceSchema(BaseModel):
    """Issue instance schema."""

    selector: str
    html: Optional[str] = None
    screenshot_path: Optional[str] = None
    context: Optional[str] = None


class IssueResponse(BaseModel):
    """Issue response schema."""

    id: str = Field(..., alias="_id")
    scan_id: str
    page_id: str
    wcag_criteria: List[str]
    wcag_level: WCAGLevel
    principle: Principle
    impact: ImpactLevel
    rule_id: str
    description: str
    help_text: Optional[str]
    help_url: Optional[str]
    detected_by: List[str]
    instances: List[IssueInstanceSchema]
    status: IssueStatus
    manual_review_required: bool
    fix_suggestion: Optional[str]
    created_at: datetime

    class Config:
        populate_by_name = True


class IssueUpdateRequest(BaseModel):
    """Request to update issue status."""

    status: IssueStatus
    notes: Optional[str] = None


class IssueListResponse(BaseModel):
    """List of issues response."""

    issues: List[IssueResponse]
    total: int
    page: int
    page_size: int


class IssueFilterRequest(BaseModel):
    """Issue filter request."""

    scan_id: Optional[str] = None
    page_id: Optional[str] = None
    impact: Optional[ImpactLevel] = None
    wcag_level: Optional[WCAGLevel] = None
    principle: Optional[Principle] = None
    status: Optional[IssueStatus] = None
    manual_review_required: Optional[bool] = None
