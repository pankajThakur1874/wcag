"""Models for WCAG Scanner."""

from wcag_backend.models_src.violation import (
    Violation,
    ViolationInstance,
    Impact,
    WCAGLevel,
    WCAG_CRITERIA_LEVELS,
    get_wcag_level
)
from wcag_backend.models_src.scan_result import (
    ScanResult,
    ScanStatus,
    ScanSummary,
    ScanScores,
    ToolStatus,
    ManualCheckItem,
    WCAGCoverage
)
from wcag_backend.models_src.report import (
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
