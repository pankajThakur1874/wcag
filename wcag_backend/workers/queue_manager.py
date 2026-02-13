"""In-memory job queue manager for background tasks."""

import asyncio
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from wcag_backend.utils.logger import get_logger
from wcag_backend.utils.exceptions import QueueFullError

logger = get_logger("queue_manager")


class JobType(str, Enum):
    """Job type enumeration."""

    SCAN = "scan"
    SITE_SCAN = "site_scan"


class JobPriority(int, Enum):
    """Job priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2


class JobStatus(str, Enum):
    """Job status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Represents a background job."""

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: JobType = JobType.SCAN
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class QueueManager:
    """Manages job queue for background workers."""

    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize queue manager.

        Args:
            max_queue_size: Maximum number of jobs in queue
        """
        self.max_queue_size = max_queue_size
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.jobs: Dict[str, Job] = {}  # Track all jobs by ID
        self._lock = asyncio.Lock()

    async def enqueue_job(
        self,
        job_type: JobType,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL
    ) -> str:
        """
        Add a job to the queue.

        Args:
            job_type: Type of job
            payload: Job data
            priority: Job priority

        Returns:
            Job ID

        Raises:
            QueueFullError: If queue is full
        """
        if self.queue.full():
            raise QueueFullError("Job queue is at capacity")

        job = Job(
            job_type=job_type,
            payload=payload,
            priority=priority
        )

        async with self._lock:
            self.jobs[job.job_id] = job

        # Priority queue uses negative priority for higher priority items
        await self.queue.put((-priority.value, job))

        logger.info(f"Job {job.job_id} enqueued: {job_type.value}", extra={"job_id": job.job_id})

        return job.job_id

    async def dequeue_job(self) -> Optional[Job]:
        """
        Get next job from queue (blocks until job available).

        Returns:
            Next job or None
        """
        try:
            # Wait for a job (blocks)
            priority, job = await self.queue.get()

            async with self._lock:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()

            logger.info(f"Job {job.job_id} dequeued", extra={"job_id": job.job_id})

            return job

        except Exception as e:
            logger.error(f"Error dequeuing job: {e}")
            return None

    async def mark_completed(self, job_id: str, error: Optional[str] = None) -> None:
        """
        Mark a job as completed or failed.

        Args:
            job_id: Job ID
            error: Error message if job failed
        """
        async with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.completed_at = datetime.utcnow()

                if error:
                    job.status = JobStatus.FAILED
                    job.error = error
                    logger.error(f"Job {job_id} failed: {error}", extra={"job_id": job_id})
                else:
                    job.status = JobStatus.COMPLETED
                    logger.info(f"Job {job_id} completed", extra={"job_id": job_id})

    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """
        Get job status by ID.

        Args:
            job_id: Job ID

        Returns:
            Job object or None
        """
        async with self._lock:
            return self.jobs.get(job_id)

    async def get_queue_size(self) -> int:
        """
        Get current queue size.

        Returns:
            Number of jobs in queue
        """
        return self.queue.qsize()

    async def cleanup_old_jobs(self, max_age_seconds: int = 86400) -> int:
        """
        Remove completed/failed jobs older than max_age.

        Args:
            max_age_seconds: Maximum age in seconds (default: 24 hours)

        Returns:
            Number of jobs removed
        """
        cutoff = datetime.utcnow().timestamp() - max_age_seconds
        removed_count = 0

        async with self._lock:
            jobs_to_remove = []

            for job_id, job in self.jobs.items():
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    if job.completed_at and job.completed_at.timestamp() < cutoff:
                        jobs_to_remove.append(job_id)

            for job_id in jobs_to_remove:
                del self.jobs[job_id]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old jobs")

        return removed_count


# Global queue manager instance
_queue_manager: Optional[QueueManager] = None


def get_queue_manager() -> QueueManager:
    """Get global queue manager instance."""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager()
    return _queue_manager


def set_queue_manager(queue_manager: QueueManager) -> None:
    """Set global queue manager instance."""
    global _queue_manager
    _queue_manager = queue_manager
