"""Core functionality for WCAG Scanner."""

from wcag_backend.core_src.aggregator import ResultsAggregator, run_scan
from wcag_backend.core_src.report_generator import ReportGenerator
from wcag_backend.core_src.crawler import SiteCrawler, CrawlResult
from wcag_backend.core_src.site_scanner import SiteScanner, SiteScanResult, run_site_scan
from wcag_backend.core_src.wcag_mapper import (
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
    "SiteCrawler",
    "CrawlResult",
    "SiteScanner",
    "SiteScanResult",
    "run_site_scan",
    "get_criteria_description",
    "get_criteria_level",
    "get_manual_testing_items",
    "group_violations_by_criteria",
    "group_violations_by_level",
    "get_conformance_status"
]
