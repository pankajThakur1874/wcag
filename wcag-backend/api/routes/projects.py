"""Project API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
import math

from wcag_backend.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectSuccessResponse,
    ProjectDetailSuccessResponse
)
from wcag_backend.schemas.common import PaginatedResponse, PaginationMetadata, SuccessResponse
from wcag_backend.database.repositories.project_repo import ProjectRepository
from wcag_backend.api.dependencies import CurrentUser, get_user_repository
from wcag_backend.utils.exceptions import ProjectNotFoundException
from motor.motor_asyncio import AsyncIOMotorDatabase
from wcag_backend.database.connection import get_db


router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> ProjectRepository:
    """Get project repository instance."""
    return ProjectRepository(db)


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    current_user: CurrentUser,
    project_repo: ProjectRepository = Depends(get_project_repository),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(active|archived)$")
):
    """
    List projects with pagination and filtering.

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 10, max: 100)
    - status: Filter by status (active or archived)
    """
    # Get projects
    projects, total_count = await project_repo.list_with_filters(
        user_id=current_user.id,
        status=status,
        page=page,
        limit=limit
    )

    # Calculate pagination metadata
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    return PaginatedResponse(
        success=True,
        data=projects,
        pagination=PaginationMetadata(
            page=page,
            limit=limit,
            totalPages=total_pages,
            totalItems=total_count
        )
    )


@router.post("", response_model=ProjectSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    current_user: CurrentUser,
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """
    Create a new project.

    Requires authentication.
    """
    project = await project_repo.create(
        user_id=current_user.id,
        name=request.name,
        url=str(request.url),
        description=request.description
    )

    project_response = ProjectResponse(
        id=project.id,
        name=project.name,
        url=project.url,
        description=project.description,
        status=project.status.value,
        score=None,
        lastScan=None,
        createdAt=project.created_at,
        updatedAt=project.updated_at
    )

    return ProjectSuccessResponse(success=True, data=project_response)


@router.get("/{project_id}", response_model=ProjectDetailSuccessResponse)
async def get_project(
    project_id: str,
    current_user: CurrentUser,
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """
    Get a single project by ID.

    Returns detailed project information including scan count.
    """
    try:
        project_detail = await project_repo.get_detail(project_id, current_user.id)

        return ProjectDetailSuccessResponse(
            success=True,
            data=ProjectDetailResponse(**project_detail)
        )

    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Project not found."
                }
            }
        )


@router.put("/{project_id}", response_model=ProjectSuccessResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: CurrentUser,
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """
    Update a project.

    Only provided fields will be updated.
    """
    try:
        # Build update dict (only include provided fields)
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.url is not None:
            updates["url"] = str(request.url)
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = request.status

        project = await project_repo.update(project_id, current_user.id, **updates)

        project_response = ProjectResponse(
            id=project.id,
            name=project.name,
            url=project.url,
            description=project.description,
            status=project.status.value,
            score=None,  # Will be enriched by list endpoint
            lastScan=None,
            createdAt=project.created_at,
            updatedAt=project.updated_at
        )

        return ProjectSuccessResponse(success=True, data=project_response)

    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Project not found."
                }
            }
        )


@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(
    project_id: str,
    current_user: CurrentUser,
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """
    Delete a project.

    This will also delete all associated scans and issues.
    """
    try:
        await project_repo.delete(project_id, current_user.id)

        return SuccessResponse(
            success=True,
            message="Project deleted successfully."
        )

    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Project not found."
                }
            }
        )
