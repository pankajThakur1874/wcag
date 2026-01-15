"""FastAPI application initialization."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from scanner_v2.utils.config import get_config, load_config
from scanner_v2.utils.logger import setup_logging, get_logger
from scanner_v2.database.connection import MongoDB
from scanner_v2.workers.queue_manager import QueueManager
from scanner_v2.workers.worker_pool import WorkerPool
from scanner_v2.api.dependencies import set_db_instance, set_queue_manager_instance
from scanner_v2.api.middleware import setup_middleware
from scanner_v2.api.routes import health, auth, projects, scans, issues, reports

logger = get_logger("api.app")

# Global instances
_db: MongoDB = None
_queue_manager: QueueManager = None
_worker_pool: WorkerPool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown events.
    """
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(level=config.logging.level, format_type=config.logging.format)

    logger.info("Starting WCAG Scanner V2 API...")

    # Initialize MongoDB
    global _db
    _db = MongoDB(config)
    await _db.connect()
    set_db_instance(_db)
    logger.info("MongoDB connected")

    # Initialize Queue Manager
    global _queue_manager
    _queue_manager = QueueManager(config)
    set_queue_manager_instance(_queue_manager)
    logger.info("Queue manager initialized")

    # Initialize Worker Pool
    global _worker_pool
    _worker_pool = WorkerPool(
        queue_manager=_queue_manager,
        worker_count=config.queue.worker_count,
        job_timeout=config.queue.job_timeout
    )
    await _worker_pool.start()
    logger.info(f"Worker pool started with {config.queue.worker_count} workers")

    logger.info("WCAG Scanner V2 API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down WCAG Scanner V2 API...")

    # Stop worker pool
    if _worker_pool:
        await _worker_pool.stop()
        logger.info("Worker pool stopped")

    # Disconnect MongoDB
    if _db:
        await _db.disconnect()
        logger.info("MongoDB disconnected")

    logger.info("WCAG Scanner V2 API shut down successfully")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="WCAG Scanner V2 API",
        description="Production-ready WCAG compliance scanner with FastAPI backend",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Setup middleware
    setup_middleware(app)

    # Include routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(scans.router, prefix="/api/v1")
    app.include_router(issues.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")

    logger.info("FastAPI application created")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    config = get_config()

    uvicorn.run(
        "scanner_v2.api.app:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.logging.level.lower(),
    )
