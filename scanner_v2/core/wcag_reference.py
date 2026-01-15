"""WCAG 2.2 Success Criteria Reference Data."""

from typing import List, Dict, Optional
from scanner_v2.database.models import WCAGLevel, Principle, AutomationLevel

# WCAG 2.2 Success Criteria (86 total)
WCAG_CRITERIA = [
    # Principle 1: Perceivable
    # Guideline 1.1: Text Alternatives
    {"id": "1.1.1", "name": "Non-text Content", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.1 Text Alternatives", "automation": AutomationLevel.PARTIALLY_AUTOMATED},

    # Guideline 1.2: Time-based Media
    {"id": "1.2.1", "name": "Audio-only and Video-only (Prerecorded)", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.2", "name": "Captions (Prerecorded)", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.3", "name": "Audio Description or Media Alternative (Prerecorded)", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.4", "name": "Captions (Live)", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.5", "name": "Audio Description (Prerecorded)", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.6", "name": "Sign Language (Prerecorded)", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.7", "name": "Extended Audio Description (Prerecorded)", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.8", "name": "Media Alternative (Prerecorded)", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},
    {"id": "1.2.9", "name": "Audio-only (Live)", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.2 Time-based Media", "automation": AutomationLevel.MANUAL},

    # Guideline 1.3: Adaptable
    {"id": "1.3.1", "name": "Info and Relationships", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.3 Adaptable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.3.2", "name": "Meaningful Sequence", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.3 Adaptable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.3.3", "name": "Sensory Characteristics", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.3 Adaptable", "automation": AutomationLevel.MANUAL},
    {"id": "1.3.4", "name": "Orientation", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.3 Adaptable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.3.5", "name": "Identify Input Purpose", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.3 Adaptable", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "1.3.6", "name": "Identify Purpose", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.3 Adaptable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},

    # Guideline 1.4: Distinguishable
    {"id": "1.4.1", "name": "Use of Color", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.MANUAL},
    {"id": "1.4.2", "name": "Audio Control", "level": WCAGLevel.A, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.4.3", "name": "Contrast (Minimum)", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "1.4.4", "name": "Resize Text", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.4.5", "name": "Images of Text", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.MANUAL},
    {"id": "1.4.6", "name": "Contrast (Enhanced)", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "1.4.7", "name": "Low or No Background Audio", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.MANUAL},
    {"id": "1.4.8", "name": "Visual Presentation", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.4.9", "name": "Images of Text (No Exception)", "level": WCAGLevel.AAA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.MANUAL},
    {"id": "1.4.10", "name": "Reflow", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.4.11", "name": "Non-text Contrast", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "1.4.12", "name": "Text Spacing", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "1.4.13", "name": "Content on Hover or Focus", "level": WCAGLevel.AA, "principle": Principle.PERCEIVABLE, "guideline": "1.4 Distinguishable", "automation": AutomationLevel.MANUAL},

    # Principle 2: Operable
    # Guideline 2.1: Keyboard Accessible
    {"id": "2.1.1", "name": "Keyboard", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.1 Keyboard Accessible", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.1.2", "name": "No Keyboard Trap", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.1 Keyboard Accessible", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.1.3", "name": "Keyboard (No Exception)", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.1 Keyboard Accessible", "automation": AutomationLevel.MANUAL},
    {"id": "2.1.4", "name": "Character Key Shortcuts", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.1 Keyboard Accessible", "automation": AutomationLevel.MANUAL},

    # Guideline 2.2: Enough Time
    {"id": "2.2.1", "name": "Timing Adjustable", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.2 Enough Time", "automation": AutomationLevel.MANUAL},
    {"id": "2.2.2", "name": "Pause, Stop, Hide", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.2 Enough Time", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.2.3", "name": "No Timing", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.2 Enough Time", "automation": AutomationLevel.MANUAL},
    {"id": "2.2.4", "name": "Interruptions", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.2 Enough Time", "automation": AutomationLevel.MANUAL},
    {"id": "2.2.5", "name": "Re-authenticating", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.2 Enough Time", "automation": AutomationLevel.MANUAL},
    {"id": "2.2.6", "name": "Timeouts", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.2 Enough Time", "automation": AutomationLevel.MANUAL},

    # Guideline 2.3: Seizures and Physical Reactions
    {"id": "2.3.1", "name": "Three Flashes or Below Threshold", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.3 Seizures", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.3.2", "name": "Three Flashes", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.3 Seizures", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.3.3", "name": "Animation from Interactions", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.3 Seizures", "automation": AutomationLevel.MANUAL},

    # Guideline 2.4: Navigable
    {"id": "2.4.1", "name": "Bypass Blocks", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.4.2", "name": "Page Titled", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "2.4.3", "name": "Focus Order", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.4.4", "name": "Link Purpose (In Context)", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.4.5", "name": "Multiple Ways", "level": WCAGLevel.AA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.MANUAL},
    {"id": "2.4.6", "name": "Headings and Labels", "level": WCAGLevel.AA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.4.7", "name": "Focus Visible", "level": WCAGLevel.AA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.4.8", "name": "Location", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.MANUAL},
    {"id": "2.4.9", "name": "Link Purpose (Link Only)", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.4.10", "name": "Section Headings", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.4.11", "name": "Focus Not Obscured (Minimum)", "level": WCAGLevel.AA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.MANUAL},
    {"id": "2.4.12", "name": "Focus Not Obscured (Enhanced)", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.MANUAL},
    {"id": "2.4.13", "name": "Focus Appearance", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.4 Navigable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},

    # Guideline 2.5: Input Modalities
    {"id": "2.5.1", "name": "Pointer Gestures", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.MANUAL},
    {"id": "2.5.2", "name": "Pointer Cancellation", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.MANUAL},
    {"id": "2.5.3", "name": "Label in Name", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.5.4", "name": "Motion Actuation", "level": WCAGLevel.A, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.MANUAL},
    {"id": "2.5.5", "name": "Target Size (Enhanced)", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "2.5.6", "name": "Concurrent Input Mechanisms", "level": WCAGLevel.AAA, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.MANUAL},
    {"id": "2.5.7", "name": "Dragging Movements", "level": WCAGLevel.AA, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.MANUAL},
    {"id": "2.5.8", "name": "Target Size (Minimum)", "level": WCAGLevel.AA, "principle": Principle.OPERABLE, "guideline": "2.5 Input Modalities", "automation": AutomationLevel.PARTIALLY_AUTOMATED},

    # Principle 3: Understandable
    # Guideline 3.1: Readable
    {"id": "3.1.1", "name": "Language of Page", "level": WCAGLevel.A, "principle": Principle.UNDERSTANDABLE, "guideline": "3.1 Readable", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "3.1.2", "name": "Language of Parts", "level": WCAGLevel.AA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.1 Readable", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "3.1.3", "name": "Unusual Words", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.1 Readable", "automation": AutomationLevel.MANUAL},
    {"id": "3.1.4", "name": "Abbreviations", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.1 Readable", "automation": AutomationLevel.MANUAL},
    {"id": "3.1.5", "name": "Reading Level", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.1 Readable", "automation": AutomationLevel.MANUAL},
    {"id": "3.1.6", "name": "Pronunciation", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.1 Readable", "automation": AutomationLevel.MANUAL},

    # Guideline 3.2: Predictable
    {"id": "3.2.1", "name": "On Focus", "level": WCAGLevel.A, "principle": Principle.UNDERSTANDABLE, "guideline": "3.2 Predictable", "automation": AutomationLevel.MANUAL},
    {"id": "3.2.2", "name": "On Input", "level": WCAGLevel.A, "principle": Principle.UNDERSTANDABLE, "guideline": "3.2 Predictable", "automation": AutomationLevel.MANUAL},
    {"id": "3.2.3", "name": "Consistent Navigation", "level": WCAGLevel.AA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.2 Predictable", "automation": AutomationLevel.MANUAL},
    {"id": "3.2.4", "name": "Consistent Identification", "level": WCAGLevel.AA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.2 Predictable", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "3.2.5", "name": "Change on Request", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.2 Predictable", "automation": AutomationLevel.MANUAL},
    {"id": "3.2.6", "name": "Consistent Help", "level": WCAGLevel.A, "principle": Principle.UNDERSTANDABLE, "guideline": "3.2 Predictable", "automation": AutomationLevel.MANUAL},

    # Guideline 3.3: Input Assistance
    {"id": "3.3.1", "name": "Error Identification", "level": WCAGLevel.A, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "3.3.2", "name": "Labels or Instructions", "level": WCAGLevel.A, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "3.3.3", "name": "Error Suggestion", "level": WCAGLevel.AA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.MANUAL},
    {"id": "3.3.4", "name": "Error Prevention (Legal, Financial, Data)", "level": WCAGLevel.AA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.MANUAL},
    {"id": "3.3.5", "name": "Help", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.MANUAL},
    {"id": "3.3.6", "name": "Error Prevention (All)", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.MANUAL},
    {"id": "3.3.7", "name": "Redundant Entry", "level": WCAGLevel.A, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.MANUAL},
    {"id": "3.3.8", "name": "Accessible Authentication (Minimum)", "level": WCAGLevel.AA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.MANUAL},
    {"id": "3.3.9", "name": "Accessible Authentication (Enhanced)", "level": WCAGLevel.AAA, "principle": Principle.UNDERSTANDABLE, "guideline": "3.3 Input Assistance", "automation": AutomationLevel.MANUAL},

    # Principle 4: Robust
    # Guideline 4.1: Compatible
    {"id": "4.1.1", "name": "Parsing", "level": WCAGLevel.A, "principle": Principle.ROBUST, "guideline": "4.1 Compatible", "automation": AutomationLevel.FULLY_AUTOMATED},
    {"id": "4.1.2", "name": "Name, Role, Value", "level": WCAGLevel.A, "principle": Principle.ROBUST, "guideline": "4.1 Compatible", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
    {"id": "4.1.3", "name": "Status Messages", "level": WCAGLevel.AA, "principle": Principle.ROBUST, "guideline": "4.1 Compatible", "automation": AutomationLevel.PARTIALLY_AUTOMATED},
]


class WCAGReference:
    """WCAG criteria reference and lookup."""

    def __init__(self):
        """Initialize WCAG reference."""
        self.criteria = {item["id"]: item for item in WCAG_CRITERIA}

    def get_criterion(self, criterion_id: str) -> Optional[Dict]:
        """
        Get WCAG criterion by ID.

        Args:
            criterion_id: Criterion ID (e.g., "1.1.1")

        Returns:
            Criterion data or None
        """
        return self.criteria.get(criterion_id)

    def get_all_criteria(self) -> List[Dict]:
        """
        Get all WCAG criteria.

        Returns:
            List of all criteria
        """
        return WCAG_CRITERIA

    def get_criteria_by_level(self, level: WCAGLevel) -> List[Dict]:
        """
        Get criteria by WCAG level.

        Args:
            level: WCAG level (A, AA, AAA)

        Returns:
            List of criteria at that level
        """
        return [c for c in WCAG_CRITERIA if c["level"] == level]

    def get_criteria_by_principle(self, principle: Principle) -> List[Dict]:
        """
        Get criteria by principle.

        Args:
            principle: WCAG principle

        Returns:
            List of criteria for that principle
        """
        return [c for c in WCAG_CRITERIA if c["principle"] == principle]

    def get_automated_criteria(self) -> List[Dict]:
        """
        Get fully automated criteria.

        Returns:
            List of fully automated criteria
        """
        return [c for c in WCAG_CRITERIA if c["automation"] == AutomationLevel.FULLY_AUTOMATED]

    def get_manual_criteria(self) -> List[Dict]:
        """
        Get manual-only criteria.

        Returns:
            List of manual criteria
        """
        return [c for c in WCAG_CRITERIA if c["automation"] == AutomationLevel.MANUAL]

    def get_criterion_url(self, criterion_id: str) -> str:
        """
        Get W3C URL for criterion.

        Args:
            criterion_id: Criterion ID

        Returns:
            W3C understanding URL
        """
        return f"https://www.w3.org/WAI/WCAG22/Understanding/{criterion_id.replace('.', '')}"

    def get_automation_percentage(self, level: WCAGLevel = WCAGLevel.AA) -> Dict[str, float]:
        """
        Calculate automation percentage for WCAG level.

        Args:
            level: WCAG level to calculate for

        Returns:
            Dictionary with automation statistics
        """
        # Get criteria up to specified level
        criteria = []
        for c in WCAG_CRITERIA:
            if level == WCAGLevel.AAA or \
               (level == WCAGLevel.AA and c["level"] in [WCAGLevel.A, WCAGLevel.AA]) or \
               (level == WCAGLevel.A and c["level"] == WCAGLevel.A):
                criteria.append(c)

        total = len(criteria)
        fully_auto = sum(1 for c in criteria if c["automation"] == AutomationLevel.FULLY_AUTOMATED)
        partially_auto = sum(1 for c in criteria if c["automation"] == AutomationLevel.PARTIALLY_AUTOMATED)
        manual = sum(1 for c in criteria if c["automation"] == AutomationLevel.MANUAL)

        return {
            "total": total,
            "fully_automated": fully_auto,
            "partially_automated": partially_auto,
            "manual": manual,
            "fully_automated_percentage": (fully_auto / total) * 100,
            "partially_automated_percentage": (partially_auto / total) * 100,
            "manual_percentage": (manual / total) * 100,
        }


# Global instance
wcag_reference = WCAGReference()
