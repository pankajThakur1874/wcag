"""Check scan status in database."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import init_db, get_db, close_db
from utils.config import get_config


async def check_scans():
    """Check scan data."""
    # Initialize database
    config = get_config()
    await init_db(config)

    db = get_db()
    scans_collection = db.scans

    # Get all scans
    all_scans = await scans_collection.find({}).to_list(length=None)
    print(f"Total scans: {len(all_scans)}")

    # Count by status
    completed = await scans_collection.count_documents({"status": "completed"})
    scanning = await scans_collection.count_documents({"status": "scanning"})
    queued = await scans_collection.count_documents({"status": "queued"})
    failed = await scans_collection.count_documents({"status": "failed"})

    print(f"\nStatus breakdown:")
    print(f"  Completed: {completed}")
    print(f"  Scanning:  {scanning}")
    print(f"  Queued:    {queued}")
    print(f"  Failed:    {failed}")

    # Check completed scans for completed_at
    if completed > 0:
        print(f"\nCompleted scans details:")
        completed_scans = await scans_collection.find({"status": "completed"}).to_list(length=10)
        for scan in completed_scans[:3]:  # Show first 3
            has_completed_at = "completed_at" in scan
            completed_at_value = scan.get("completed_at", "NOT SET")
            print(f"  Scan {scan['_id']}: completed_at = {completed_at_value} (exists: {has_completed_at})")

    await close_db()


if __name__ == "__main__":
    asyncio.run(check_scans())
