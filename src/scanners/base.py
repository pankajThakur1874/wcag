"""Base scanner class for WCAG Scanner."""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
import time

from src.models import Violation, ToolStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseScanner(ABC):
    """Abstract base class for all accessibility scanners."""

    name: str = "base"
    version: str = "1.0.0"

    def __init__(self):
        self._start_time: Optional[float] = None
        self._violations: list[Violation] = []
        self._passes: int = 0
        self._error: Optional[str] = None

    @abstractmethod
    async def scan(self, url: str, html_content: Optional[str] = None) -> list[Violation]:
        """
        Perform accessibility scan.

        Args:
            url: URL to scan
            html_content: Optional pre-fetched HTML content

        Returns:
            List of violations found
        """
        pass

    async def run(self, url: str, html_content: Optional[str] = None) -> tuple[list[Violation], ToolStatus]:
        """
        Run the scanner and return results with status.

        Args:
            url: URL to scan
            html_content: Optional pre-fetched HTML content

        Returns:
            Tuple of (violations, tool_status)
        """
        self._start_time = time.time()
        self._violations = []
        self._error = None

        try:
            logger.info(f"Starting {self.name} scan for {url}")
            self._violations = await self.scan(url, html_content)
            logger.info(f"{self.name} found {len(self._violations)} violations")

            return self._violations, self._get_status()

        except Exception as e:
            self._error = str(e)
            logger.error(f"{self.name} scan failed: {e}")
            return [], self._get_status()

    def _get_status(self) -> ToolStatus:
        """Get the tool status after a scan."""
        duration_ms = None
        if self._start_time:
            duration_ms = int((time.time() - self._start_time) * 1000)

        return ToolStatus(
            name=self.name,
            version=self.version,
            status="success" if not self._error else "error",
            rules_checked=None,
            error=self._error,
            duration_ms=duration_ms
        )

    @property
    def passes(self) -> int:
        """Get number of passing checks."""
        return self._passes
