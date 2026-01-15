"""Project management routes."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from scanner_v2.api.dependencies import (
    get_project_repository,
    get_current_active_user
)
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.models import User
from scanner_v2.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse
)
from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import ProjectNotFoundException

logger = get_logger("api.routes.projects")

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or URL")
):
    """
    List projects for current user.

    Args:
        current_user: Current authenticated user
        project_repo: Project repository
        skip: Number of projects to skip
        limit: Maximum number of projects to return
        search: Optional search query

    Returns:
        List of projects with pagination info
    """
    if search:
        projects, total = await project_repo.search(
            user_id=current_user.id,
            query=search,
            skip=skip,
            limit=limit
        )
    else:
        projects, total = await project_repo.get_by_user(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )

    return ProjectListResponse(
        projects=[
            ProjectResponse(
                id=p.id,
                user_id=p.user_id,
                name=p.name,
                base_url=p.base_url,
                description=p.description,
                settings=p.settings,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in projects
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)]
):
    """
    Create a new project.

    Args:
        request: Project creation request
        current_user: Current authenticated user
        project_repo: Project repository

    Returns:
        Created project
    """
    project = await project_repo.create(
        user_id=current_user.id,
        name=request.name,
        base_url=request.base_url,
        description=request.description,
        settings=request.settings
    )

    logger.info(f"Project created: {project.id} by user {current_user.email}")

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        base_url=project.base_url,
        description=project.description,
        settings=project.settings,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)]
):
    """
    Get project by ID.

    Args:
        project_id: Project ID
        current_user: Current authenticated user
        project_repo: Project repository

    Returns:
        Project details

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project = await project_repo.get_by_id(project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    # Check ownership
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        base_url=project.base_url,
        description=project.description,
        settings=project.settings,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)]
):
    """
    Update project.

    Args:
        project_id: Project ID
        request: Project update request
        current_user: Current authenticated user
        project_repo: Project repository

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or access denied
    """
    # Check ownership
    try:
        project = await project_repo.get_by_id(project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )

    # Prepare updates
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.base_url is not None:
        updates["base_url"] = request.base_url
    if request.description is not None:
        updates["description"] = request.description
    if request.settings is not None:
        from scanner_v2.database.models import to_mongo_dict
        updates["settings"] = to_mongo_dict(request.settings)

    # Update project
    updated_project = await project_repo.update(project_id, updates)

    logger.info(f"Project updated: {project_id} by user {current_user.email}")

    return ProjectResponse(
        id=updated_project.id,
        user_id=updated_project.user_id,
        name=updated_project.name,
        base_url=updated_project.base_url,
        description=updated_project.description,
        settings=updated_project.settings,
        created_at=updated_project.created_at,
        updated_at=updated_project.updated_at
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)]
):
    """
    Delete project.

    Args:
        project_id: Project ID
        current_user: Current authenticated user
        project_repo: Project repository

    Raises:
        HTTPException: If project not found or access denied
    """
    # Check ownership
    try:
        project = await project_repo.get_by_id(project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )

    # Delete project
    await project_repo.delete(project_id)

    logger.info(f"Project deleted: {project_id} by user {current_user.email}")
