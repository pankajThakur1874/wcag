"""Scanners for WCAG accessibility testing."""

from src.scanners.base import BaseScanner
from src.scanners.axe_scanner import AxeScanner
from src.scanners.pa11y_scanner import Pa11yScanner
from src.scanners.lighthouse_scanner import LighthouseScanner
from src.scanners.html_validator import HTMLValidatorScanner
from src.scanners.contrast_checker import ContrastChecker

__all__ = [
    "BaseScanner",
    "AxeScanner",
    "Pa11yScanner",
    "LighthouseScanner",
    "HTMLValidatorScanner",
    "ContrastChecker"
]

# Scanner registry
SCANNERS = {
    "axe": AxeScanner,
    "pa11y": Pa11yScanner,
    "lighthouse": LighthouseScanner,
    "html_validator": HTMLValidatorScanner,
    "contrast": ContrastChecker
}


def get_scanner(name: str) -> type[BaseScanner]:
    """Get a scanner class by name."""
    if name not in SCANNERS:
        raise ValueError(f"Unknown scanner: {name}. Available: {list(SCANNERS.keys())}")
    return SCANNERS[name]
