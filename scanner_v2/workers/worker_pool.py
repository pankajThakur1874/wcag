"""Worker pool manager for managing multiple scan workers."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import generate_id
from scanner_v2.workers.queue_manager import QueueManager, get_queue_manager
from scanner_v2.workers.scan_worker import ScanWorker

logger = get_logger("worker_pool")


class WorkerPool:
    """Manages a pool of scan workers."""

    def __init__(
        self,
        worker_count: int = 5,
        job_timeout: int = 300,
        queue_manager: Optional[QueueManager] = None
    ):
        """
        Initialize worker pool.

        Args:
            worker_count: Number of workers to spawn
            job_timeout: Job timeout in seconds
            queue_manager: Queue manager instance (optional)
        """
        self.worker_count = worker_count
        self.job_timeout = job_timeout
        self.queue_manager = queue_manager or get_queue_manager()

        self.workers: List[ScanWorker] = []
        self.is_running = False
        self.cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"Worker pool initialized (workers={worker_count})")

    async def start(self) -> None:
        """Start the worker pool."""
        if self.is_running:
            logger.warning("Worker pool already running")
            return

        self.is_running = True

        # Create and start workers
        for i in range(self.worker_count):
            worker_id = f"worker-{i+1}"
            worker = ScanWorker(
                worker_id=worker_id,
                queue_manager=self.queue_manager,
                job_timeout=self.job_timeout
            )

            self.workers.append(worker)
            await worker.start()

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info(f"Worker pool started with {self.worker_count} workers")

    async def stop(self) -> None:
        """Stop the worker pool gracefully."""
        if not self.is_running:
            return

        self.is_running = False

        logger.info("Stopping worker pool...")

        # Stop cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop all workers
        stop_tasks = [worker.stop() for worker in self.workers]
        await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.info("Worker pool stopped")

    async def scale(self, new_count: int) -> None:
        """
        Scale the worker pool.

        Args:
            new_count: New worker count
        """
        if not self.is_running:
            logger.warning("Worker pool not running, cannot scale")
            return

        current_count = len(self.workers)

        if new_count > current_count:
            # Add workers
            for i in range(new_count - current_count):
                worker_id = f"worker-{current_count + i + 1}"
                worker = ScanWorker(
                    worker_id=worker_id,
                    queue_manager=self.queue_manager,
                    job_timeout=self.job_timeout
                )

                self.workers.append(worker)
                await worker.start()

            logger.info(f"Scaled up from {current_count} to {new_count} workers")

        elif new_count < current_count:
            # Remove workers
            workers_to_remove = self.workers[new_count:]
            self.workers = self.workers[:new_count]

            # Stop removed workers
            stop_tasks = [worker.stop() for worker in workers_to_remove]
            await asyncio.gather(*stop_tasks, return_exceptions=True)

            logger.info(f"Scaled down from {current_count} to {new_count} workers")

    def get_status(self) -> Dict[str, Any]:
        """
        Get worker pool status.

        Returns:
            Status dictionary
        """
        worker_statuses = [worker.get_status() for worker in self.workers]

        active_workers = sum(1 for w in worker_statuses if w["is_running"])
        busy_workers = sum(1 for w in worker_statuses if w["current_job"] is not None)

        return {
            "is_running": self.is_running,
            "worker_count": len(self.workers),
            "active_workers": active_workers,
            "busy_workers": busy_workers,
            "idle_workers": active_workers - busy_workers,
            "workers": worker_statuses,
            "queue_stats": self.queue_manager.get_stats(),
        }

    def get_health(self) -> Dict[str, Any]:
        """
        Get worker pool health.

        Returns:
            Health dictionary
        """
        status = self.get_status()

        # Determine health status
        if not status["is_running"]:
            health_status = "stopped"
        elif status["active_workers"] == 0:
            health_status = "unhealthy"
        elif status["active_workers"] < self.worker_count * 0.5:
            health_status = "degraded"
        else:
            health_status = "healthy"

        return {
            "status": health_status,
            "active_workers": status["active_workers"],
            "total_workers": self.worker_count,
            "queue_sizes": status["queue_stats"],
        }

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup old completed jobs."""
        logger.info("Cleanup loop started")

        while self.is_running:
            try:
                # Wait 5 minutes between cleanups
                await asyncio.sleep(300)

                # Clear old completed jobs (older than 1 hour)
                cleared = await self.queue_manager.clear_completed_jobs(max_age_seconds=3600)

                if cleared > 0:
                    logger.info(f"Cleanup: removed {cleared} old jobs")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

        logger.info("Cleanup loop stopped")


# Global worker pool instance
_worker_pool: Optional[WorkerPool] = None


async def init_worker_pool(
    worker_count: int = 5,
    job_timeout: int = 300,
    queue_manager: Optional[QueueManager] = None
) -> WorkerPool:
    """
    Initialize global worker pool.

    Args:
        worker_count: Number of workers
        job_timeout: Job timeout in seconds
        queue_manager: Optional queue manager

    Returns:
        WorkerPool instance
    """
    global _worker_pool

    if _worker_pool is not None:
        logger.warning("Worker pool already initialized")
        return _worker_pool

    _worker_pool = WorkerPool(
        worker_count=worker_count,
        job_timeout=job_timeout,
        queue_manager=queue_manager
    )

    await _worker_pool.start()

    return _worker_pool


async def stop_worker_pool() -> None:
    """Stop global worker pool."""
    global _worker_pool

    if _worker_pool:
        await _worker_pool.stop()
        _worker_pool = None


def get_worker_pool() -> Optional[WorkerPool]:
    """
    Get global worker pool instance.

    Returns:
        WorkerPool instance or None
    """
    return _worker_pool
