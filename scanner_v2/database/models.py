"""Pydantic models for MongoDB documents."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ScanStatus(str, Enum):
    """Scan status enum."""

    QUEUED = "queued"
    CRAWLING = "crawling"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, Enum):
    """Scan type enum."""

    FULL = "full"
    SINGLE_PAGE = "single_page"


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


class Principle(str, Enum):
    """WCAG principle."""

    PERCEIVABLE = "perceivable"
    OPERABLE = "operable"
    UNDERSTANDABLE = "understandable"
    ROBUST = "robust"


class IssueStatus(str, Enum):
    """Issue status."""

    OPEN = "open"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"
    IGNORED = "ignored"


class AutomationLevel(str, Enum):
    """Automation level for WCAG criteria."""

    FULLY_AUTOMATED = "fully_automated"
    PARTIALLY_AUTOMATED = "partially_automated"
    MANUAL = "manual"


class UserRole(str, Enum):
    """User role."""

    ADMIN = "admin"
    USER = "user"


# Base model with common fields
class MongoBaseModel(BaseModel):
    """Base model for MongoDB documents."""

    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# User models
class User(MongoBaseModel):
    """User document model."""

    email: str
    password_hash: str
    name: Optional[str] = None
    role: UserRole = UserRole.USER


# Project models
class ProjectSettings(BaseModel):
    """Project settings."""

    max_depth: int = 3
    max_pages: int = 100
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)
    viewport: Dict[str, int] = {"width": 1920, "height": 1080}
    wait_time: int = 2000  # ms
    wcag_level: WCAGLevel = WCAGLevel.AA


class Project(MongoBaseModel):
    """Project document model."""

    user_id: str
    name: str
    base_url: str
    description: Optional[str] = None
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


# Scan models
class ScanConfig(BaseModel):
    """Scan configuration."""

    scanners: List[str] = ["axe", "pa11y", "lighthouse"]
    max_depth: int = 3
    max_pages: int = 100
    wait_time: int = 2000
    wcag_level: WCAGLevel = WCAGLevel.AA
    viewport: Dict[str, int] = {"width": 1920, "height": 1080}
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)


class ScanProgress(BaseModel):
    """Scan progress information."""

    total_pages: int = 0
    pages_crawled: int = 0
    pages_scanned: int = 0
    current_page: Optional[str] = None


class ImpactSummary(BaseModel):
    """Issue count by impact level."""

    critical: int = 0
    serious: int = 0
    moderate: int = 0
    minor: int = 0


class WCAGLevelSummary(BaseModel):
    """Issue count by WCAG level."""

    A: int = 0
    AA: int = 0
    AAA: int = 0


class ScanSummary(BaseModel):
    """Scan summary statistics."""

    total_issues: int = 0
    by_impact: ImpactSummary = Field(default_factory=ImpactSummary)
    by_wcag_level: WCAGLevelSummary = Field(default_factory=WCAGLevelSummary)


class PrincipleScores(BaseModel):
    """Scores by WCAG principle."""

    perceivable: float = 0.0
    operable: float = 0.0
    understandable: float = 0.0
    robust: float = 0.0


class ScanScores(BaseModel):
    """Scan scores."""

    overall: float = 0.0
    by_principle: PrincipleScores = Field(default_factory=PrincipleScores)


class Scan(MongoBaseModel):
    """Scan document model."""

    project_id: str
    status: ScanStatus = ScanStatus.QUEUED
    scan_type: ScanType = ScanType.FULL
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: ScanConfig = Field(default_factory=ScanConfig)
    progress: ScanProgress = Field(default_factory=ScanProgress)
    summary: ScanSummary = Field(default_factory=ScanSummary)
    scores: ScanScores = Field(default_factory=ScanScores)
    error_message: Optional[str] = None


# Scanned page models
class RawScanResults(BaseModel):
    """Raw scanner results."""

    axe: Optional[Dict[str, Any]] = None
    pa11y: Optional[Dict[str, Any]] = None
    lighthouse: Optional[Dict[str, Any]] = None


class ScannedPage(MongoBaseModel):
    """Scanned page document model."""

    scan_id: str
    url: str
    title: Optional[str] = None
    status_code: Optional[int] = None
    load_time_ms: Optional[int] = None
    screenshot_path: Optional[str] = None
    raw_results: RawScanResults = Field(default_factory=RawScanResults)
    issues_count: int = 0
    compliance_score: float = 0.0
    scanned_at: datetime = Field(default_factory=datetime.utcnow)


# Issue models
class IssueInstance(BaseModel):
    """Single instance of an issue."""

    selector: str
    html: Optional[str] = None
    screenshot_path: Optional[str] = None
    context: Optional[str] = None


class Issue(MongoBaseModel):
    """Issue document model."""

    scan_id: str
    page_id: str
    wcag_criteria: List[str] = Field(default_factory=list)
    wcag_level: WCAGLevel
    principle: Principle
    impact: ImpactLevel
    rule_id: str
    description: str
    help_text: Optional[str] = None
    help_url: Optional[str] = None
    detected_by: List[str] = Field(default_factory=list)
    instances: List[IssueInstance] = Field(default_factory=list)
    status: IssueStatus = IssueStatus.OPEN
    manual_review_required: bool = False
    fix_suggestion: Optional[str] = None


# WCAG Criteria reference
class WCAGCriteria(BaseModel):
    """WCAG criteria reference document."""

    id: str = Field(..., alias="_id")
    name: str
    level: WCAGLevel
    principle: Principle
    guideline: str
    description: str
    automation_level: AutomationLevel
    url: str

    class Config:
        populate_by_name = True


# Helper function to convert model to MongoDB document
def to_mongo_dict(model: BaseModel) -> Dict[str, Any]:
    """
    Convert Pydantic model to MongoDB document dictionary.

    Args:
        model: Pydantic model instance

    Returns:
        Dictionary ready for MongoDB insertion
    """
    doc = model.model_dump(by_alias=True, exclude_none=True)

    # Convert Enum values to strings
    for key, value in doc.items():
        if isinstance(value, Enum):
            doc[key] = value.value
        elif isinstance(value, dict):
            doc[key] = _convert_enum_values(value)

    return doc


def _convert_enum_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert Enum values to strings in dictionary."""
    result = {}
    for key, value in data.items():
        if isinstance(value, Enum):
            result[key] = value.value
        elif isinstance(value, dict):
            result[key] = _convert_enum_values(value)
        elif isinstance(value, list):
            result[key] = [
                item.value if isinstance(item, Enum) else item
                for item in value
            ]
        else:
            result[key] = value
    return result
