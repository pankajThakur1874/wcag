"""Health check routes."""

from typing import Annotated
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from scanner_v2.api.dependencies import get_database, get_queue_manager
from scanner_v2.workers.queue_manager import QueueManager
from scanner_v2.utils.logger import get_logger

logger = get_logger("api.routes.health")

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """
    Basic health check.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "WCAG Scanner V2"
    }


@router.get("/status")
async def system_status(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    queue_manager: Annotated[QueueManager, Depends(get_queue_manager)]
):
    """
    Detailed system status.

    Args:
        db: Database instance
        queue_manager: Queue manager instance

    Returns:
        System status including database, queue, and workers
    """
    # Check database
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database ping failed: {e}")
        db_status = "disconnected"

    # Get queue statistics
    queue_stats = queue_manager.get_statistics()

    return {
        "status": "healthy",
        "components": {
            "database": {
                "status": db_status,
                "type": "MongoDB"
            },
            "queue": {
                "status": "operational",
                "statistics": queue_stats
            }
        }
    }
