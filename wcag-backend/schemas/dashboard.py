"""Dashboard request and response schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Response Schemas

class IssuesByImpactResponse(BaseModel):
    """Issues grouped by impact level."""

    critical: int
    serious: int
    moderate: int
    minor: int


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""

    totalScans: int = Field(..., alias="totalScans")
    activeProjects: int = Field(..., alias="activeProjects")
    criticalIssues: int = Field(..., alias="criticalIssues")
    avgScore: int = Field(..., alias="avgScore")
    issuesByImpact: IssuesByImpactResponse = Field(..., alias="issuesByImpact")

    model_config = {"populate_by_name": True}


class DashboardStatsSuccessResponse(BaseModel):
    """Dashboard stats success response."""

    success: bool = True
    data: DashboardStatsResponse


class ScannedPageResponse(BaseModel):
    """Scanned page response for dashboard."""

    id: str
    url: str
    projectName: Optional[str] = Field(None, alias="projectName")
    score: Optional[int] = None
    issuesCount: int = Field(..., alias="issuesCount")
    lastScanned: datetime = Field(..., alias="lastScanned")
    status: str

    model_config = {"populate_by_name": True}
