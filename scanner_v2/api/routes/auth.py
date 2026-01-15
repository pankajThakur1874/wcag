"""Authentication routes."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from scanner_v2.api.dependencies import (
    get_user_repository,
    get_current_active_user,
    create_access_token
)
from scanner_v2.database.repositories.user_repo import UserRepository
from scanner_v2.database.models import User
from scanner_v2.schemas.user import (
    UserCreateRequest,
    UserResponse,
    LoginRequest,
    LoginResponse
)
from scanner_v2.utils.config import Config, get_config
from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import InvalidCredentialsError

logger = get_logger("api.routes.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserCreateRequest,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
):
    """
    Register a new user.

    Args:
        request: User registration request
        user_repo: User repository

    Returns:
        Created user

    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    existing_user = await user_repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = await user_repo.create(
        email=request.email,
        password=request.password,
        name=request.name,
        role=request.role
    )

    logger.info(f"User registered: {user.email}")

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    config: Annotated[Config, Depends(get_config)]
):
    """
    Login user and get access token.

    Args:
        request: Login request
        user_repo: User repository
        config: Configuration

    Returns:
        Access token and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Authenticate user
        user = await user_repo.authenticate(request.email, request.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.id},
        config=config
    )

    logger.info(f"User logged in: {user.email}")

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user info
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Logout user (client should discard token).

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.email}")

    return {
        "message": "Successfully logged out"
    }
