"""Scan repository for database operations."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import math

from wcag_backend.database.models import Scan, ScanType, ScanStatus, ScanConfig, to_mongo_dict
from wcag_backend.utils.exceptions import ScanNotFoundException


class ScanRepository:
    """Repository for Scan collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize scan repository.

        Args:
            db: MongoDB database instance
        """
        self.collection = db.scans
        self.projects_collection = db.projects

    async def create(
        self,
        user_id: str,
        url: str,
        scan_type: str,
        config: Dict[str, Any],
        project_id: Optional[str] = None
    ) -> Scan:
        """
        Create a new scan.

        Args:
            user_id: User ID
            url: URL to scan
            scan_type: Type of scan (quick or full)
            config: Scan configuration
            project_id: Optional project ID

        Returns:
            Created Scan object
        """
        scan = Scan(
            user_id=user_id,
            project_id=project_id,
            url=url,
            type=ScanType(scan_type),
            status=ScanStatus.QUEUED,
            config=ScanConfig(**config)
        )

        # Insert into database
        scan_dict = to_mongo_dict(scan)
        result = await self.collection.insert_one(scan_dict)

        # Update scan with generated ID
        scan.id = str(result.inserted_id)

        return scan

    async def get_by_id(self, scan_id: str) -> Dict[str, Any]:
        """
        Get scan by ID.

        Args:
            scan_id: Scan ID

        Returns:
            Scan dictionary

        Raises:
            ScanNotFoundException: If scan not found
        """
        try:
            doc = await self.collection.find_one({"_id": ObjectId(scan_id)})
        except Exception:
            raise ScanNotFoundException(scan_id)

        if not doc:
            raise ScanNotFoundException(scan_id)

        # Convert MongoDB document
        doc["_id"] = str(doc["_id"])
        return doc

    async def update_status(self, scan_id: str, status: str, error: Optional[str] = None) -> None:
        """
        Update scan status.

        Args:
            scan_id: Scan ID
            status: New status
            error: Optional error message

        Raises:
            ScanNotFoundException: If scan not found
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if status == "scanning" and not error:
            update_data["started_at"] = datetime.utcnow()

        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()

        if error:
            update_data["error"] = error

        result = await self.collection.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ScanNotFoundException(scan_id)

    async def update_progress(self, scan_id: str, progress_data: Dict[str, Any]) -> None:
        """
        Update scan progress.

        Args:
            scan_id: Scan ID
            progress_data: Progress information

        Raises:
            ScanNotFoundException: If scan not found
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {"progress": progress_data, "updated_at": datetime.utcnow()}}
        )

        if result.matched_count == 0:
            raise ScanNotFoundException(scan_id)

    async def update_results(self, scan_id: str, results_data: Dict[str, Any]) -> None:
        """
        Update scan with final results.

        Args:
            scan_id: Scan ID
            results_data: Results data including score, issues_count, etc.

        Raises:
            ScanNotFoundException: If scan not found
        """
        results_data["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": results_data}
        )

        if result.matched_count == 0:
            raise ScanNotFoundException(scan_id)

    async def list_with_filters(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[dict], int]:
        """
        List scans with filters and pagination.

        Args:
            user_id: User ID
            project_id: Optional project ID filter
            status: Optional status filter
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (scans list, total count)
        """
        # Build query
        query = {"user_id": user_id}
        if project_id:
            query["project_id"] = project_id
        if status:
            query["status"] = status

        # Get total count
        total_count = await self.collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * limit

        # Get scans
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        scans = await cursor.to_list(length=limit)

        # Enrich with project names
        enriched_scans = []
        for scan in scans:
            scan["_id"] = str(scan["_id"])

            # Get project name if project_id exists
            project_name = None
            if scan.get("project_id"):
                project = await self.projects_collection.find_one({"_id": ObjectId(scan["project_id"])})
                if project:
                    project_name = project["name"]

            enriched_scans.append({
                "id": scan["_id"],
                "projectId": scan.get("project_id"),
                "projectName": project_name,
                "url": scan["url"],
                "type": scan["type"],
                "status": scan["status"],
                "score": scan.get("score"),
                "issuesCount": scan.get("issues_count", 0),
                "duration": scan.get("duration"),
                "createdAt": scan["created_at"],
                "completedAt": scan.get("completed_at")
            })

        return enriched_scans, total_count

    async def get_detail(self, scan_id: str, user_id: str) -> dict:
        """
        Get detailed scan information.

        Args:
            scan_id: Scan ID
            user_id: User ID (for ownership check)

        Returns:
            Scan detail dictionary

        Raises:
            ScanNotFoundException: If scan not found or user doesn't own it
        """
        scan = await self.get_by_id(scan_id)

        # Check ownership
        if scan.get("user_id") != user_id:
            raise ScanNotFoundException(scan_id)

        # Get project name
        project_name = None
        if scan.get("project_id"):
            project = await self.projects_collection.find_one({"_id": ObjectId(scan["project_id"])})
            if project:
                project_name = project["name"]

        return {
            "id": scan["_id"],
            "projectId": scan.get("project_id"),
            "projectName": project_name,
            "url": scan["url"],
            "type": scan["type"],
            "status": scan["status"],
            "score": scan.get("score"),
            "issuesCount": scan.get("issues_count", 0),
            "duration": scan.get("duration"),
            "pagesScanned": scan.get("progress", {}).get("pages_scanned", 0),
            "scanners": scan.get("config", {}).get("scanners", []),
            "createdAt": scan["created_at"],
            "completedAt": scan.get("completed_at")
        }

    async def count_by_user(self, user_id: str, status: Optional[str] = None) -> int:
        """
        Count scans for a user.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Count of scans
        """
        query = {"user_id": user_id}
        if status:
            query["status"] = status

        return await self.collection.count_documents(query)

    async def average_score_by_user(self, user_id: str) -> int:
        """
        Calculate average score for completed scans.

        Args:
            user_id: User ID

        Returns:
            Average score (0-100)
        """
        pipeline = [
            {"$match": {"user_id": user_id, "status": "completed", "score": {"$exists": True}}},
            {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
        ]

        result = await self.collection.aggregate(pipeline).to_list(length=1)

        if result:
            return round(result[0]["avg_score"])

        return 0
