"""Violation models for WCAG Scanner."""

from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class Impact(str, Enum):
    """Impact level of a violation."""
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class WCAGLevel(str, Enum):
    """WCAG conformance level."""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class ViolationInstance(BaseModel):
    """Individual instance of a violation."""
    html: str = Field(description="HTML snippet of the violating element")
    selector: str = Field(description="CSS selector for the element")
    xpath: Optional[str] = Field(default=None, description="XPath for the element")
    fix_suggestion: Optional[str] = Field(default=None, description="Suggested fix")


class Violation(BaseModel):
    """Represents an accessibility violation."""
    id: str = Field(description="Unique violation identifier")
    rule_id: str = Field(description="Rule ID from the testing tool")
    wcag_criteria: list[str] = Field(default_factory=list, description="WCAG success criteria")
    wcag_level: Optional[WCAGLevel] = Field(default=None, description="WCAG level")
    impact: Impact = Field(description="Impact level")
    description: str = Field(description="Description of the violation")
    help_text: Optional[str] = Field(default=None, description="Help text for fixing")
    help_url: Optional[str] = Field(default=None, description="URL for more information")
    detected_by: list[str] = Field(default_factory=list, description="Tools that detected this")
    instances: list[ViolationInstance] = Field(default_factory=list, description="All instances")
    tags: list[str] = Field(default_factory=list, description="Additional tags")

    def add_detected_by(self, tool: str) -> None:
        """Add a tool to the detected_by list if not already present."""
        if tool not in self.detected_by:
            self.detected_by.append(tool)

    def merge_instances(self, other: "Violation") -> None:
        """Merge instances from another violation of the same type."""
        existing_selectors = {i.selector for i in self.instances}
        for instance in other.instances:
            if instance.selector not in existing_selectors:
                self.instances.append(instance)
                existing_selectors.add(instance.selector)


# WCAG criteria to level mapping
WCAG_CRITERIA_LEVELS: dict[str, WCAGLevel] = {
    # Level A
    "1.1.1": WCAGLevel.A,
    "1.2.1": WCAGLevel.A,
    "1.2.2": WCAGLevel.A,
    "1.2.3": WCAGLevel.A,
    "1.3.1": WCAGLevel.A,
    "1.3.2": WCAGLevel.A,
    "1.3.3": WCAGLevel.A,
    "1.4.1": WCAGLevel.A,
    "1.4.2": WCAGLevel.A,
    "2.1.1": WCAGLevel.A,
    "2.1.2": WCAGLevel.A,
    "2.1.4": WCAGLevel.A,
    "2.2.1": WCAGLevel.A,
    "2.2.2": WCAGLevel.A,
    "2.3.1": WCAGLevel.A,
    "2.4.1": WCAGLevel.A,
    "2.4.2": WCAGLevel.A,
    "2.4.3": WCAGLevel.A,
    "2.4.4": WCAGLevel.A,
    "2.5.1": WCAGLevel.A,
    "2.5.2": WCAGLevel.A,
    "2.5.3": WCAGLevel.A,
    "2.5.4": WCAGLevel.A,
    "3.1.1": WCAGLevel.A,
    "3.2.1": WCAGLevel.A,
    "3.2.2": WCAGLevel.A,
    "3.2.6": WCAGLevel.A,
    "3.3.1": WCAGLevel.A,
    "3.3.2": WCAGLevel.A,
    "3.3.7": WCAGLevel.A,
    "4.1.2": WCAGLevel.A,
    # Level AA
    "1.2.4": WCAGLevel.AA,
    "1.2.5": WCAGLevel.AA,
    "1.3.4": WCAGLevel.AA,
    "1.3.5": WCAGLevel.AA,
    "1.4.3": WCAGLevel.AA,
    "1.4.4": WCAGLevel.AA,
    "1.4.5": WCAGLevel.AA,
    "1.4.10": WCAGLevel.AA,
    "1.4.11": WCAGLevel.AA,
    "1.4.12": WCAGLevel.AA,
    "1.4.13": WCAGLevel.AA,
    "2.4.5": WCAGLevel.AA,
    "2.4.6": WCAGLevel.AA,
    "2.4.7": WCAGLevel.AA,
    "2.4.11": WCAGLevel.AA,
    "2.5.7": WCAGLevel.AA,
    "2.5.8": WCAGLevel.AA,
    "3.1.2": WCAGLevel.AA,
    "3.2.3": WCAGLevel.AA,
    "3.2.4": WCAGLevel.AA,
    "3.3.3": WCAGLevel.AA,
    "3.3.4": WCAGLevel.AA,
    "3.3.8": WCAGLevel.AA,
    "4.1.3": WCAGLevel.AA,
    # Level AAA
    "1.2.6": WCAGLevel.AAA,
    "1.2.7": WCAGLevel.AAA,
    "1.2.8": WCAGLevel.AAA,
    "1.2.9": WCAGLevel.AAA,
    "1.3.6": WCAGLevel.AAA,
    "1.4.6": WCAGLevel.AAA,
    "1.4.7": WCAGLevel.AAA,
    "1.4.8": WCAGLevel.AAA,
    "1.4.9": WCAGLevel.AAA,
    "2.1.3": WCAGLevel.AAA,
    "2.2.3": WCAGLevel.AAA,
    "2.2.4": WCAGLevel.AAA,
    "2.2.5": WCAGLevel.AAA,
    "2.2.6": WCAGLevel.AAA,
    "2.3.2": WCAGLevel.AAA,
    "2.3.3": WCAGLevel.AAA,
    "2.4.8": WCAGLevel.AAA,
    "2.4.9": WCAGLevel.AAA,
    "2.4.10": WCAGLevel.AAA,
    "2.4.12": WCAGLevel.AAA,
    "2.4.13": WCAGLevel.AAA,
    "2.5.5": WCAGLevel.AAA,
    "2.5.6": WCAGLevel.AAA,
    "3.1.3": WCAGLevel.AAA,
    "3.1.4": WCAGLevel.AAA,
    "3.1.5": WCAGLevel.AAA,
    "3.1.6": WCAGLevel.AAA,
    "3.2.5": WCAGLevel.AAA,
    "3.3.5": WCAGLevel.AAA,
    "3.3.6": WCAGLevel.AAA,
    "3.3.9": WCAGLevel.AAA,
}


def get_wcag_level(criteria: str) -> Optional[WCAGLevel]:
    """Get the WCAG level for a criteria."""
    return WCAG_CRITERIA_LEVELS.get(criteria)
