"""Issue request and response schemas."""

from typing import Optional
from pydantic import BaseModel, Field


# Request Schemas

class UpdateIssueStatusRequest(BaseModel):
    """Update issue status request."""

    status: str = Field(..., pattern="^(open|fixed|ignored)$")


# Response Schemas

class IssueResponse(BaseModel):
    """Issue response."""

    id: str
    scanId: str = Field(..., alias="scanId")
    description: str
    impact: str
    wcagCriteria: Optional[str] = Field(None, alias="wcagCriteria")
    wcagLevel: Optional[str] = Field(None, alias="wcagLevel")
    selector: Optional[str] = None
    htmlSnippet: Optional[str] = Field(None, alias="htmlSnippet")
    howToFix: Optional[str] = Field(None, alias="howToFix")
    helpUrl: Optional[str] = Field(None, alias="helpUrl")
    status: str
    pageUrl: str = Field(..., alias="pageUrl")

    model_config = {"populate_by_name": True}


class IssueStatusUpdateResponse(BaseModel):
    """Issue status update response."""

    success: bool = True
    data: dict
