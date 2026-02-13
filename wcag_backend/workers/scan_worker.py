"""Scan worker for processing scan jobs."""

import asyncio
from datetime import datetime
from typing import Optional

from wcag_backend.workers.queue_manager import QueueManager, JobType, Job
from wcag_backend.core.scanner_adapter import ScannerAdapter
from wcag_backend.database.connection import get_db
from wcag_backend.database.repositories.scan_repo import ScanRepository
from wcag_backend.database.repositories.issue_repo import IssueRepository
from wcag_backend.database.models import Issue, ImpactLevel, WCAGLevel, IssueStatus
from wcag_backend.utils.logger import get_logger

logger = get_logger("scan_worker")


class ScanWorker:
    """Worker that processes scan jobs from the queue."""

    def __init__(self, worker_id: str, queue_manager: QueueManager):
        """
        Initialize scan worker.

        Args:
            worker_id: Unique worker identifier
            queue_manager: Queue manager instance
        """
        self.worker_id = worker_id
        self.queue_manager = queue_manager
        self.scanner_adapter = ScannerAdapter()
        self.running = False

    async def run(self) -> None:
        """
        Main worker loop - processes jobs from queue.

        Runs continuously until cancelled.
        """
        logger.info(f"Worker {self.worker_id} started")
        self.running = True

        try:
            while self.running:
                # Get next job from queue (blocks until job available)
                job = await self.queue_manager.dequeue_job()

                if job:
                    await self._process_job(job)

        except asyncio.CancelledError:
            logger.info(f"Worker {self.worker_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Worker {self.worker_id} error: {e}")
        finally:
            self.running = False
            logger.info(f"Worker {self.worker_id} stopped")

    async def _process_job(self, job: Job) -> None:
        """
        Process a single job.

        Args:
            job: Job to process
        """
        logger.info(f"Worker {self.worker_id} processing job {job.job_id}")

        try:
            if job.job_type == JobType.SCAN:
                await self._process_scan_job(job)
            elif job.job_type == JobType.SITE_SCAN:
                await self._process_site_scan_job(job)
            else:
                logger.error(f"Unknown job type: {job.job_type}")
                await self.queue_manager.mark_completed(job.job_id, error="Unknown job type")
                return

            # Mark job as completed
            await self.queue_manager.mark_completed(job.job_id)

        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            await self.queue_manager.mark_completed(job.job_id, error=str(e))

    async def _process_scan_job(self, job: Job) -> None:
        """
        Process a single-page scan job.

        Args:
            job: Scan job
        """
        # Extract job payload
        scan_id = job.payload.get("scan_id")
        url = job.payload.get("url")
        scanners = job.payload.get("scanners", ["axe"])

        logger.info(f"Processing scan job for {url}", extra={"scan_id": scan_id})

        # Get database connection
        db = get_db()
        scan_repo = ScanRepository(db)
        issue_repo = IssueRepository(db)

        # Update scan status to 'scanning'
        await scan_repo.update_status(scan_id, "scanning")

        # Progress callback
        async def on_progress(phase: str, current: int, total: int, message: str):
            await scan_repo.update_progress(scan_id, {
                "pages_scanned": current,
                "total_pages": total,
                "current_url": message,
                "percentage": int((current / total) * 100) if total > 0 else 0
            })

        # Execute scan
        result = await self.scanner_adapter.scan_single_page(
            url=url,
            scanners=scanners,
            progress_callback=on_progress
        )

        # Save issues to database
        issues_data = []
        impact_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}

        # Get scan to get user_id
        scan = await scan_repo.get_by_id(scan_id)

        for violation in result["violations"]:
            # Count by impact
            impact = violation.get("impact", "moderate")
            impact_counts[impact] = impact_counts.get(impact, 0) + 1

            issues_data.append({
                "scan_id": scan_id,
                "user_id": scan.get("user_id"),
                "page_url": url,
                "description": violation.get("description"),
                "impact": violation.get("impact"),
                "wcag_criteria": violation.get("wcag_criteria"),
                "wcag_level": violation.get("wcag_level"),
                "selector": violation.get("selector"),
                "html_snippet": violation.get("html_snippet"),
                "how_to_fix": violation.get("how_to_fix"),
                "help_url": violation.get("help_url"),
                "status": "open"
            })

        # Bulk insert issues
        if issues_data:
            await issue_repo.create_many(issues_data)

        # Update scan with results
        await scan_repo.update_results(scan_id, {
            "status": "completed",
            "score": result.get("score", 0),
            "issues_count": len(issues_data),
            "issues_by_impact": impact_counts,
            "duration": result.get("duration"),
            "completed_at": datetime.utcnow()
        })

        logger.info(f"Scan completed: {scan_id}, score: {result.get('score')}, issues: {len(issues_data)}")

    async def _process_site_scan_job(self, job: Job) -> None:
        """
        Process a site-wide scan job.

        Args:
            job: Site scan job
        """
        # Extract job payload
        scan_id = job.payload.get("scan_id")
        url = job.payload.get("url")
        max_pages = job.payload.get("max_pages", 10)
        max_depth = job.payload.get("max_depth", 3)
        scanners = job.payload.get("scanners", ["axe"])

        logger.info(f"Processing site scan job for {url}", extra={"scan_id": scan_id})

        # Get database connection
        db = get_db()
        scan_repo = ScanRepository(db)
        issue_repo = IssueRepository(db)

        # Update scan status to 'scanning'
        await scan_repo.update_status(scan_id, "scanning")

        # Progress callback
        async def on_progress(phase: str, current: int, total: int, message: str):
            await scan_repo.update_progress(scan_id, {
                "pages_scanned": current,
                "total_pages": total,
                "current_url": message,
                "percentage": int((current / total) * 100) if total > 0 else 0
            })

        # Execute site scan
        result = await self.scanner_adapter.scan_site(
            url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            scanners=scanners,
            progress_callback=on_progress
        )

        # Save issues (similar to single scan)
        issues_data = []
        impact_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}

        scan = await scan_repo.get_by_id(scan_id)

        for violation in result["violations"]:
            impact = violation.get("impact", "moderate")
            impact_counts[impact] = impact_counts.get(impact, 0) + 1

            issues_data.append({
                "scan_id": scan_id,
                "user_id": scan.get("user_id"),
                "page_url": url,  # Could be enhanced to track which page
                "description": violation.get("description"),
                "impact": violation.get("impact"),
                "wcag_criteria": violation.get("wcag_criteria"),
                "wcag_level": violation.get("wcag_level"),
                "selector": violation.get("selector"),
                "html_snippet": violation.get("html_snippet"),
                "how_to_fix": violation.get("how_to_fix"),
                "help_url": violation.get("help_url"),
                "status": "open"
            })

        # Bulk insert issues
        if issues_data:
            await issue_repo.create_many(issues_data)

        # Update scan with results
        await scan_repo.update_results(scan_id, {
            "status": "completed",
            "score": result.get("score", 0),
            "issues_count": len(issues_data),
            "issues_by_impact": impact_counts,
            "duration": result.get("duration"),
            "completed_at": datetime.utcnow()
        })

        logger.info(f"Site scan completed: {scan_id}, pages: {result.get('pages_scanned')}, issues: {len(issues_data)}")
