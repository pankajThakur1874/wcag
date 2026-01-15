"""Issue aggregator for deduplicating and merging issues."""

from typing import List, Dict, Any
from collections import defaultdict

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import hash_dict
from scanner_v2.database.models import ImpactLevel, WCAGLevel, Principle

logger = get_logger("issue_aggregator")


class IssueAggregator:
    """Aggregates and deduplicates issues from multiple scanners."""

    def aggregate_issues(self, page_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregate issues from multiple scanners, removing duplicates.

        Args:
            page_issues: List of issues from all pages

        Returns:
            Deduplicated and merged issues
        """
        logger.info(f"Aggregating {len(page_issues)} issues")

        # Group issues by unique signature
        issue_groups = defaultdict(list)

        for issue in page_issues:
            signature = self._get_issue_signature(issue)
            issue_groups[signature].append(issue)

        # Merge grouped issues
        aggregated = []
        for signature, issues in issue_groups.items():
            merged = self._merge_issues(issues)
            aggregated.append(merged)

        logger.info(f"Aggregated to {len(aggregated)} unique issues")

        return aggregated

    def _get_issue_signature(self, issue: Dict[str, Any]) -> str:
        """
        Generate unique signature for an issue.

        Args:
            issue: Issue dictionary

        Returns:
            Signature hash
        """
        # Create signature from key fields
        signature_data = {
            "rule_id": issue.get("rule_id", ""),
            "description": issue.get("description", ""),
            "wcag_criteria": sorted(issue.get("wcag_criteria", [])),
        }

        return hash_dict(signature_data)

    def _merge_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge duplicate issues.

        Args:
            issues: List of duplicate issues

        Returns:
            Merged issue
        """
        if len(issues) == 1:
            return issues[0]

        # Use first issue as base
        merged = issues[0].copy()

        # Collect all detected_by scanners
        all_detected_by = set()
        all_instances = []

        for issue in issues:
            # Collect scanners
            detected_by = issue.get("detected_by", [])
            if isinstance(detected_by, list):
                all_detected_by.update(detected_by)
            elif isinstance(detected_by, str):
                all_detected_by.add(detected_by)

            # Collect instances
            instances = issue.get("instances", [])
            if instances:
                all_instances.extend(instances)

        # Update merged issue
        merged["detected_by"] = list(all_detected_by)
        merged["instances"] = all_instances
        merged["instance_count"] = len(all_instances)

        # Use highest impact level
        impacts = [issue.get("impact") for issue in issues if issue.get("impact")]
        if impacts:
            impact_priority = {
                ImpactLevel.CRITICAL.value: 4,
                ImpactLevel.SERIOUS.value: 3,
                ImpactLevel.MODERATE.value: 2,
                ImpactLevel.MINOR.value: 1,
            }

            highest_impact = max(impacts, key=lambda x: impact_priority.get(x, 0))
            merged["impact"] = highest_impact

        return merged

    def calculate_summary(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate issue summary statistics.

        Args:
            issues: List of issues

        Returns:
            Summary statistics
        """
        summary = {
            "total_issues": len(issues),
            "by_impact": {
                "critical": 0,
                "serious": 0,
                "moderate": 0,
                "minor": 0,
            },
            "by_wcag_level": {
                "A": 0,
                "AA": 0,
                "AAA": 0,
            },
            "by_principle": {
                "perceivable": 0,
                "operable": 0,
                "understandable": 0,
                "robust": 0,
            },
        }

        for issue in issues:
            # Count by impact
            impact = issue.get("impact", "moderate")
            if impact in summary["by_impact"]:
                summary["by_impact"][impact] += 1

            # Count by WCAG level
            wcag_level = issue.get("wcag_level", "AA")
            if wcag_level in summary["by_wcag_level"]:
                summary["by_wcag_level"][wcag_level] += 1

            # Count by principle
            principle = issue.get("principle", "perceivable")
            if principle in summary["by_principle"]:
                summary["by_principle"][principle] += 1

        return summary


# Global instance
issue_aggregator = IssueAggregator()
