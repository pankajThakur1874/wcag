"""Project management routes."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from scanner_v2.api.dependencies import (
    get_project_repository,
    get_scan_repository,
    get_queue_manager,
    get_current_active_user
)
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.repositories.scan_repo import ScanRepository
from scanner_v2.database.models import User, ScanConfig, ScanType
from scanner_v2.workers.queue_manager import QueueManager
from scanner_v2.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse
)
from scanner_v2.schemas.scan import ScanResponse, JobType, JobPriority
from pydantic import BaseModel
from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import ProjectNotFoundException

logger = get_logger("api.routes.projects")

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=ProjectListResponse, response_model_by_alias=False)
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

    from scanner_v2.schemas.project import ProjectSettingsSchema

    return ProjectListResponse(
        projects=[
            ProjectResponse(
                _id=p.id or str(p.__dict__.get('_id', '')),
                user_id=p.user_id,
                name=p.name,
                base_url=p.base_url,
                description=p.description,
                settings=ProjectSettingsSchema(**p.settings.model_dump()),
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in projects
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=ProjectResponse, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
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
    from scanner_v2.database.models import ProjectSettings

    # Convert settings schema to model
    settings = None
    if request.settings:
        settings = ProjectSettings(**request.settings.model_dump())

    project = await project_repo.create(
        user_id=current_user.id,
        name=request.name,
        base_url=request.base_url,
        description=request.description,
        settings=settings
    )

    logger.info(f"Project created: {project.id} by user {current_user.email}")

    from scanner_v2.schemas.project import ProjectSettingsSchema

    return ProjectResponse(
        _id=project.id or str(project.__dict__.get('_id', '')),
        user_id=project.user_id,
        name=project.name,
        base_url=project.base_url,
        description=project.description,
        settings=ProjectSettingsSchema(**project.settings.model_dump()),
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.get("/{project_id}", response_model=ProjectResponse, response_model_by_alias=False)
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

    from scanner_v2.schemas.project import ProjectSettingsSchema

    return ProjectResponse(
        _id=project.id or str(project.__dict__.get('_id', '')),
        user_id=project.user_id,
        name=project.name,
        base_url=project.base_url,
        description=project.description,
        settings=ProjectSettingsSchema(**project.settings.model_dump()),
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.put("/{project_id}", response_model=ProjectResponse, response_model_by_alias=False)
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
        from scanner_v2.database.models import ProjectSettings, to_mongo_dict
        # Convert schema to model
        settings_model = ProjectSettings(**request.settings.model_dump())
        updates["settings"] = to_mongo_dict(settings_model)

    # Update project
    updated_project = await project_repo.update(project_id, updates)

    logger.info(f"Project updated: {project_id} by user {current_user.email}")

    from scanner_v2.schemas.project import ProjectSettingsSchema

    return ProjectResponse(
        _id=updated_project.id or str(updated_project.__dict__.get('_id', '')),
        user_id=updated_project.user_id,
        name=updated_project.name,
        base_url=updated_project.base_url,
        description=updated_project.description,
        settings=ProjectSettingsSchema(**updated_project.settings.model_dump()),
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


class ProjectScanRequest(BaseModel):
    """Request to start a project scan."""
    scan_type: str = "full"
    scanners: Optional[list[str]] = None


@router.post("/{project_id}/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_project_scan(
    project_id: str,
    request: ProjectScanRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    scan_repo: Annotated[ScanRepository, Depends(get_scan_repository)],
    queue_manager: Annotated[QueueManager, Depends(get_queue_manager)]
):
    """
    Create and start a new scan for a project.

    Args:
        project_id: Project ID
        request: Scan configuration request
        current_user: Current authenticated user
        project_repo: Project repository
        scan_repo: Scan repository
        queue_manager: Queue manager

    Returns:
        Created scan

    Raises:
        HTTPException: If project not found or access denied
    """
    # Verify project exists and user has access
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

    # Create scan configuration based on project settings
    scan_config = ScanConfig(
        url=project.base_url,
        max_pages=project.settings.max_pages if project.settings else 10,
        scanners=request.scanners or project.settings.scanners if project.settings and project.settings.scanners else None,
        scan_depth=project.settings.scan_depth if project.settings else 3,
        follow_external_links=project.settings.follow_external_links if project.settings else False
    )

    # Determine scan type
    scan_type = ScanType.FULL if request.scan_type == "full" else ScanType.QUICK

    # Create scan
    scan = await scan_repo.create(
        project_id=project_id,
        user_id=current_user.id,
        scan_type=scan_type,
        config=scan_config
    )

    # Enqueue scan job
    job_id = await queue_manager.enqueue_job(
        job_type=JobType.SCAN,
        priority=JobPriority.NORMAL,
        data={
            "scan_id": scan.id,
            "project_id": project_id,
            "user_id": current_user.id,
            "config": scan_config.model_dump()
        }
    )

    logger.info(f"Project scan created: {scan.id} for project {project_id} by user {current_user.email}")

    return ScanResponse(
        id=scan.id,
        project_id=scan.project_id,
        user_id=scan.user_id,
        scan_type=scan.scan_type,
        status=scan.status,
        config=scan.config,
        scores=scan.scores,
        summary=scan.summary,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        started_at=scan.started_at,
        completed_at=scan.completed_at
    )
