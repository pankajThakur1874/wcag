"""Scan result models for WCAG Scanner."""

from typing import Optional
from datetime import datetime
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field

from src.models.violation import Violation, Impact, WCAGLevel


class ScanStatus(str, Enum):
    """Status of a scan."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolStatus(BaseModel):
    """Status of an individual tool."""
    name: str
    version: Optional[str] = None
    status: str = "success"
    rules_checked: Optional[int] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class ScanSummary(BaseModel):
    """Summary of scan results."""
    total_violations: int = 0
    by_impact: dict[str, int] = Field(default_factory=lambda: {
        "critical": 0,
        "serious": 0,
        "moderate": 0,
        "minor": 0
    })
    by_wcag_level: dict[str, int] = Field(default_factory=lambda: {
        "A": 0,
        "AA": 0,
        "AAA": 0
    })
    passes: int = 0

    @classmethod
    def from_violations(cls, violations: list[Violation], passes: int = 0) -> "ScanSummary":
        """Create summary from list of violations."""
        summary = cls(passes=passes)
        summary.total_violations = len(violations)

        for violation in violations:
            # Count by impact
            impact_key = violation.impact.value
            summary.by_impact[impact_key] = summary.by_impact.get(impact_key, 0) + 1

            # Count by WCAG level
            if violation.wcag_level:
                level_key = violation.wcag_level.value
                summary.by_wcag_level[level_key] = summary.by_wcag_level.get(level_key, 0) + 1

        return summary


class ScanScores(BaseModel):
    """Scores from different tools."""
    overall: float = 0.0
    axe: Optional[float] = None
    lighthouse: Optional[float] = None
    pa11y: Optional[float] = None
    html_validator: Optional[float] = None


class ScanResult(BaseModel):
    """Complete scan result."""
    scan_id: str = Field(default_factory=lambda: str(uuid4()))
    url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: ScanStatus = ScanStatus.PENDING
    duration_seconds: Optional[float] = None
    scores: ScanScores = Field(default_factory=ScanScores)
    summary: ScanSummary = Field(default_factory=ScanSummary)
    violations: list[Violation] = Field(default_factory=list)
    tools_used: dict[str, ToolStatus] = Field(default_factory=dict)
    error: Optional[str] = None

    def calculate_overall_score(self) -> float:
        """Calculate overall accessibility score (0-100)."""
        if self.summary.total_violations == 0:
            return 100.0

        # Weight violations by impact
        weights = {
            "critical": 25,
            "serious": 15,
            "moderate": 7,
            "minor": 3
        }

        penalty = sum(
            count * weights.get(impact, 5)
            for impact, count in self.summary.by_impact.items()
        )

        # Cap at 0 minimum
        score = max(0, 100 - penalty)
        return round(score, 1)

    def finalize(self, duration: float) -> None:
        """Finalize the scan result with duration and scores."""
        self.duration_seconds = round(duration, 2)
        self.status = ScanStatus.COMPLETED
        self.summary = ScanSummary.from_violations(self.violations, self.summary.passes)
        self.scores.overall = self.calculate_overall_score()


class ManualCheckItem(BaseModel):
    """Item requiring manual review."""
    criteria: str
    description: str
    reason: str


class WCAGCoverage(BaseModel):
    """WCAG coverage information."""
    automatable_criteria: int = 28
    criteria_checked: int = 0
    manual_review_needed: list[ManualCheckItem] = Field(default_factory=list)
