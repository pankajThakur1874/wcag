"""Scan request and response schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# Request Schemas

class QuickScanRequest(BaseModel):
    """Quick scan request."""

    url: HttpUrl
    siteWide: bool = Field(False, alias="siteWide")
    maxPages: int = Field(10, ge=1, le=100, alias="maxPages")
    maxDepth: int = Field(3, ge=1, le=10, alias="maxDepth")
    scanners: List[str] = Field(default_factory=lambda: ["axe-core"])

    model_config = {"populate_by_name": True}


class ProjectScanRequest(BaseModel):
    """Project scan request."""

    projectId: str = Field(..., alias="projectId")
    maxPages: int = Field(50, ge=1, le=100, alias="maxPages")
    maxDepth: int = Field(5, ge=1, le=10, alias="maxDepth")
    scanners: List[str] = Field(default_factory=lambda: ["axe-core", "html-validator"])

    model_config = {"populate_by_name": True}


# Response Schemas

class ScanProgressResponse(BaseModel):
    """Scan progress information."""

    pagesScanned: int = Field(..., alias="pagesScanned")
    totalPages: int = Field(..., alias="totalPages")
    currentUrl: Optional[str] = Field(None, alias="currentUrl")
    percentage: int

    model_config = {"populate_by_name": True}


class ScanStatusResponse(BaseModel):
    """Scan status response."""

    scanId: str = Field(..., alias="scanId")
    status: str
    progress: ScanProgressResponse
    pagesScanned: Optional[int] = Field(None, alias="pagesScanned")
    totalPages: Optional[int] = Field(None, alias="totalPages")
    currentUrl: Optional[str] = Field(None, alias="currentUrl")
    startedAt: Optional[datetime] = Field(None, alias="startedAt")

    model_config = {"populate_by_name": True}


class ScanStatusCompletedResponse(BaseModel):
    """Scan status when completed."""

    scanId: str = Field(..., alias="scanId")
    status: str
    progress: int
    pagesScanned: int = Field(..., alias="pagesScanned")
    totalPages: int = Field(..., alias="totalPages")
    score: int
    issuesCount: int = Field(..., alias="issuesCount")
    duration: int
    completedAt: datetime = Field(..., alias="completedAt")

    model_config = {"populate_by_name": True}


class ScanResponse(BaseModel):
    """Scan creation response."""

    scanId: str = Field(..., alias="scanId")
    url: str
    type: str
    status: str
    createdAt: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class ScanSuccessResponse(BaseModel):
    """Scan creation success response."""

    success: bool = True
    data: ScanResponse
    message: str


class ScanListItemResponse(BaseModel):
    """Scan list item response."""

    id: str
    projectId: Optional[str] = Field(None, alias="projectId")
    projectName: Optional[str] = Field(None, alias="projectName")
    url: str
    type: str
    status: str
    score: Optional[int] = None
    issuesCount: int = Field(0, alias="issuesCount")
    duration: Optional[int] = None
    createdAt: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class ScanDetailResponse(BaseModel):
    """Detailed scan response."""

    id: str
    projectId: Optional[str] = Field(None, alias="projectId")
    projectName: Optional[str] = Field(None, alias="projectName")
    url: str
    type: str
    status: str
    score: Optional[int] = None
    issuesCount: int = Field(0, alias="issuesCount")
    duration: Optional[int] = None
    pagesScanned: int = Field(0, alias="pagesScanned")
    scanners: List[str]
    createdAt: datetime = Field(..., alias="createdAt")
    completedAt: Optional[datetime] = Field(None, alias="completedAt")

    model_config = {"populate_by_name": True}
