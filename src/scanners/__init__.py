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
    "FormsScanner"
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
    "forms": FormsScanner
}

# Default scanners to run (fast and reliable)
DEFAULT_SCANNERS = ["axe", "html_validator", "contrast", "keyboard", "aria", "forms", "seo"]

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
