"""Issue repository for database operations."""

from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, is_valid_object_id
from scanner_v2.utils.exceptions import IssueNotFoundException, InvalidInputError
from scanner_v2.database.models import Issue, IssueStatus, ImpactLevel, WCAGLevel, Principle, to_mongo_dict

logger = get_logger("issue_repo")


class IssueRepository:
    """Repository for issue operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize issue repository.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.issues

    async def create(self, issue: Issue) -> Issue:
        """
        Create a new issue.

        Args:
            issue: Issue to create

        Returns:
            Created issue with ID
        """
        doc = to_mongo_dict(issue)
        doc["created_at"] = utc_now()

        result = await self.collection.insert_one(doc)
        issue.id = str(result.inserted_id)

        logger.debug(f"Created issue: {issue.id}")

        return issue

    async def create_many(self, issues: List[Issue]) -> List[str]:
        """
        Create multiple issues.

        Args:
            issues: List of issues to create

        Returns:
            List of created issue IDs
        """
        if not issues:
            return []

        docs = []
        for issue in issues:
            doc = to_mongo_dict(issue)
            doc["created_at"] = utc_now()
            docs.append(doc)

        result = await self.collection.insert_many(docs)

        issue_ids = [str(id) for id in result.inserted_ids]

        logger.info(f"Created {len(issue_ids)} issues")

        return issue_ids

    async def get_by_id(self, issue_id: str) -> Issue:
        """
        Get issue by ID.

        Args:
            issue_id: Issue ID

        Returns:
            Issue

        Raises:
            IssueNotFoundException: If issue not found
        """
        if not is_valid_object_id(issue_id):
            raise InvalidInputError(f"Invalid issue ID: {issue_id}")

        doc = await self.collection.find_one({"_id": ObjectId(issue_id)})

        if not doc:
            raise IssueNotFoundException(issue_id)

        return self._doc_to_issue(doc)

    async def get_by_scan(
        self,
        scan_id: str,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Issue], int]:
        """
        Get issues by scan ID with optional filters.

        Args:
            scan_id: Scan ID
            skip: Number to skip
            limit: Maximum to return
            filters: Optional filters (impact, wcag_level, status, etc.)

        Returns:
            Tuple of (issues list, total count)
        """
        query = {"scan_id": scan_id}

        # Apply filters
        if filters:
            if "impact" in filters:
                query["impact"] = filters["impact"]
            if "wcag_level" in filters:
                query["wcag_level"] = filters["wcag_level"]
            if "principle" in filters:
                query["principle"] = filters["principle"]
            if "status" in filters:
                query["status"] = filters["status"]
            if "manual_review_required" in filters:
                query["manual_review_required"] = filters["manual_review_required"]

        # Get total count
        total = await self.collection.count_documents(query)

        # Get issues
        cursor = self.collection.find(query).skip(skip).limit(limit)

        issues = []
        async for doc in cursor:
            issues.append(self._doc_to_issue(doc))

        logger.debug(f"Found {len(issues)} issues for scan {scan_id}")

        return issues, total

    async def get_by_page(self, page_id: str) -> List[Issue]:
        """
        Get issues by page ID.

        Args:
            page_id: Page ID

        Returns:
            List of issues
        """
        cursor = self.collection.find({"page_id": page_id})

        issues = []
        async for doc in cursor:
            issues.append(self._doc_to_issue(doc))

        return issues

    async def update_status(
        self,
        issue_id: str,
        status: IssueStatus,
        notes: Optional[str] = None
    ) -> Issue:
        """
        Update issue status.

        Args:
            issue_id: Issue ID
            status: New status
            notes: Optional notes

        Returns:
            Updated issue
        """
        if not is_valid_object_id(issue_id):
            raise InvalidInputError(f"Invalid issue ID: {issue_id}")

        updates = {"status": status.value}

        if notes:
            updates["notes"] = notes

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(issue_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            raise IssueNotFoundException(issue_id)

        logger.info(f"Updated issue {issue_id} status to {status.value}")

        return self._doc_to_issue(result)

    async def get_summary_by_scan(self, scan_id: str) -> Dict[str, Any]:
        """
        Get issue summary for a scan.

        Args:
            scan_id: Scan ID

        Returns:
            Summary dictionary
        """
        pipeline = [
            {"$match": {"scan_id": scan_id}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "by_impact": {
                        "$push": "$impact"
                    },
                    "by_wcag_level": {
                        "$push": "$wcag_level"
                    },
                    "by_principle": {
                        "$push": "$principle"
                    }
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)

        async for doc in cursor:
            # Count by impact
            by_impact = {}
            for impact in doc["by_impact"]:
                by_impact[impact] = by_impact.get(impact, 0) + 1

            # Count by WCAG level
            by_wcag_level = {}
            for level in doc["by_wcag_level"]:
                by_wcag_level[level] = by_wcag_level.get(level, 0) + 1

            # Count by principle
            by_principle = {}
            for principle in doc["by_principle"]:
                by_principle[principle] = by_principle.get(principle, 0) + 1

            return {
                "total": doc["total"],
                "by_impact": by_impact,
                "by_wcag_level": by_wcag_level,
                "by_principle": by_principle
            }

        return {
            "total": 0,
            "by_impact": {},
            "by_wcag_level": {},
            "by_principle": {}
        }

    async def delete_by_scan(self, scan_id: str) -> int:
        """
        Delete all issues for a scan.

        Args:
            scan_id: Scan ID

        Returns:
            Number of deleted issues
        """
        result = await self.collection.delete_many({"scan_id": scan_id})

        logger.info(f"Deleted {result.deleted_count} issues for scan {scan_id}")

        return result.deleted_count

    def _doc_to_issue(self, doc: Dict) -> Issue:
        """
        Convert MongoDB document to Issue.

        Args:
            doc: MongoDB document

        Returns:
            Issue instance
        """
        doc["_id"] = str(doc["_id"])

        # Convert enums
        if "wcag_level" in doc and isinstance(doc["wcag_level"], str):
            doc["wcag_level"] = WCAGLevel(doc["wcag_level"])

        if "principle" in doc and isinstance(doc["principle"], str):
            doc["principle"] = Principle(doc["principle"])

        if "impact" in doc and isinstance(doc["impact"], str):
            doc["impact"] = ImpactLevel(doc["impact"])

        if "status" in doc and isinstance(doc["status"], str):
            doc["status"] = IssueStatus(doc["status"])

        return Issue(**doc)
