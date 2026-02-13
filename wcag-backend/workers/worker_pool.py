"""Worker pool for processing background jobs."""

import asyncio
from typing import List, Optional
import signal

from wcag_backend.workers.queue_manager import QueueManager
from wcag_backend.workers.scan_worker import ScanWorker
from wcag_backend.utils.logger import get_logger

logger = get_logger("worker_pool")


class WorkerPool:
    """Manages a pool of worker coroutines."""

    def __init__(self, queue_manager: QueueManager, worker_count: int = 5):
        """
        Initialize worker pool.

        Args:
            queue_manager: Queue manager instance
            worker_count: Number of workers to create
        """
        self.queue_manager = queue_manager
        self.worker_count = worker_count
        self.workers: List[asyncio.Task] = []
        self.running = False

    async def start(self) -> None:
        """Start all workers."""
        if self.running:
            logger.warning("Worker pool already running")
            return

        logger.info(f"Starting worker pool with {self.worker_count} workers")

        self.running = True

        # Create and start worker tasks
        for i in range(self.worker_count):
            worker = ScanWorker(
                worker_id=f"worker-{i+1}",
                queue_manager=self.queue_manager
            )

            task = asyncio.create_task(worker.run())
            self.workers.append(task)

        logger.info(f"Worker pool started with {len(self.workers)} workers")

    async def stop(self) -> None:
        """Stop all workers gracefully."""
        if not self.running:
            logger.warning("Worker pool not running")
            return

        logger.info("Stopping worker pool...")

        self.running = False

        # Cancel all worker tasks
        for task in self.workers:
            task.cancel()

        # Wait for all tasks to complete
        await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers.clear()

        logger.info("Worker pool stopped")

    async def get_status(self) -> dict:
        """
        Get worker pool status.

        Returns:
            Dictionary with status information
        """
        return {
            "running": self.running,
            "worker_count": self.worker_count,
            "active_workers": len([w for w in self.workers if not w.done()]),
            "queue_size": await self.queue_manager.get_queue_size()
        }
