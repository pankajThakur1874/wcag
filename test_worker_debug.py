#!/usr/bin/env python3
"""Debug script to test if workers are running and processing jobs."""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner_v2.utils.config import load_config
from scanner_v2.database.connection import MongoDB
from scanner_v2.workers.queue_manager import QueueManager
from scanner_v2.workers.worker_pool import WorkerPool
from scanner_v2.schemas.scan import JobType, JobPriority
from scanner_v2.api.dependencies import set_db_instance, set_queue_manager_instance


async def main():
    """Test worker setup and job processing."""
    print("=" * 60)
    print("WORKER DEBUG TEST")
    print("=" * 60)

    # Load config
    config = load_config()
    print(f"\n✓ Config loaded")
    print(f"  - Workers: {config.queue.worker_count}")
    print(f"  - Queue size: {config.queue.max_queue_size}")
    print(f"  - Job timeout: {config.queue.job_timeout}s")

    # Connect to MongoDB
    db = MongoDB(config)
    await db.connect()
    set_db_instance(db)
    print(f"\n✓ MongoDB connected")

    # Initialize queue manager
    queue_manager = QueueManager(max_queue_size=config.queue.max_queue_size)
    set_queue_manager_instance(queue_manager)
    print(f"\n✓ Queue manager initialized")

    # Get queue stats before workers
    stats = queue_manager.get_stats()
    print(f"\n📊 Queue stats (before workers):")
    print(f"  - Jobs queued: {stats}")

    # Initialize worker pool
    worker_pool = WorkerPool(
        queue_manager=queue_manager,
        worker_count=config.queue.worker_count,
        job_timeout=config.queue.job_timeout
    )

    print(f"\n🚀 Starting worker pool...")
    await worker_pool.start()

    # Get worker pool status
    status = worker_pool.get_status()
    print(f"\n✓ Worker pool started")
    print(f"  - Total workers: {status['worker_count']}")
    print(f"  - Active workers: {status['active_workers']}")
    print(f"  - Idle workers: {status['idle_workers']}")

    # Check if workers are actually running
    print(f"\n👷 Worker details:")
    for worker_status in status['workers']:
        print(f"  - {worker_status['worker_id']}: running={worker_status['is_running']}, job={worker_status['current_job']}")

    # Wait a moment for workers to fully start
    await asyncio.sleep(2)

    # Try to enqueue a simple test job
    print(f"\n📝 Enqueuing test job...")

    test_job_id = await queue_manager.enqueue_job(
        job_type=JobType.SCAN_ORCHESTRATION,
        payload={
            "scan_id": "test-scan-123",
            "project_id": "test-project",
            "base_url": "https://example.com",
            "config": {
                "scanners": ["axe"],
                "max_depth": 1,
                "max_pages": 1,
                "wcag_level": "AA",
                "screenshot_enabled": False
            }
        },
        priority=JobPriority.NORMAL.value
    )

    print(f"✓ Job enqueued: {test_job_id}")

    # Wait and check if job is picked up
    print(f"\n⏳ Waiting for workers to pick up job...")
    for i in range(10):
        await asyncio.sleep(1)

        # Check worker status
        status = worker_pool.get_status()
        busy = status['busy_workers']

        print(f"  [{i+1}s] Busy workers: {busy}")

        if busy > 0:
            print(f"\n✓ Job picked up by worker!")
            break
    else:
        print(f"\n❌ Job NOT picked up after 10 seconds")
        print(f"\n📊 Final queue stats:")
        print(queue_manager.get_stats())

        print(f"\n👷 Final worker status:")
        status = worker_pool.get_status()
        for worker_status in status['workers']:
            print(f"  - {worker_status['worker_id']}: running={worker_status['is_running']}, job={worker_status['current_job']}")

    # Cleanup
    print(f"\n🛑 Stopping worker pool...")
    await worker_pool.stop()

    print(f"\n🛑 Disconnecting MongoDB...")
    await db.disconnect()

    print(f"\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
