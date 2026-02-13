"""FastAPI application setup with lifespan management."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from wcag_backend.api.middleware import setup_middleware
from wcag_backend.api.routes import auth, dashboard, projects, scans, issues, reports
from wcag_backend.database.connection import MongoDB, set_mongodb_instance
from wcag_backend.workers.queue_manager import QueueManager, set_queue_manager
from wcag_backend.workers.worker_pool import WorkerPool
from wcag_backend.utils.config import get_config
from wcag_backend.utils.logger import setup_logging, get_logger

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting WCAG Backend API v2...")

    # Load configuration
    config = get_config()

    # Setup logging
    setup_logging(
        level=config.logging.level,
        format_type=config.logging.format
    )

    # Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    mongodb = MongoDB(config)
    await mongodb.connect()
    set_mongodb_instance(mongodb)
    logger.info("MongoDB connected")

    # Initialize queue manager
    logger.info("Initializing queue manager...")
    queue_manager = QueueManager(max_queue_size=config.queue.max_queue_size)
    set_queue_manager(queue_manager)
    logger.info("Queue manager initialized")

    # Start worker pool
    logger.info(f"Starting worker pool with {config.queue.worker_count} workers...")
    worker_pool = WorkerPool(queue_manager, worker_count=config.queue.worker_count)
    await worker_pool.start()
    logger.info("Worker pool started")

    logger.info("✓ WCAG Backend API v2 startup complete")

    yield

    # Shutdown
    logger.info("Shutting down WCAG Backend API v2...")

    # Stop worker pool
    logger.info("Stopping worker pool...")
    await worker_pool.stop()
    logger.info("Worker pool stopped")

    # Disconnect from MongoDB
    logger.info("Disconnecting from MongoDB...")
    await mongodb.disconnect()
    logger.info("MongoDB disconnected")

    logger.info("✓ WCAG Backend API v2 shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="WCAG Backend API v2",
        description="""
        Production-ready WCAG accessibility scanner backend API.

        ## Features
        - JWT authentication with refresh token rotation
        - User and project management
        - Async scan processing with background workers
        - Issue tracking and status management
        - Multi-format report generation (HTML/JSON/CSV)
        - Dashboard statistics and analytics

        ## Authentication
        All endpoints (except /auth/*) require a valid JWT access token in the Authorization header:
        ```
        Authorization: Bearer <access_token>
        ```
        """,
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Setup middleware
    setup_middleware(app)

    # Include routers with /api/v2 prefix
    app.include_router(auth.router, prefix="/api/v2")
    app.include_router(dashboard.router, prefix="/api/v2")
    app.include_router(projects.router, prefix="/api/v2")
    app.include_router(scans.router, prefix="/api/v2")
    app.include_router(issues.router, prefix="/api/v2")
    app.include_router(reports.router, prefix="/api/v2")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "2.0.0",
            "api": "wcag-backend"
        }

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "WCAG Backend API v2",
            "docs": "/docs",
            "health": "/health"
        }

    return app


# Create app instance
app = create_app()
