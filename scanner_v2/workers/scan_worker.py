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
        logger.info(f"Worker {self.worker_id} processing job {job.job_id} (type={job.job_type})")

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
        from scanner_v2.database.models import (
            ScanProgress, ScannedPage, Issue, WCAGLevel,
            Principle, ImpactLevel, IssueStatus, IssueInstance
        )
        from scanner_v2.api.dependencies import get_db_instance
        from scanner_v2.database.repositories.scan_repo import ScanRepository
        from scanner_v2.database.repositories.page_repo import PageRepository
        from scanner_v2.database.repositories.issue_repo import IssueRepository

        payload = ScanJobPayload(**job.payload)

        logger.info(f"Executing scan orchestration for {payload.base_url}")

        # Get database access for progress updates
        mongodb_instance = get_db_instance()
        db = mongodb_instance.db  # Get the actual AsyncIOMotorDatabase
        scan_repo = ScanRepository(db)
        page_repo = PageRepository(db)
        issue_repo = IssueRepository(db)

        # Progress callback to track status AND update database
        async def progress_callback(status: str, data: Dict):
            logger.info(f"Scan {payload.scan_id} progress: {status} - {data.get('message')}")

            # Update database with progress
            try:
                # Update status if it changed
                if status in [s.value for s in ScanStatus]:
                    await scan_repo.update_status(payload.scan_id, ScanStatus(status))

                # Parse started_at if provided
                started_at = None
                if data.get('started_at'):
                    from datetime import datetime
                    started_at = datetime.fromisoformat(data['started_at'])

                # Update progress details
                progress = ScanProgress(
                    total_pages=data.get('pages_discovered', data.get('pages_total', 0)),
                    pages_crawled=data.get('pages_discovered', 0),
                    pages_scanned=data.get('pages_scanned', 0),
                    current_page=data.get('current_url'),
                    percentage_complete=data.get('percentage_complete', 0.0),
                    estimated_time_remaining_seconds=data.get('estimated_time_remaining_seconds'),
                    started_at=started_at
                )
                await scan_repo.update_progress(payload.scan_id, progress)
            except Exception as e:
                logger.warning(f"Failed to update scan progress in database: {e}")

        # Execute scan
        results = await scan_orchestrator.execute_scan(
            base_url=payload.base_url,
            scan_id=payload.scan_id,
            config=payload.config,
            progress_callback=progress_callback
        )

        logger.info(f"Scan orchestration complete: {payload.scan_id}")

        # Save pages to database
        try:
            logger.info(f"Saving {len(results.get('pages', []))} pages to database...")

            pages_to_save = []
            temp_id_to_page_data = {}  # Map temp page_id to page data for later lookup

            for page_data in results.get("pages", []):
                # Convert page dict to ScannedPage model
                scanned_page = ScannedPage(
                    scan_id=payload.scan_id,
                    url=page_data.get("url", ""),
                    title=page_data.get("title"),
                    status_code=page_data.get("status_code"),
                    load_time_ms=page_data.get("load_time_ms"),
                    screenshot_path=page_data.get("screenshot_path"),
                    issues_count=len(page_data.get("issues", [])),
                    compliance_score=page_data.get("compliance_score", 0.0),
                    error_message=page_data.get("error")  # Capture error if page scan failed
                )
                pages_to_save.append(scanned_page)

                # Store mapping from temp page_id to page data
                temp_page_id = page_data.get("page_id", "")
                temp_id_to_page_data[temp_page_id] = {
                    "url": page_data.get("url", ""),
                    "page_obj": scanned_page
                }

            # Save pages in bulk
            if pages_to_save:
                page_ids = await page_repo.create_many(pages_to_save)
                logger.info(f"✓ Saved {len(page_ids)} pages to database")

                # Update mapping with actual database IDs
                for i, page_obj in enumerate(pages_to_save):
                    page_obj.id = page_ids[i]

                # Create URL to page_id mapping for issues
                url_to_page_id = {}
                for temp_page_id, data in temp_id_to_page_data.items():
                    url = data["url"]
                    page_obj = data["page_obj"]
                    url_to_page_id[url] = page_obj.id

        except Exception as e:
            logger.error(f"Failed to save pages to database: {e}")
            url_to_page_id = {}

        # Save issues to database
        try:
            logger.info(f"Saving {len(results.get('all_issues', []))} issues to database...")

            issues_to_save = []

            for issue_data in results.get("all_issues", []):
                # Get actual page_id from URL
                page_url = issue_data.get("page_url", "")
                page_id = url_to_page_id.get(page_url, "")

                if not page_id:
                    logger.warning(f"Could not find page_id for URL: {page_url}, skipping issue")
                    continue

                # Convert instances
                instances = []
                for inst_data in issue_data.get("instances", []):
                    instance = IssueInstance(
                        selector=inst_data.get("selector", ""),
                        html=inst_data.get("html"),
                        screenshot_path=inst_data.get("screenshot_path"),
                        context=inst_data.get("context"),
                        failure_summary=inst_data.get("failure_summary"),
                        data=inst_data.get("data")
                    )
                    instances.append(instance)

                # Convert issue dict to Issue model
                try:
                    issue = Issue(
                        scan_id=payload.scan_id,
                        page_id=page_id,
                        wcag_criteria=issue_data.get("wcag_criteria", []),
                        wcag_level=WCAGLevel(issue_data.get("wcag_level", "AA")),
                        principle=Principle(issue_data.get("principle", "perceivable")),
                        impact=ImpactLevel(issue_data.get("impact", "moderate")),
                        rule_id=issue_data.get("rule_id", ""),
                        description=issue_data.get("description", ""),
                        help_text=issue_data.get("help_text"),
                        help_url=issue_data.get("help_url"),
                        detected_by=issue_data.get("detected_by", []),
                        instances=instances,
                        status=IssueStatus.OPEN,
                        manual_review_required=issue_data.get("manual_review_required", False),
                        fix_suggestion=issue_data.get("fix_suggestion")
                    )
                    issues_to_save.append(issue)
                except Exception as e:
                    logger.warning(f"Failed to convert issue: {e}")
                    continue

            # Save issues in bulk
            if issues_to_save:
                issue_ids = await issue_repo.create_many(issues_to_save)
                logger.info(f"✓ Saved {len(issue_ids)} issues to database")
        except Exception as e:
            logger.error(f"Failed to save issues to database: {e}")

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
