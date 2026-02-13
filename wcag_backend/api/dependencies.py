"""FastAPI dependency injection."""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from wcag_backend.database.connection import get_db
from wcag_backend.database.repositories.user_repo import UserRepository
from wcag_backend.database.repositories.refresh_token_repo import RefreshTokenRepository
from wcag_backend.database.models import User
from wcag_backend.core.auth_service import AuthService
from wcag_backend.utils.config import get_config
from wcag_backend.utils.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    UserNotFoundException
)


# Security scheme
security = HTTPBearer()


# Config dependency
def get_app_config():
    """Get application configuration."""
    return get_config()


# Auth service dependency
def get_auth_service(config = Depends(get_app_config)) -> AuthService:
    """Get auth service instance."""
    return AuthService(config)


# Repository dependencies
def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


def get_refresh_token_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> RefreshTokenRepository:
    """Get refresh token repository instance."""
    return RefreshTokenRepository(db)


# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials
        auth_service: Auth service instance
        user_repo: User repository instance

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Validate access token and get user_id
        user_id = auth_service.validate_access_token(credentials.credentials)

        # Get user from database
        user = await user_repo.get_by_id(user_id)

        return user

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Access token has expired. Please refresh your token."
                }
            }
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_INVALID",
                    "message": "Invalid access token."
                }
            }
        )
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User no longer exists."
                }
            }
        )


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
