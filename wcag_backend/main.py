"""Main entry point for WCAG Backend API v2."""

import uvicorn

from wcag_backend.utils.config import get_config


if __name__ == "__main__":
    # Load configuration
    config = get_config()

    # Run server
    uvicorn.run(
        "wcag_backend.api.app:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.logging.level.lower()
    )
