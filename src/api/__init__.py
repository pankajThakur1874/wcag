"""API module for WCAG Scanner."""

from src.api.app import app
from src.api.routes import router

__all__ = ["app", "router"]
