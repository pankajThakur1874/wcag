"""Pydantic schemas for project API requests and responses."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

from scanner_v2.database.models import WCAGLevel


class ProjectSettingsSchema(BaseModel):
    """Project settings schema."""

    max_depth: int = 3
    max_pages: int = 100
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)
    viewport: dict = {"width": 1920, "height": 1080}
    wait_time: int = 2000
    wcag_level: WCAGLevel = WCAGLevel.AA


class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    base_url: str
    description: Optional[str] = None
    settings: Optional[ProjectSettingsSchema] = None


class ProjectUpdateRequest(BaseModel):
    """Request to update a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[ProjectSettingsSchema] = None


class ProjectResponse(BaseModel):
    """Project response schema."""

    id: str = Field(..., alias="_id")
    user_id: str
    name: str
    base_url: str
    description: Optional[str]
    settings: ProjectSettingsSchema
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class ProjectListResponse(BaseModel):
    """List of projects response."""

    projects: List[ProjectResponse]
    total: int
    skip: int
    limit: int
