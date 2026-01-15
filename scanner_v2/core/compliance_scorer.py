"""Compliance scorer for calculating WCAG compliance scores."""

from typing import List, Dict, Any
from collections import defaultdict

from scanner_v2.utils.logger import get_logger
from scanner_v2.database.models import WCAGLevel, Principle, ImpactLevel
from scanner_v2.core.wcag_reference import wcag_reference

logger = get_logger("compliance_scorer")


class ComplianceScorer:
    """Calculates WCAG compliance scores."""

    # Impact weights for scoring
    IMPACT_WEIGHTS = {
        ImpactLevel.CRITICAL.value: 10,
        ImpactLevel.SERIOUS.value: 5,
        ImpactLevel.MODERATE.value: 2,
        ImpactLevel.MINOR.value: 1,
    }

    # WCAG level weights
    LEVEL_WEIGHTS = {
        WCAGLevel.A.value: 3,
        WCAGLevel.AA.value: 2,
        WCAGLevel.AAA.value: 1,
    }

    def calculate_score(
        self,
        issues: List[Dict[str, Any]],
        wcag_level: WCAGLevel = WCAGLevel.AA
    ) -> Dict[str, Any]:
        """
        Calculate compliance score.

        Args:
            issues: List of issues
            wcag_level: Target WCAG level

        Returns:
            Scores dictionary
        """
        logger.info(f"Calculating compliance score for {len(issues)} issues (level: {wcag_level.value})")

        # Get applicable criteria for level
        applicable_criteria = self._get_applicable_criteria(wcag_level)

        # Calculate weighted issue score
        issue_weight = self._calculate_issue_weight(issues, wcag_level)

        # Calculate total possible weight
        total_weight = self._calculate_total_weight(applicable_criteria)

        # Calculate overall score (0-100)
        if total_weight > 0:
            overall_score = max(0, (1 - (issue_weight / total_weight)) * 100)
        else:
            overall_score = 100.0

        # Calculate scores by principle
        principle_scores = self._calculate_principle_scores(issues, applicable_criteria)

        scores = {
            "overall": round(overall_score, 2),
            "by_principle": principle_scores,
            "issue_weight": issue_weight,
            "total_weight": total_weight,
            "applicable_criteria_count": len(applicable_criteria),
        }

        logger.info(f"Compliance score: {scores['overall']}/100")

        return scores

    def _get_applicable_criteria(self, wcag_level: WCAGLevel) -> List[Dict]:
        """
        Get applicable WCAG criteria for level.

        Args:
            wcag_level: Target WCAG level

        Returns:
            List of applicable criteria
        """
        criteria = []

        for criterion in wcag_reference.get_all_criteria():
            if wcag_level == WCAGLevel.AAA:
                # AAA includes all levels
                criteria.append(criterion)
            elif wcag_level == WCAGLevel.AA:
                # AA includes A and AA
                if criterion["level"] in [WCAGLevel.A, WCAGLevel.AA]:
                    criteria.append(criterion)
            elif wcag_level == WCAGLevel.A:
                # A includes only A
                if criterion["level"] == WCAGLevel.A:
                    criteria.append(criterion)

        return criteria

    def _calculate_issue_weight(self, issues: List[Dict[str, Any]], wcag_level: WCAGLevel) -> float:
        """
        Calculate weighted score for issues.

        Args:
            issues: List of issues
            wcag_level: Target WCAG level

        Returns:
            Weighted issue score
        """
        weight = 0.0

        for issue in issues:
            impact = issue.get("impact", ImpactLevel.MODERATE.value)
            issue_level = issue.get("wcag_level", WCAGLevel.AA.value)

            # Only count issues at or below target level
            if self._is_level_applicable(issue_level, wcag_level):
                impact_weight = self.IMPACT_WEIGHTS.get(impact, 2)
                level_weight = self.LEVEL_WEIGHTS.get(issue_level, 2)

                weight += impact_weight * level_weight

        return weight

    def _calculate_total_weight(self, criteria: List[Dict]) -> float:
        """
        Calculate total possible weight for criteria.

        Args:
            criteria: List of WCAG criteria

        Returns:
            Total weight
        """
        weight = 0.0

        for criterion in criteria:
            # Use serious impact and level weight as baseline
            level_weight = self.LEVEL_WEIGHTS.get(criterion["level"].value, 2)
            baseline_impact = self.IMPACT_WEIGHTS[ImpactLevel.SERIOUS.value]

            weight += baseline_impact * level_weight

        return weight

    def _calculate_principle_scores(
        self,
        issues: List[Dict[str, Any]],
        criteria: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate scores by WCAG principle.

        Args:
            issues: List of issues
            criteria: Applicable criteria

        Returns:
            Scores by principle
        """
        # Group criteria by principle
        criteria_by_principle = defaultdict(list)
        for criterion in criteria:
            criteria_by_principle[criterion["principle"].value].append(criterion)

        # Group issues by principle
        issues_by_principle = defaultdict(list)
        for issue in issues:
            principle = issue.get("principle", Principle.PERCEIVABLE.value)
            issues_by_principle[principle].append(issue)

        # Calculate score for each principle
        principle_scores = {}

        for principle_value in ["perceivable", "operable", "understandable", "robust"]:
            principle_criteria = criteria_by_principle.get(principle_value, [])
            principle_issues = issues_by_principle.get(principle_value, [])

            if principle_criteria:
                issue_weight = sum(
                    self.IMPACT_WEIGHTS.get(issue.get("impact", "moderate"), 2) *
                    self.LEVEL_WEIGHTS.get(issue.get("wcag_level", "AA"), 2)
                    for issue in principle_issues
                )

                total_weight = sum(
                    self.IMPACT_WEIGHTS[ImpactLevel.SERIOUS.value] *
                    self.LEVEL_WEIGHTS.get(c["level"].value, 2)
                    for c in principle_criteria
                )

                if total_weight > 0:
                    score = max(0, (1 - (issue_weight / total_weight)) * 100)
                else:
                    score = 100.0

                principle_scores[principle_value] = round(score, 2)
            else:
                principle_scores[principle_value] = 100.0

        return principle_scores

    def _is_level_applicable(self, issue_level: str, target_level: WCAGLevel) -> bool:
        """
        Check if issue level is applicable to target level.

        Args:
            issue_level: Issue WCAG level
            target_level: Target WCAG level

        Returns:
            True if applicable
        """
        level_hierarchy = {
            "A": 1,
            "AA": 2,
            "AAA": 3,
        }

        issue_rank = level_hierarchy.get(issue_level, 2)
        target_rank = level_hierarchy.get(target_level.value, 2)

        return issue_rank <= target_rank

    def get_compliance_level(self, score: float, critical_issues: int) -> str:
        """
        Determine compliance level based on score and critical issues.

        Args:
            score: Compliance score (0-100)
            critical_issues: Number of critical issues

        Returns:
            Compliance level description
        """
        # Must have zero critical issues for compliance
        if critical_issues > 0:
            return "non-compliant"

        if score >= 95:
            return "AAA"
        elif score >= 85:
            return "AA"
        elif score >= 75:
            return "A"
        else:
            return "non-compliant"


# Global instance
compliance_scorer = ComplianceScorer()
