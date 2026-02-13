"""Scanners for WCAG accessibility testing."""

from src.scanners.base import BaseScanner
from src.scanners.axe_scanner import AxeScanner
from src.scanners.pa11y_scanner import Pa11yScanner
from src.scanners.lighthouse_scanner import LighthouseScanner
from src.scanners.html_validator import HTMLValidatorScanner
from src.scanners.contrast_checker import ContrastChecker
from src.scanners.keyboard_scanner import KeyboardScanner
from src.scanners.aria_scanner import ARIAScanner
from src.scanners.seo_scanner import SEOAccessibilityScanner
from src.scanners.forms_scanner import FormsScanner
from src.scanners.link_text_scanner import LinkTextScanner
from src.scanners.image_alt_scanner import ImageAltScanner
from src.scanners.media_scanner import MediaScanner
from src.scanners.touch_target_scanner import TouchTargetScanner
from src.scanners.readability_scanner import ReadabilityScanner
from src.scanners.interactive_scanner import InteractiveScanner

# New custom WCAG 2.2 scanners
from src.scanners.color_only_scanner import ColorOnlyScanner
from src.scanners.hover_content_scanner import HoverContentScanner
from src.scanners.multiple_ways_scanner import MultipleWaysScanner
from src.scanners.pointer_gestures_scanner import PointerGesturesScanner
from src.scanners.consistent_navigation_scanner import ConsistentNavigationScanner
from src.scanners.character_shortcuts_scanner import CharacterShortcutsScanner
from src.scanners.focus_obscured_scanner import FocusObscuredScanner
from src.scanners.media_accessibility_scanner import MediaAccessibilityScanner

__all__ = [
    "BaseScanner",
    "AxeScanner",
    "Pa11yScanner",
    "LighthouseScanner",
    "HTMLValidatorScanner",
    "ContrastChecker",
    "KeyboardScanner",
    "ARIAScanner",
    "SEOAccessibilityScanner",
    "FormsScanner",
    "LinkTextScanner",
    "ImageAltScanner",
    "MediaScanner",
    "TouchTargetScanner",
    "ReadabilityScanner",
    "InteractiveScanner",
    # New custom scanners
    "ColorOnlyScanner",
    "HoverContentScanner",
    "MultipleWaysScanner",
    "PointerGesturesScanner",
    "ConsistentNavigationScanner",
    "CharacterShortcutsScanner",
    "FocusObscuredScanner",
    "MediaAccessibilityScanner"
]

# Scanner registry - all available scanners
SCANNERS = {
    "axe": AxeScanner,
    "pa11y": Pa11yScanner,
    "lighthouse": LighthouseScanner,
    "html_validator": HTMLValidatorScanner,
    "contrast": ContrastChecker,
    "keyboard": KeyboardScanner,
    "aria": ARIAScanner,
    "seo": SEOAccessibilityScanner,
    "forms": FormsScanner,
    "link_text": LinkTextScanner,
    "image_alt": ImageAltScanner,
    "media": MediaScanner,
    "touch_target": TouchTargetScanner,
    "readability": ReadabilityScanner,
    "interactive": InteractiveScanner,
    # New custom WCAG 2.2 scanners
    "color_only": ColorOnlyScanner,
    "hover_content": HoverContentScanner,
    "multiple_ways": MultipleWaysScanner,
    "pointer_gestures": PointerGesturesScanner,
    "consistent_navigation": ConsistentNavigationScanner,
    "character_shortcuts": CharacterShortcutsScanner,
    "focus_obscured": FocusObscuredScanner,
    "media_accessibility": MediaAccessibilityScanner
}

# Default scanners to run (fast and reliable)
DEFAULT_SCANNERS = [
    "axe", "html_validator", "contrast", "keyboard", "aria", "forms", "seo",
    "link_text", "image_alt", "media", "touch_target", "readability", "interactive"
]

# Enhanced scanner set with custom WCAG 2.2 scanners
ENHANCED_SCANNERS = DEFAULT_SCANNERS + [
    "color_only", "hover_content", "multiple_ways", "pointer_gestures",
    "consistent_navigation", "character_shortcuts", "focus_obscured", "media_accessibility"
]

# All scanners including external tools
ALL_SCANNERS = list(SCANNERS.keys())


def get_scanner(name: str) -> type[BaseScanner]:
    """Get a scanner class by name."""
    if name not in SCANNERS:
        raise ValueError(f"Unknown scanner: {name}. Available: {list(SCANNERS.keys())}")
    return SCANNERS[name]


def get_default_scanners() -> list[str]:
    """Get list of default scanner names."""
    return DEFAULT_SCANNERS.copy()


def get_all_scanners() -> list[str]:
    """Get list of all scanner names."""
    return ALL_SCANNERS.copy()
