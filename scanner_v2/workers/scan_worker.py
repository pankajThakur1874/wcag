"""Scan worker that processes jobs from the queue."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import generate_id, utc_now
from scanner_v2.schemas.scan import Job, JobType, JobStatus, ScanJobPayload, PageScanJobPayload
from scanner_v2.workers.queue_manager import QueueManager
from scanner_v2.core.scanner_orchestrator import scan_orchestrator
from scanner_v2.database.models import ScanStatus

logger = get_logger("scan_worker")


class ScanWorker:
    """Worker that processes scan jobs."""

    def __init__(
        self,
        worker_id: str,
        queue_manager: QueueManager,
        job_timeout: int = 300
    ):
        """
        Initialize scan worker.

        Args:
            worker_id: Worker ID
            queue_manager: Queue manager instance
            job_timeout: Job timeout in seconds
        """
        self.worker_id = worker_id
        self.queue_manager = queue_manager
        self.job_timeout = job_timeout
        self.is_running = False
        self.current_job: Optional[Job] = None
        self.task: Optional[asyncio.Task] = None

        logger.info(f"Worker {worker_id} initialized")

    async def start(self) -> None:
        """Start the worker."""
        if self.is_running:
            logger.warning(f"Worker {self.worker_id} already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run())

        logger.info(f"Worker {self.worker_id} started")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        if not self.is_running:
            return

        self.is_running = False

        # Wait for current job to complete
        if self.task:
            try:
                await asyncio.wait_for(self.task, timeout=60)
            except asyncio.TimeoutError:
                logger.warning(f"Worker {self.worker_id} stop timed out, cancelling")
                self.task.cancel()

        logger.info(f"Worker {self.worker_id} stopped")

    async def _run(self) -> None:
        """Main worker loop."""
        logger.info(f"Worker {self.worker_id} running")

        while self.is_running:
            try:
                # Try to get orchestration job first (higher priority)
                job = await self.queue_manager.dequeue_job(
                    JobType.SCAN_ORCHESTRATION,
                    timeout=1.0
                )

                if not job:
                    # Try page scan job
                    job = await self.queue_manager.dequeue_job(
                        JobType.PAGE_SCAN,
                        timeout=1.0
                    )

                if job:
                    self.current_job = job
                    await self._process_job(job)
                    self.current_job = None

            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {self.worker_id} exited")

    async def _process_job(self, job: Job) -> None:
        """
        Process a job.

        Args:
            job: Job to process
        """
        logger.info(f"Worker {self.worker_id} processing job {job.job_id} (type={job.job_type.value})")

        job.worker_id = self.worker_id

        try:
            # Execute job with timeout
            result = await asyncio.wait_for(
                self._execute_job(job),
                timeout=self.job_timeout
            )

            # Mark as completed
            await self.queue_manager.mark_job_completed(job.job_id, result)

        except asyncio.TimeoutError:
            error = f"Job timed out after {self.job_timeout}s"
            logger.error(f"Worker {self.worker_id}: {error}")
            await self.queue_manager.mark_job_failed(job.job_id, error)

        except Exception as e:
            error = f"Job failed: {e}"
            logger.error(f"Worker {self.worker_id}: {error}")
            await self.queue_manager.mark_job_failed(job.job_id, error)

    async def _execute_job(self, job: Job) -> Dict[str, Any]:
        """
        Execute job based on type.

        Args:
            job: Job to execute

        Returns:
            Job result
        """
        if job.job_type == JobType.SCAN_ORCHESTRATION:
            return await self._execute_scan_orchestration(job)
        elif job.job_type == JobType.PAGE_SCAN:
            return await self._execute_page_scan(job)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

    async def _execute_scan_orchestration(self, job: Job) -> Dict[str, Any]:
        """
        Execute scan orchestration job.

        Args:
            job: Job

        Returns:
            Scan results
        """
        payload = ScanJobPayload(**job.payload)

        logger.info(f"Executing scan orchestration for {payload.base_url}")

        # Progress callback to track status
        def progress_callback(status: str, data: Dict):
            logger.info(f"Scan {payload.scan_id} progress: {status} - {data.get('message')}")

        # Execute scan
        results = await scan_orchestrator.execute_scan(
            base_url=payload.base_url,
            scan_id=payload.scan_id,
            config=payload.config,
            progress_callback=progress_callback
        )

        logger.info(f"Scan orchestration complete: {payload.scan_id}")

        return results

    async def _execute_page_scan(self, job: Job) -> Dict[str, Any]:
        """
        Execute page scan job.

        Args:
            job: Job

        Returns:
            Page scan results
        """
        payload = PageScanJobPayload(**job.payload)

        logger.info(f"Executing page scan for {payload.page_url}")

        # Note: This would use PageScanner directly if we wanted individual page scanning
        # For now, page scanning is handled by the orchestrator

        return {
            "page_url": payload.page_url,
            "status": "completed"
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get worker status.

        Returns:
            Status dictionary
        """
        return {
            "worker_id": self.worker_id,
            "is_running": self.is_running,
            "current_job": self.current_job.job_id if self.current_job else None,
        }
