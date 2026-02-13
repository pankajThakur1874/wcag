"""Project request and response schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# Request Schemas

class ProjectCreateRequest(BaseModel):
    """Create project request."""

    name: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl
    description: Optional[str] = Field(None, max_length=1000)


class ProjectUpdateRequest(BaseModel):
    """Update project request."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(active|archived)$")


# Response Schemas

class ProjectResponse(BaseModel):
    """Project response."""

    id: str
    name: str
    url: str
    description: Optional[str] = None
    status: str
    score: Optional[int] = None
    lastScan: Optional[datetime] = Field(None, alias="lastScan")
    createdAt: datetime = Field(..., alias="createdAt")
    updatedAt: datetime = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


class ProjectDetailResponse(BaseModel):
    """Detailed project response."""

    id: str
    name: str
    url: str
    description: Optional[str] = None
    status: str
    score: Optional[int] = None
    lastScan: Optional[datetime] = Field(None, alias="lastScan")
    scanCount: int = Field(0, alias="scanCount")
    createdAt: datetime = Field(..., alias="createdAt")
    updatedAt: datetime = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


class ProjectSuccessResponse(BaseModel):
    """Single project success response."""

    success: bool = True
    data: ProjectResponse


class ProjectDetailSuccessResponse(BaseModel):
    """Detailed project success response."""

    success: bool = True
    data: ProjectDetailResponse
