"""Project repository for database operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.helpers import utc_now, is_valid_object_id
from scanner_v2.utils.exceptions import ProjectNotFoundException, InvalidInputError
from scanner_v2.database.models import Project, ProjectSettings, to_mongo_dict

logger = get_logger("project_repo")


class ProjectRepository:
    """Repository for project operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize project repository.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.projects

    async def create(
        self,
        user_id: str,
        name: str,
        base_url: str,
        description: Optional[str] = None,
        settings: Optional[ProjectSettings] = None
    ) -> Project:
        """
        Create a new project.

        Args:
            user_id: User ID
            name: Project name
            base_url: Base URL
            description: Optional description
            settings: Optional project settings

        Returns:
            Created project
        """
        project = Project(
            user_id=user_id,
            name=name,
            base_url=base_url,
            description=description,
            settings=settings or ProjectSettings(),
            created_at=utc_now(),
            updated_at=utc_now()
        )

        # Convert to MongoDB document
        doc = to_mongo_dict(project)

        # Insert
        result = await self.collection.insert_one(doc)
        project.id = str(result.inserted_id)

        logger.info(f"Created project: {project.id} - {name}")

        return project

    async def get_by_id(self, project_id: str) -> Project:
        """
        Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project

        Raises:
            ProjectNotFoundException: If project not found
        """
        if not is_valid_object_id(project_id):
            raise InvalidInputError(f"Invalid project ID: {project_id}")

        doc = await self.collection.find_one({"_id": ObjectId(project_id)})

        if not doc:
            raise ProjectNotFoundException(project_id)

        return self._doc_to_project(doc)

    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Project], int]:
        """
        Get projects by user ID.

        Args:
            user_id: User ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (projects list, total count)
        """
        # Get total count
        total = await self.collection.count_documents({"user_id": user_id})

        # Get projects
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)

        projects = []
        async for doc in cursor:
            projects.append(self._doc_to_project(doc))

        logger.debug(f"Found {len(projects)} projects for user {user_id}")

        return projects, total

    async def update(
        self,
        project_id: str,
        updates: Dict[str, Any]
    ) -> Project:
        """
        Update project.

        Args:
            project_id: Project ID
            updates: Fields to update

        Returns:
            Updated project

        Raises:
            ProjectNotFoundException: If project not found
        """
        if not is_valid_object_id(project_id):
            raise InvalidInputError(f"Invalid project ID: {project_id}")

        # Add updated_at
        updates["updated_at"] = utc_now()

        # Update
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(project_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            raise ProjectNotFoundException(project_id)

        logger.info(f"Updated project: {project_id}")

        return self._doc_to_project(result)

    async def delete(self, project_id: str) -> bool:
        """
        Delete project.

        Args:
            project_id: Project ID

        Returns:
            True if deleted

        Raises:
            ProjectNotFoundException: If project not found
        """
        if not is_valid_object_id(project_id):
            raise InvalidInputError(f"Invalid project ID: {project_id}")

        result = await self.collection.delete_one({"_id": ObjectId(project_id)})

        if result.deleted_count == 0:
            raise ProjectNotFoundException(project_id)

        logger.info(f"Deleted project: {project_id}")

        return True

    async def search(
        self,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Project], int]:
        """
        Search projects by name or URL.

        Args:
            user_id: User ID
            query: Search query
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (projects list, total count)
        """
        filter_query = {
            "user_id": user_id,
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"base_url": {"$regex": query, "$options": "i"}},
            ]
        }

        # Get total count
        total = await self.collection.count_documents(filter_query)

        # Get projects
        cursor = self.collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)

        projects = []
        async for doc in cursor:
            projects.append(self._doc_to_project(doc))

        return projects, total

    def _doc_to_project(self, doc: Dict) -> Project:
        """
        Convert MongoDB document to Project.

        Args:
            doc: MongoDB document

        Returns:
            Project instance
        """
        doc["_id"] = str(doc["_id"])

        # Convert settings if it exists
        if "settings" in doc and isinstance(doc["settings"], dict):
            doc["settings"] = ProjectSettings(**doc["settings"])

        return Project(**doc)
