"""Scan repository for database operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, is_valid_object_id
from scanner_v2.utils.exceptions import ScanNotFoundException, InvalidInputError
from scanner_v2.database.models import (
    Scan, ScanStatus, ScanType, ScanConfig, ScanProgress,
    ScanSummary, ScanScores, to_mongo_dict
)

logger = get_logger("scan_repo")


class ScanRepository:
    """Repository for scan operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize scan repository.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.scans

    async def create(
        self,
        project_id: str,
        scan_type: ScanType = ScanType.FULL,
        config: Optional[ScanConfig] = None
    ) -> Scan:
        """
        Create a new scan.

        Args:
            project_id: Project ID
            scan_type: Type of scan
            config: Scan configuration

        Returns:
            Created scan
        """
        scan = Scan(
            project_id=project_id,
            scan_type=scan_type,
            status=ScanStatus.QUEUED,
            config=config or ScanConfig(),
            created_at=utc_now(),
            updated_at=utc_now()
        )

        # Convert to MongoDB document
        doc = to_mongo_dict(scan)

        # Insert
        result = await self.collection.insert_one(doc)
        scan.id = str(result.inserted_id)

        logger.info(f"Created scan: {scan.id} for project {project_id}")

        return scan

    async def get_by_id(self, scan_id: str) -> Scan:
        """
        Get scan by ID.

        Args:
            scan_id: Scan ID

        Returns:
            Scan

        Raises:
            ScanNotFoundException: If scan not found
        """
        if not is_valid_object_id(scan_id):
            raise InvalidInputError(f"Invalid scan ID: {scan_id}")

        doc = await self.collection.find_one({"_id": ObjectId(scan_id)})

        if not doc:
            raise ScanNotFoundException(scan_id)

        return self._doc_to_scan(doc)

    async def get_by_project(
        self,
        project_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Scan], int]:
        """
        Get scans by project ID.

        Args:
            project_id: Project ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (scans list, total count)
        """
        # Get total count
        total = await self.collection.count_documents({"project_id": project_id})

        # Get scans
        cursor = self.collection.find({"project_id": project_id}).sort("created_at", -1).skip(skip).limit(limit)

        scans = []
        async for doc in cursor:
            scans.append(self._doc_to_scan(doc))

        logger.debug(f"Found {len(scans)} scans for project {project_id}")

        return scans, total

    async def update_status(
        self,
        scan_id: str,
        status: ScanStatus,
        error_message: Optional[str] = None
    ) -> Scan:
        """
        Update scan status.

        Args:
            scan_id: Scan ID
            status: New status
            error_message: Optional error message

        Returns:
            Updated scan
        """
        if not is_valid_object_id(scan_id):
            raise InvalidInputError(f"Invalid scan ID: {scan_id}")

        updates = {
            "status": status.value,
            "updated_at": utc_now()
        }

        if status == ScanStatus.SCANNING:
            updates["started_at"] = utc_now()
        elif status in [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]:
            updates["completed_at"] = utc_now()

        if error_message:
            updates["error_message"] = error_message

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(scan_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            raise ScanNotFoundException(scan_id)

        logger.info(f"Updated scan {scan_id} status to {status.value}")

        return self._doc_to_scan(result)

    async def update_progress(
        self,
        scan_id: str,
        progress: ScanProgress
    ) -> Scan:
        """
        Update scan progress.

        Args:
            scan_id: Scan ID
            progress: Scan progress

        Returns:
            Updated scan
        """
        if not is_valid_object_id(scan_id):
            raise InvalidInputError(f"Invalid scan ID: {scan_id}")

        updates = {
            "progress": to_mongo_dict(progress),
            "updated_at": utc_now()
        }

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(scan_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            raise ScanNotFoundException(scan_id)

        return self._doc_to_scan(result)

    async def update_results(
        self,
        scan_id: str,
        summary: ScanSummary,
        scores: ScanScores
    ) -> Scan:
        """
        Update scan results (summary and scores).

        Args:
            scan_id: Scan ID
            summary: Scan summary
            scores: Scan scores

        Returns:
            Updated scan
        """
        if not is_valid_object_id(scan_id):
            raise InvalidInputError(f"Invalid scan ID: {scan_id}")

        updates = {
            "summary": to_mongo_dict(summary),
            "scores": to_mongo_dict(scores),
            "updated_at": utc_now()
        }

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(scan_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            raise ScanNotFoundException(scan_id)

        logger.info(f"Updated scan {scan_id} results")

        return self._doc_to_scan(result)

    async def get_by_status(
        self,
        status: ScanStatus,
        limit: int = 100
    ) -> List[Scan]:
        """
        Get scans by status.

        Args:
            status: Scan status
            limit: Maximum to return

        Returns:
            List of scans
        """
        cursor = self.collection.find({"status": status.value}).limit(limit)

        scans = []
        async for doc in cursor:
            scans.append(self._doc_to_scan(doc))

        return scans

    async def get_recent_scans(
        self,
        limit: int = 10
    ) -> List[Scan]:
        """
        Get recent scans across all projects.

        Args:
            limit: Maximum to return

        Returns:
            List of recent scans
        """
        cursor = self.collection.find().sort("created_at", -1).limit(limit)

        scans = []
        async for doc in cursor:
            scans.append(self._doc_to_scan(doc))

        return scans

    async def get_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get scan statistics.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            Statistics dictionary
        """
        match_stage = {"project_id": project_id} if project_id else {}

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)

        stats = {
            "total": 0,
            "by_status": {}
        }

        async for doc in cursor:
            status = doc["_id"]
            count = doc["count"]
            stats["by_status"][status] = count
            stats["total"] += count

        return stats

    async def delete(self, scan_id: str) -> bool:
        """
        Delete scan.

        Args:
            scan_id: Scan ID

        Returns:
            True if deleted

        Raises:
            ScanNotFoundException: If scan not found
        """
        if not is_valid_object_id(scan_id):
            raise InvalidInputError(f"Invalid scan ID: {scan_id}")

        result = await self.collection.delete_one({"_id": ObjectId(scan_id)})

        if result.deleted_count == 0:
            raise ScanNotFoundException(scan_id)

        logger.info(f"Deleted scan: {scan_id}")

        return True

    def _doc_to_scan(self, doc: Dict) -> Scan:
        """
        Convert MongoDB document to Scan.

        Args:
            doc: MongoDB document

        Returns:
            Scan instance
        """
        doc["_id"] = str(doc["_id"])

        # Convert nested models
        if "config" in doc and isinstance(doc["config"], dict):
            doc["config"] = ScanConfig(**doc["config"])

        if "progress" in doc and isinstance(doc["progress"], dict):
            doc["progress"] = ScanProgress(**doc["progress"])

        if "summary" in doc and isinstance(doc["summary"], dict):
            doc["summary"] = ScanSummary(**doc["summary"])

        if "scores" in doc and isinstance(doc["scores"], dict):
            doc["scores"] = ScanScores(**doc["scores"])

        # Convert status enum
        if "status" in doc and isinstance(doc["status"], str):
            doc["status"] = ScanStatus(doc["status"])

        if "scan_type" in doc and isinstance(doc["scan_type"], str):
            doc["scan_type"] = ScanType(doc["scan_type"])

        return Scan(**doc)
