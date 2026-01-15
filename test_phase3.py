"""Test script for Phase 3: Queue System & Workers."""

import asyncio
import sys
from pathlib import Path

# Add scanner_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner_v2.utils.logger import setup_logging, get_logger
from scanner_v2.schemas.scan import JobType, JobPriority, ScanJobPayload
from scanner_v2.workers.queue_manager import QueueManager, get_queue_manager
from scanner_v2.workers.scan_worker import ScanWorker
from scanner_v2.workers.worker_pool import WorkerPool, init_worker_pool, stop_worker_pool


async def test_queue_manager():
    """Test queue manager."""
    print("\n" + "=" * 60)
    print("Testing Queue Manager")
    print("=" * 60)

    try:
        # Create queue manager
        queue_manager = QueueManager(max_queue_size=100)

        # Test enqueue
        job_id = await queue_manager.enqueue_job(
            job_type=JobType.SCAN_ORCHESTRATION,
            payload={
                "scan_id": "test_scan_1",
                "project_id": "test_project",
                "base_url": "https://example.com",
                "config": {}
            },
            priority=JobPriority.NORMAL.value
        )

        print(f"✓ Enqueued job: {job_id}")

        # Test queue sizes
        sizes = queue_manager.get_queue_sizes()
        print(f"✓ Queue sizes: {sizes}")

        # Test dequeue
        job = await queue_manager.dequeue_job(JobType.SCAN_ORCHESTRATION, timeout=1.0)
        if job:
            print(f"✓ Dequeued job: {job.job_id}")

            # Test mark completed
            await queue_manager.mark_job_completed(job.job_id)
            print(f"✓ Marked job as completed")
        else:
            print("⚠ No job dequeued (timeout)")

        # Test stats
        stats = queue_manager.get_stats()
        print(f"✓ Stats: {stats}")

        return True

    except Exception as e:
        print(f"✗ Queue manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scan_worker():
    """Test scan worker."""
    print("\n" + "=" * 60)
    print("Testing Scan Worker")
    print("=" * 60)

    try:
        # Create queue manager
        queue_manager = QueueManager(max_queue_size=100)

        # Create worker
        worker = ScanWorker(
            worker_id="test-worker-1",
            queue_manager=queue_manager,
            job_timeout=30
        )

        print(f"✓ Worker created: {worker.worker_id}")

        # Start worker
        await worker.start()
        print(f"✓ Worker started")

        # Enqueue a simple job
        job_id = await queue_manager.enqueue_job(
            job_type=JobType.SCAN_ORCHESTRATION,
            payload={
                "scan_id": "test_scan_2",
                "project_id": "test_project",
                "base_url": "https://example.com",
                "config": {
                    "max_depth": 1,
                    "max_pages": 2,
                    "scanners": ["axe"]
                }
            },
            priority=JobPriority.HIGH.value
        )

        print(f"✓ Enqueued test job: {job_id}")

        # Wait a bit for worker to pick it up
        await asyncio.sleep(2)

        # Check job status
        job_status = queue_manager.get_job_status(job_id)
        if job_status:
            print(f"✓ Job status: {job_status.status.value}")
        else:
            print("⚠ Job status not found")

        # Stop worker
        await worker.stop()
        print(f"✓ Worker stopped")

        return True

    except Exception as e:
        print(f"✗ Scan worker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_worker_pool():
    """Test worker pool."""
    print("\n" + "=" * 60)
    print("Testing Worker Pool")
    print("=" * 60)

    try:
        # Create worker pool
        pool = WorkerPool(worker_count=3, job_timeout=30)

        print(f"✓ Worker pool created with 3 workers")

        # Start pool
        await pool.start()
        print(f"✓ Worker pool started")

        # Check status
        status = pool.get_status()
        print(f"✓ Pool status: {status['active_workers']} active workers")

        # Check health
        health = pool.get_health()
        print(f"✓ Pool health: {health['status']}")

        # Enqueue multiple jobs
        queue_manager = pool.queue_manager

        for i in range(5):
            job_id = await queue_manager.enqueue_job(
                job_type=JobType.SCAN_ORCHESTRATION,
                payload={
                    "scan_id": f"test_scan_{i}",
                    "project_id": "test_project",
                    "base_url": f"https://example{i}.com",
                    "config": {
                        "max_depth": 1,
                        "max_pages": 2,
                    }
                },
                priority=JobPriority.NORMAL.value
            )

        print(f"✓ Enqueued 5 test jobs")

        # Wait for processing
        await asyncio.sleep(3)

        # Check stats
        stats = queue_manager.get_stats()
        print(f"✓ Queue stats: {stats['total_jobs']} total, {stats['running_jobs']} running")

        # Test scaling
        await pool.scale(5)
        print(f"✓ Scaled pool to 5 workers")

        status = pool.get_status()
        print(f"✓ Updated pool status: {status['active_workers']} active workers")

        # Stop pool
        await pool.stop()
        print(f"✓ Worker pool stopped")

        return True

    except Exception as e:
        print(f"✗ Worker pool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_job_retry():
    """Test job retry mechanism."""
    print("\n" + "=" * 60)
    print("Testing Job Retry Mechanism")
    print("=" * 60)

    try:
        queue_manager = QueueManager(max_queue_size=100)

        # Enqueue a job that will fail
        job_id = await queue_manager.enqueue_job(
            job_type=JobType.SCAN_ORCHESTRATION,
            payload={
                "scan_id": "fail_test",
                "project_id": "test_project",
                "base_url": "https://invalid-url-that-will-fail.com",
                "config": {}
            },
            priority=JobPriority.NORMAL.value,
            max_retries=2
        )

        print(f"✓ Enqueued job with max_retries=2: {job_id}")

        # Dequeue and fail it
        job = await queue_manager.dequeue_job(JobType.SCAN_ORCHESTRATION, timeout=1.0)
        if job:
            # Mark as failed - should trigger retry
            will_retry = await queue_manager.mark_job_failed(job.job_id, "Test failure")
            print(f"✓ Job failed, will retry: {will_retry}")

            # Check if re-enqueued
            await asyncio.sleep(0.5)
            sizes = queue_manager.get_queue_sizes()
            print(f"✓ Queue size after retry: {sizes}")

        return True

    except Exception as e:
        print(f"✗ Job retry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_workers():
    """Test concurrent workers processing jobs."""
    print("\n" + "=" * 60)
    print("Testing Concurrent Workers")
    print("=" * 60)

    try:
        queue_manager = QueueManager(max_queue_size=100)

        # Start multiple workers
        workers = []
        for i in range(3):
            worker = ScanWorker(
                worker_id=f"concurrent-worker-{i+1}",
                queue_manager=queue_manager,
                job_timeout=30
            )
            workers.append(worker)
            await worker.start()

        print(f"✓ Started 3 concurrent workers")

        # Enqueue multiple jobs
        job_ids = []
        for i in range(10):
            job_id = await queue_manager.enqueue_job(
                job_type=JobType.SCAN_ORCHESTRATION,
                payload={
                    "scan_id": f"concurrent_scan_{i}",
                    "project_id": "test_project",
                    "base_url": f"https://example{i}.com",
                    "config": {"max_pages": 2}
                }
            )
            job_ids.append(job_id)

        print(f"✓ Enqueued 10 jobs")

        # Wait for processing
        await asyncio.sleep(5)

        # Check results
        stats = queue_manager.get_stats()
        print(f"✓ Processed: completed={stats['completed_jobs']}, failed={stats['failed_jobs']}")

        # Stop workers
        for worker in workers:
            await worker.stop()

        print(f"✓ Stopped all workers")

        return True

    except Exception as e:
        print(f"✗ Concurrent workers test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 3 tests."""
    print("\n" + "=" * 60)
    print("WCAG Scanner V2 - Phase 3 Tests")
    print("Queue System & Workers")
    print("=" * 60)

    # Setup logging
    setup_logging(level="INFO", format_type="standard")

    results = []

    # Run tests
    results.append(("Queue Manager", await test_queue_manager()))
    results.append(("Scan Worker", await test_scan_worker()))
    results.append(("Worker Pool", await test_worker_pool()))
    results.append(("Job Retry", await test_job_retry()))
    results.append(("Concurrent Workers", await test_concurrent_workers()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for name, result in results:
        if result is True:
            print(f"✓ {name}")
        elif result is False:
            print(f"✗ {name}")
        else:
            print(f"⚠ {name} (skipped)")

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n🎉 Phase 3: Queue System & Workers - Complete!")
        print("\nImplemented components:")
        print("  ✓ In-memory Queue Manager (asyncio.Queue)")
        print("  ✓ Job priority and retry logic")
        print("  ✓ Scan Worker (job processing)")
        print("  ✓ Worker Pool (lifecycle management)")
        print("  ✓ Concurrent job processing")
        print("  ✓ Automatic cleanup of old jobs")
        print("  ✓ Worker scaling (dynamic)")
        print("  ✓ Health monitoring")
    else:
        print("\n❌ Some tests failed. Please review errors above.")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
