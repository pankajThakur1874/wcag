"""Core functionality for WCAG Scanner."""

from src.core.aggregator import ResultsAggregator, run_scan
from src.core.report_generator import ReportGenerator
from src.core.wcag_mapper import (
    get_criteria_description,
    get_criteria_level,
    get_manual_testing_items,
    group_violations_by_criteria,
    group_violations_by_level,
    get_conformance_status
)

__all__ = [
    "ResultsAggregator",
    "run_scan",
    "ReportGenerator",
    "get_criteria_description",
    "get_criteria_level",
    "get_manual_testing_items",
    "group_violations_by_criteria",
    "group_violations_by_level",
    "get_conformance_status"
]
