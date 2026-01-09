"""Logging configuration for WCAG Scanner."""

import logging
import sys
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

from src.utils.config import get_config

# Console for rich output
console = Console()


def setup_logger(
    name: str = "wcag_scanner",
    level: Optional[str] = None
) -> logging.Logger:
    """
    Set up and return a configured logger.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    config = get_config()
    log_level = level or config.log_level

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create rich handler for console output
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True
    )
    rich_handler.setLevel(getattr(logging, log_level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    rich_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(rich_handler)

    return logger


# Default logger instance
logger = setup_logger()


def get_logger(name: str = "wcag_scanner") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
