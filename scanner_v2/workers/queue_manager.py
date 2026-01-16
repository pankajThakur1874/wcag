"""In-memory queue manager using asyncio.Queue."""

import asyncio
from typing import Optional, Dict, Callable
from collections import defaultdict
from datetime import datetime

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import generate_id
from scanner_v2.schemas.scan import Job, JobType, JobStatus, JobPriority

logger = get_logger("queue_manager")


class QueueManager:
    """Manages in-memory job queues."""

    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize queue manager.

        Args:
            max_queue_size: Maximum queue size (0 = unlimited)
        """
        self.max_queue_size = max_queue_size

        # Separate queues for different job types
        self.orchestration_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.page_scan_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)

        # Job tracking
        self.jobs: Dict[str, Job] = {}
        self.job_callbacks: Dict[str, Callable] = {}

        # Statistics
        self.stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0,
        }

        # Counter for priority queue tie-breaking
        self._counter = 0

        logger.info(f"Queue manager initialized (max_size={max_queue_size})")

    async def enqueue_job(
        self,
        job_type: JobType,
        payload: Dict,
        priority: int = JobPriority.NORMAL.value,
        max_retries: int = 3,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Enqueue a new job.

        Args:
            job_type: Type of job
            payload: Job payload
            priority: Job priority
            max_retries: Maximum retry attempts
            callback: Optional callback when job completes

        Returns:
            Job ID
        """
        # Create job
        job_id = generate_id()
        job = Job(
            job_id=job_id,
            job_type=job_type,
            priority=priority,
            payload=payload,
            max_retries=max_retries,
            created_at=datetime.utcnow()
        )

        # Store job
        self.jobs[job_id] = job

        if callback:
            self.job_callbacks[job_id] = callback

        # Enqueue to appropriate queue
        queue = self._get_queue(job_type)

        # Use priority and counter for ordering (counter prevents comparison of Job objects)
        self._counter += 1
        await queue.put((priority, self._counter, job))

        self.stats["total_jobs"] += 1

        logger.info(f"Enqueued job {job_id} (type={job_type.value}, priority={priority})")

        return job_id

    async def dequeue_job(self, job_type: JobType, timeout: Optional[float] = None) -> Optional[Job]:
        """
        Dequeue a job from specified queue.

        Args:
            job_type: Type of job to dequeue
            timeout: Optional timeout in seconds

        Returns:
            Job or None if timeout
        """
        queue = self._get_queue(job_type)

        try:
            if timeout:
                priority, counter, job = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                priority, counter, job = await queue.get()

            # Mark as running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()

            logger.debug(f"Dequeued job {job.job_id} (type={job_type.value})")

            return job

        except asyncio.TimeoutError:
            return None

    async def mark_job_completed(self, job_id: str, result: Optional[Dict] = None) -> None:
        """
        Mark job as completed.

        Args:
            job_id: Job ID
            result: Optional result data
        """
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found")
            return

        job = self.jobs[job_id]
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

        self.stats["completed_jobs"] += 1

        logger.info(f"Job {job_id} completed")

        # Execute callback
        if job_id in self.job_callbacks:
            try:
                callback = self.job_callbacks[job_id]
                await callback(job, result)
            except Exception as e:
                logger.error(f"Job callback failed for {job_id}: {e}")

    async def mark_job_failed(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed and potentially retry.

        Args:
            job_id: Job ID
            error: Error message

        Returns:
            True if job will be retried, False otherwise
        """
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found")
            return False

        job = self.jobs[job_id]
        job.error_message = error
        job.retry_count += 1

        # Check if should retry
        if job.retry_count < job.max_retries:
            logger.warning(f"Job {job_id} failed (attempt {job.retry_count}/{job.max_retries}), retrying...")

            # Reset status and re-enqueue
            job.status = JobStatus.PENDING
            job.started_at = None

            # Re-enqueue with exponential backoff
            await asyncio.sleep(min(2 ** job.retry_count, 60))

            queue = self._get_queue(job.job_type)
            await queue.put((job.priority, job))

            return True
        else:
            logger.error(f"Job {job_id} failed permanently after {job.retry_count} attempts: {error}")

            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()

            self.stats["failed_jobs"] += 1

            return False

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False if not found or already running
        """
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]

        if job.status in [JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED]:
            logger.warning(f"Cannot cancel job {job_id} in status {job.status.value}")
            return False

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        self.stats["cancelled_jobs"] += 1

        logger.info(f"Job {job_id} cancelled")

        return True

    def get_job_status(self, job_id: str) -> Optional[Job]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            Job or None
        """
        return self.jobs.get(job_id)

    def get_queue_sizes(self) -> Dict[str, int]:
        """
        Get queue sizes.

        Returns:
            Dictionary of queue sizes
        """
        return {
            "orchestration_queue": self.orchestration_queue.qsize(),
            "page_scan_queue": self.page_scan_queue.qsize(),
        }

    def get_stats(self) -> Dict:
        """
        Get queue statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "pending_jobs": sum(1 for j in self.jobs.values() if j.status == JobStatus.PENDING),
            "running_jobs": sum(1 for j in self.jobs.values() if j.status == JobStatus.RUNNING),
            **self.get_queue_sizes(),
        }

    async def clear_completed_jobs(self, max_age_seconds: int = 3600) -> int:
        """
        Clear old completed jobs from memory.

        Args:
            max_age_seconds: Maximum age of completed jobs to keep

        Returns:
            Number of jobs cleared
        """
        now = datetime.utcnow()
        cleared = 0

        job_ids_to_remove = []

        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at:
                    age = (now - job.completed_at).total_seconds()
                    if age > max_age_seconds:
                        job_ids_to_remove.append(job_id)

        for job_id in job_ids_to_remove:
            del self.jobs[job_id]
            if job_id in self.job_callbacks:
                del self.job_callbacks[job_id]
            cleared += 1

        if cleared > 0:
            logger.info(f"Cleared {cleared} old completed jobs")

        return cleared

    def _get_queue(self, job_type: JobType) -> asyncio.Queue:
        """
        Get queue for job type.

        Args:
            job_type: Job type

        Returns:
            Queue instance
        """
        if job_type == JobType.SCAN_ORCHESTRATION:
            return self.orchestration_queue
        elif job_type == JobType.PAGE_SCAN:
            return self.page_scan_queue
        else:
            raise ValueError(f"Unknown job type: {job_type}")


# Global queue manager instance
_queue_manager: Optional[QueueManager] = None


def get_queue_manager(max_queue_size: int = 1000) -> QueueManager:
    """
    Get global queue manager instance.

    Args:
        max_queue_size: Maximum queue size

    Returns:
        QueueManager instance
    """
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager(max_queue_size=max_queue_size)
    return _queue_manager
