"""Issue repository for database operations."""

from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import math

from wcag_backend.database.models import Issue, ImpactLevel, IssueStatus, to_mongo_dict
from wcag_backend.utils.exceptions import IssueNotFoundException


class IssueRepository:
    """Repository for Issue collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize issue repository.

        Args:
            db: MongoDB database instance
        """
        self.collection = db.issues

    async def create_many(self, issues_data: List[Dict[str, Any]]) -> List[str]:
        """
        Bulk create issues.

        Args:
            issues_data: List of issue dictionaries

        Returns:
            List of created issue IDs
        """
        if not issues_data:
            return []

        # Create Issue objects
        issues = []
        for data in issues_data:
            issue = Issue(
                scan_id=data["scan_id"],
                user_id=data["user_id"],
                page_url=data["page_url"],
                description=data["description"],
                impact=ImpactLevel(data["impact"]),
                wcag_criteria=data.get("wcag_criteria"),
                wcag_level=data.get("wcag_level"),
                selector=data.get("selector"),
                html_snippet=data.get("html_snippet"),
                how_to_fix=data.get("how_to_fix"),
                help_url=data.get("help_url"),
                status=IssueStatus.OPEN
            )
            issues.append(to_mongo_dict(issue))

        # Bulk insert
        result = await self.collection.insert_many(issues)

        return [str(id) for id in result.inserted_ids]

    async def list_with_filters(
        self,
        scan_id: str,
        impact: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[dict], int]:
        """
        List issues with filters and pagination.

        Args:
            scan_id: Scan ID
            impact: Optional impact filter (critical, serious, moderate, minor)
            status: Optional status filter (open, fixed, ignored)
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (issues list, total count)
        """
        # Build query
        query = {"scan_id": scan_id}
        if impact:
            query["impact"] = impact
        if status:
            query["status"] = status

        # Get total count
        total_count = await self.collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * limit

        # Get issues
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        issues = await cursor.to_list(length=limit)

        # Convert to response format
        issues_list = []
        for issue in issues:
            issues_list.append({
                "id": str(issue["_id"]),
                "scanId": issue["scan_id"],
                "description": issue["description"],
                "impact": issue["impact"],
                "wcagCriteria": issue.get("wcag_criteria"),
                "wcagLevel": issue.get("wcag_level"),
                "selector": issue.get("selector"),
                "htmlSnippet": issue.get("html_snippet"),
                "howToFix": issue.get("how_to_fix"),
                "helpUrl": issue.get("help_url"),
                "status": issue["status"],
                "pageUrl": issue["page_url"]
            })

        return issues_list, total_count

    async def update_status(self, issue_id: str, new_status: str, user_id: str) -> dict:
        """
        Update issue status.

        Args:
            issue_id: Issue ID
            new_status: New status (open, fixed, ignored)
            user_id: User ID (for ownership check)

        Returns:
            Updated issue dictionary

        Raises:
            IssueNotFoundException: If issue not found or user doesn't own it
        """
        # Verify ownership and update
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(issue_id), "user_id": user_id},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
            return_document=True
        )

        if not result:
            raise IssueNotFoundException(issue_id)

        return {
            "id": str(result["_id"]),
            "status": result["status"],
            "updatedAt": result["updated_at"]
        }

    async def count_by_user(
        self,
        user_id: str,
        impact: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Count issues for a user.

        Args:
            user_id: User ID
            impact: Optional impact filter
            status: Optional status filter

        Returns:
            Count of issues
        """
        query = {"user_id": user_id}
        if impact:
            query["impact"] = impact
        if status:
            query["status"] = status

        return await self.collection.count_documents(query)

    async def count_by_impact(self, user_id: str) -> Dict[str, int]:
        """
        Count issues by impact level for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with counts by impact level
        """
        pipeline = [
            {"$match": {"user_id": user_id, "status": "open"}},
            {"$group": {"_id": "$impact", "count": {"$sum": 1}}}
        ]

        result = await self.collection.aggregate(pipeline).to_list(length=10)

        counts = {
            "critical": 0,
            "serious": 0,
            "moderate": 0,
            "minor": 0
        }

        for item in result:
            counts[item["_id"]] = item["count"]

        return counts
