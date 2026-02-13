"""Report request and response schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Response Schemas

class ReportListItemResponse(BaseModel):
    """Report list item response."""

    id: str
    scanId: str = Field(..., alias="scanId")
    projectId: Optional[str] = Field(None, alias="projectId")
    projectName: Optional[str] = Field(None, alias="projectName")
    url: str
    type: str
    score: Optional[int] = None
    issuesCount: int = Field(..., alias="issuesCount")
    status: str
    createdAt: datetime = Field(..., alias="createdAt")
    completedAt: Optional[datetime] = Field(None, alias="completedAt")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }
