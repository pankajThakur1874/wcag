#!/usr/bin/env python3
"""Entry point for WCAG Scanner V2 API server."""

import sys
from pathlib import Path

# Add scanner_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from scanner_v2.utils.config import load_config

    # Load configuration
    config = load_config()

    # Run server
    uvicorn.run(
        "scanner_v2.api.app:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.logging.level.lower(),
    )
