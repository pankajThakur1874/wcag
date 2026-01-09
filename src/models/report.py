"""Report models for WCAG Scanner."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.scan_result import ScanResult, ScanSummary, ScanScores, WCAGCoverage


class ReportMetadata(BaseModel):
    """Metadata for the report."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    scanner_version: str = "1.0.0"
    wcag_version: str = "2.2"


class AccessibilityReport(BaseModel):
    """Complete accessibility report."""
    metadata: ReportMetadata = Field(default_factory=ReportMetadata)
    scan_result: ScanResult
    wcag_coverage: WCAGCoverage = Field(default_factory=WCAGCoverage)

    def to_summary_dict(self) -> dict:
        """Convert to a summary dictionary for display."""
        return {
            "url": self.scan_result.url,
            "scan_id": self.scan_result.scan_id,
            "timestamp": self.scan_result.timestamp.isoformat(),
            "overall_score": self.scan_result.scores.overall,
            "total_violations": self.scan_result.summary.total_violations,
            "critical": self.scan_result.summary.by_impact.get("critical", 0),
            "serious": self.scan_result.summary.by_impact.get("serious", 0),
            "moderate": self.scan_result.summary.by_impact.get("moderate", 0),
            "minor": self.scan_result.summary.by_impact.get("minor", 0),
            "passes": self.scan_result.summary.passes,
            "duration_seconds": self.scan_result.duration_seconds
        }
