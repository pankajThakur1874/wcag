"""Project repository for database operations."""

from typing import List, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import math

from wcag_backend.database.models import Project, ProjectStatus, to_mongo_dict
from wcag_backend.utils.exceptions import ProjectNotFoundException


class ProjectRepository:
    """Repository for Project collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize project repository.

        Args:
            db: MongoDB database instance
        """
        self.collection = db.projects
        self.scans_collection = db.scans

    async def create(
        self,
        user_id: str,
        name: str,
        url: str,
        description: Optional[str] = None
    ) -> Project:
        """
        Create a new project.

        Args:
            user_id: Owner user ID
            name: Project name
            url: Project URL
            description: Optional description

        Returns:
            Created Project object
        """
        project = Project(
            user_id=user_id,
            name=name,
            url=str(url),
            description=description,
            status=ProjectStatus.ACTIVE
        )

        # Insert into database
        project_dict = to_mongo_dict(project)
        result = await self.collection.insert_one(project_dict)

        # Update project with generated ID
        project.id = str(result.inserted_id)

        return project

    async def get_by_id(self, project_id: str, user_id: str) -> Project:
        """
        Get project by ID (ensures user owns the project).

        Args:
            project_id: Project ID
            user_id: User ID (for ownership check)

        Returns:
            Project object

        Raises:
            ProjectNotFoundException: If project not found or user doesn't own it
        """
        try:
            doc = await self.collection.find_one({
                "_id": ObjectId(project_id),
                "user_id": user_id
            })
        except Exception:
            raise ProjectNotFoundException(project_id)

        if not doc:
            raise ProjectNotFoundException(project_id)

        # Convert MongoDB document to Project model
        doc["_id"] = str(doc["_id"])
        return Project(**doc)

    async def list_with_filters(
        self,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[dict], int]:
        """
        List projects with filters and pagination.

        Args:
            user_id: User ID
            status: Optional status filter (active or archived)
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (projects list with metadata, total count)
        """
        # Build query
        query = {"user_id": user_id}
        if status:
            query["status"] = status

        # Get total count
        total_count = await self.collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * limit

        # Get projects
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        projects = await cursor.to_list(length=limit)

        # Enrich with scan data
        enriched_projects = []
        for project in projects:
            project["_id"] = str(project["_id"])

            # Get last scan for this project
            last_scan = await self.scans_collection.find_one(
                {"project_id": str(project["_id"]), "status": "completed"},
                sort=[("completed_at", -1)]
            )

            project_data = {
                "id": project["_id"],
                "name": project["name"],
                "url": project["url"],
                "description": project.get("description"),
                "status": project["status"],
                "score": last_scan.get("score") if last_scan else None,
                "lastScan": last_scan.get("completed_at") if last_scan else None,
                "createdAt": project["created_at"],
                "updatedAt": project["updated_at"]
            }

            enriched_projects.append(project_data)

        return enriched_projects, total_count

    async def get_detail(self, project_id: str, user_id: str) -> dict:
        """
        Get detailed project information including scan count.

        Args:
            project_id: Project ID
            user_id: User ID (for ownership check)

        Returns:
            Project detail dictionary

        Raises:
            ProjectNotFoundException: If project not found
        """
        project = await self.get_by_id(project_id, user_id)

        # Get scan count
        scan_count = await self.scans_collection.count_documents({"project_id": project_id})

        # Get last scan
        last_scan = await self.scans_collection.find_one(
            {"project_id": project_id, "status": "completed"},
            sort=[("completed_at", -1)]
        )

        return {
            "id": project.id,
            "name": project.name,
            "url": project.url,
            "description": project.description,
            "status": project.status.value,
            "score": last_scan.get("score") if last_scan else None,
            "lastScan": last_scan.get("completed_at") if last_scan else None,
            "scanCount": scan_count,
            "createdAt": project.created_at,
            "updatedAt": project.updated_at
        }

    async def update(self, project_id: str, user_id: str, **updates) -> Project:
        """
        Update project fields.

        Args:
            project_id: Project ID
            user_id: User ID (for ownership check)
            **updates: Fields to update

        Returns:
            Updated Project object

        Raises:
            ProjectNotFoundException: If project not found
        """
        # Add updated_at timestamp
        updates["updated_at"] = datetime.utcnow()

        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}

        result = await self.collection.update_one(
            {"_id": ObjectId(project_id), "user_id": user_id},
            {"$set": updates}
        )

        if result.matched_count == 0:
            raise ProjectNotFoundException(project_id)

        return await self.get_by_id(project_id, user_id)

    async def delete(self, project_id: str, user_id: str) -> None:
        """
        Delete a project.

        Args:
            project_id: Project ID
            user_id: User ID (for ownership check)

        Raises:
            ProjectNotFoundException: If project not found
        """
        result = await self.collection.delete_one({
            "_id": ObjectId(project_id),
            "user_id": user_id
        })

        if result.deleted_count == 0:
            raise ProjectNotFoundException(project_id)

    async def count_by_user(self, user_id: str, status: Optional[str] = None) -> int:
        """
        Count projects for a user.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Count of projects
        """
        query = {"user_id": user_id}
        if status:
            query["status"] = status

        return await self.collection.count_documents(query)
