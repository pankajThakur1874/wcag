"""Pydantic models for MongoDB documents."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


# Enums

class ScanStatus(str, Enum):
    """Scan status enum."""

    QUEUED = "queued"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanType(str, Enum):
    """Scan type enum."""

    QUICK = "quick"
    FULL = "full"


class WCAGLevel(str, Enum):
    """WCAG conformance level."""

    A = "A"
    AA = "AA"
    AAA = "AAA"


class ImpactLevel(str, Enum):
    """Issue impact level."""

    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class IssueStatus(str, Enum):
    """Issue status."""

    OPEN = "open"
    FIXED = "fixed"
    IGNORED = "ignored"


class ProjectStatus(str, Enum):
    """Project status."""

    ACTIVE = "active"
    ARCHIVED = "archived"


# Base Models

class MongoBaseModel(BaseModel):
    """Base model for MongoDB documents."""

    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


# Domain Models

class User(MongoBaseModel):
    """User document model."""

    name: str
    email: EmailStr
    password_hash: str


class RefreshToken(MongoBaseModel):
    """Refresh token document model."""

    user_id: str
    token_hash: str  # SHA256 hash of the token
    expires_at: datetime
    revoked: bool = False
    replaced_by: Optional[str] = None  # ID of the new token that replaced this one


class Project(MongoBaseModel):
    """Project document model."""

    user_id: str
    name: str
    url: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE


class ScanConfig(BaseModel):
    """Scan configuration."""

    max_pages: Optional[int] = 10
    max_depth: Optional[int] = 3
    scanners: List[str] = Field(default_factory=lambda: ["axe"])


class ScanProgress(BaseModel):
    """Scan progress tracking."""

    pages_scanned: int = 0
    total_pages: int = 0
    current_url: Optional[str] = None
    percentage: int = 0


class IssuesByImpact(BaseModel):
    """Issues grouped by impact level."""

    critical: int = 0
    serious: int = 0
    moderate: int = 0
    minor: int = 0


class Scan(MongoBaseModel):
    """Scan document model."""

    user_id: str
    project_id: Optional[str] = None
    url: str
    type: ScanType
    status: ScanStatus = ScanStatus.QUEUED

    # Configuration
    config: ScanConfig = Field(default_factory=ScanConfig)

    # Progress tracking
    progress: ScanProgress = Field(default_factory=ScanProgress)

    # Results
    score: Optional[int] = None
    issues_count: int = 0
    issues_by_impact: IssuesByImpact = Field(default_factory=IssuesByImpact)

    # Timing
    duration: Optional[int] = None  # seconds
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class Issue(MongoBaseModel):
    """Issue document model."""

    scan_id: str
    user_id: str  # Denormalized for quick access
    page_url: str

    # Issue details
    description: str
    impact: ImpactLevel
    wcag_criteria: Optional[str] = None
    wcag_level: Optional[WCAGLevel] = None
    selector: Optional[str] = None
    html_snippet: Optional[str] = None
    how_to_fix: Optional[str] = None
    help_url: Optional[str] = None

    # Status
    status: IssueStatus = IssueStatus.OPEN


# Helper functions

def to_mongo_dict(model: BaseModel) -> Dict[str, Any]:
    """
    Convert Pydantic model to MongoDB-safe dictionary.

    Args:
        model: Pydantic model instance

    Returns:
        Dictionary suitable for MongoDB insertion
    """
    data = model.model_dump(by_alias=True, exclude_none=True)

    # Convert enums to strings
    for key, value in data.items():
        if isinstance(value, Enum):
            data[key] = value.value
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, Enum):
                    value[sub_key] = sub_value.value

    # Remove None values from _id if present
    if "_id" in data and data["_id"] is None:
        del data["_id"]

    return data
