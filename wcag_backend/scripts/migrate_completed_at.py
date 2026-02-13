"""
Migration script to backfill completed_at field for existing completed scans.

This script sets completed_at = updated_at for all completed scans that don't have it.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import init_db, get_db, close_db
from utils.config import get_config


async def migrate_completed_at():
    """Backfill completed_at for existing completed scans."""
    # Initialize database connection
    config = get_config()
    await init_db(config)

    db = get_db()
    scans_collection = db.scans

    # Find all completed scans without completed_at
    query = {
        "status": "completed",
        "completed_at": {"$exists": False}
    }

    scans = await scans_collection.find(query).to_list(length=None)

    print(f"Found {len(scans)} completed scans without completed_at")

    updated_count = 0
    for scan in scans:
        # Use updated_at if available, otherwise use created_at
        completed_at = scan.get("updated_at") or scan.get("created_at") or datetime.utcnow()

        result = await scans_collection.update_one(
            {"_id": scan["_id"]},
            {"$set": {"completed_at": completed_at}}
        )

        if result.modified_count > 0:
            updated_count += 1

    print(f"Successfully updated {updated_count} scans")
    return updated_count


async def main():
    """Main migration function."""
    print("Starting migration: Backfill completed_at for completed scans")
    print("-" * 60)

    try:
        result = await migrate_completed_at()
        print("-" * 60)
        print(f"Migration completed: {result} scans updated")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
