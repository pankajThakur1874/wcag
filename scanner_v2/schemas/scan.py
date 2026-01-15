"""Pydantic schemas for scan jobs and requests."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from scanner_v2.database.models import (
    WCAGLevel, ScanStatus, ScanType, ScanConfig,
    ScanProgress, ScanSummary, ScanScores
)


class JobType(str, Enum):
    """Job type enum."""

    SCAN_ORCHESTRATION = "scan_orchestration"
    PAGE_SCAN = "page_scan"


class JobStatus(str, Enum):
    """Job status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    """Job priority levels."""

    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 10


class ScanJobPayload(BaseModel):
    """Payload for scan orchestration job."""

    scan_id: str
    project_id: str
    base_url: str
    config: Dict[str, Any] = Field(default_factory=dict)


class PageScanJobPayload(BaseModel):
    """Payload for page scan job."""

    scan_id: str
    page_url: str
    config: Dict[str, Any] = Field(default_factory=dict)


class Job(BaseModel):
    """Job model."""

    job_id: str
    job_type: JobType
    priority: int = JobPriority.NORMAL.value
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None

    class Config:
        use_enum_values = True


class ScanRequest(BaseModel):
    """Request to create a new scan."""

    project_id: str
    scan_type: str = "full"
    config: Optional[Dict[str, Any]] = None


class ScanConfigRequest(BaseModel):
    """Scan configuration request."""

    max_depth: int = 3
    max_pages: int = 100
    scanners: List[str] = ["axe"]
    wcag_level: WCAGLevel = WCAGLevel.AA
    screenshot_enabled: bool = True
    wait_time: int = 2000
    page_timeout: int = 30000
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)
    viewport: Dict[str, int] = {"width": 1920, "height": 1080}


class ScanStatusResponse(BaseModel):
    """Scan status response."""

    scan_id: str
    status: ScanStatus
    progress: Dict[str, Any]
    summary: Optional[Dict[str, Any]] = None
    scores: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ScanSummaryResponse(BaseModel):
    """Scan summary response."""

    scan_id: str
    project_id: str
    base_url: str
    status: ScanStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    pages_scanned: int
    total_issues: int
    by_impact: Dict[str, int]
    compliance_score: float
    wcag_level: WCAGLevel


class QueueStatsResponse(BaseModel):
    """Queue statistics response."""

    orchestration_queue_size: int
    page_scan_queue_size: int
    active_workers: int
    total_jobs_processed: int
    failed_jobs: int


class ScanCreateRequest(BaseModel):
    """Request to create a new scan."""

    scan_type: Optional[ScanType] = ScanType.FULL
    scanners: Optional[List[str]] = None
    max_depth: Optional[int] = None
    max_pages: Optional[int] = None
    exclude_patterns: Optional[List[str]] = None
    include_patterns: Optional[List[str]] = None
    viewport: Optional[Dict[str, int]] = None
    wait_time: Optional[int] = None
    wcag_level: Optional[WCAGLevel] = None
    screenshot_enabled: Optional[bool] = None


class ScanResponse(BaseModel):
    """Scan response."""

    id: str
    project_id: str
    scan_type: ScanType
    status: ScanStatus
    config: Optional[ScanConfig] = None
    progress: Optional[ScanProgress] = None
    summary: Optional[ScanSummary] = None
    scores: Optional[ScanScores] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    """List of scans response."""

    scans: List[ScanResponse]
    total: int
    skip: int
    limit: int
