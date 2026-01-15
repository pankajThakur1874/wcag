"""FastAPI dependencies for dependency injection."""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from jose import JWTError, jwt
from datetime import datetime, timedelta

from scanner_v2.database.connection import MongoDB
from scanner_v2.database.repositories.user_repo import UserRepository
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.repositories.scan_repo import ScanRepository
from scanner_v2.database.repositories.page_repo import PageRepository
from scanner_v2.database.repositories.issue_repo import IssueRepository
from scanner_v2.workers.queue_manager import QueueManager
from scanner_v2.utils.config import Config, get_config
from scanner_v2.utils.logger import get_logger
from scanner_v2.database.models import User

logger = get_logger("api.dependencies")

# Security
security = HTTPBearer()

# Singleton instances
_db_instance: Optional[MongoDB] = None
_queue_manager_instance: Optional[QueueManager] = None


def get_db_instance() -> MongoDB:
    """Get MongoDB instance."""
    global _db_instance
    if _db_instance is None:
        raise RuntimeError("Database not initialized")
    return _db_instance


def set_db_instance(db: MongoDB) -> None:
    """Set MongoDB instance."""
    global _db_instance
    _db_instance = db


def get_queue_manager_instance() -> QueueManager:
    """Get QueueManager instance."""
    global _queue_manager_instance
    if _queue_manager_instance is None:
        raise RuntimeError("Queue manager not initialized")
    return _queue_manager_instance


def set_queue_manager_instance(queue_manager: QueueManager) -> None:
    """Set QueueManager instance."""
    global _queue_manager_instance
    _queue_manager_instance = queue_manager


# Dependencies
def get_database() -> AsyncIOMotorDatabase:
    """
    Get database dependency.

    Returns:
        MongoDB database instance
    """
    db = get_db_instance()
    return db.db


def get_queue_manager() -> QueueManager:
    """
    Get queue manager dependency.

    Returns:
        QueueManager instance
    """
    return get_queue_manager_instance()


# Repository dependencies
def get_user_repository(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)


def get_project_repository(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> ProjectRepository:
    """Get project repository."""
    return ProjectRepository(db)


def get_scan_repository(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> ScanRepository:
    """Get scan repository."""
    return ScanRepository(db)


def get_page_repository(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> PageRepository:
    """Get page repository."""
    return PageRepository(db)


def get_issue_repository(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> IssueRepository:
    """Get issue repository."""
    return IssueRepository(db)


# JWT Token handling
def create_access_token(data: dict, config: Config) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        config: Configuration

    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=config.security.jwt_expiry)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        config.security.jwt_secret,
        algorithm="HS256"
    )
    return encoded_jwt


def decode_access_token(token: str, config: Config) -> dict:
    """
    Decode JWT access token.

    Args:
        token: JWT token string
        config: Configuration

    Returns:
        Decoded token data

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            config.security.jwt_secret,
            algorithms=["HS256"]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    config: Annotated[Config, Depends(get_config)]
) -> User:
    """
    Get current authenticated user.

    Args:
        credentials: HTTP bearer credentials
        user_repo: User repository
        config: Configuration

    Returns:
        Current user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_access_token(token, config)

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user (can add active check here).

    Args:
        current_user: Current user

    Returns:
        Current active user
    """
    # Can add is_active check here if needed
    return current_user


# Optional current user (for endpoints that work with or without auth)
async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
    config: Config = Depends(get_config)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Args:
        credentials: Optional HTTP bearer credentials
        user_repo: User repository
        config: Configuration

    Returns:
        Current user or None
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, user_repo, config)
    except HTTPException:
        return None
