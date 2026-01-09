"""
WCAG Accessibility Scanner - Main Entry Point

This file provides both CLI and API interfaces for the scanner.

Usage:
    CLI:     python -m src.cli scan https://example.com
    API:     uvicorn main:app --reload
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import FastAPI app for uvicorn
from src.api.app import app

# Re-export app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    from src.utils.config import get_config

    config = get_config()
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True
    )
