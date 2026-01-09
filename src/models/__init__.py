"""Models for WCAG Scanner."""

from src.models.violation import (
    Violation,
    ViolationInstance,
    Impact,
    WCAGLevel,
    WCAG_CRITERIA_LEVELS,
    get_wcag_level
)
from src.models.scan_result import (
    ScanResult,
    ScanStatus,
    ScanSummary,
    ScanScores,
    ToolStatus,
    ManualCheckItem,
    WCAGCoverage
)
from src.models.report import (
    AccessibilityReport,
    ReportMetadata
)

__all__ = [
    "Violation",
    "ViolationInstance",
    "Impact",
    "WCAGLevel",
    "WCAG_CRITERIA_LEVELS",
    "get_wcag_level",
    "ScanResult",
    "ScanStatus",
    "ScanSummary",
    "ScanScores",
    "ToolStatus",
    "ManualCheckItem",
    "WCAGCoverage",
    "AccessibilityReport",
    "ReportMetadata"
]
