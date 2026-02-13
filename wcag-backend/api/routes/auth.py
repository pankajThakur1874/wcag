"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status, Depends

from wcag_backend.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    AuthResponse,
    UserResponse,
    TokenOnlyResponse,
    LogoutResponse,
    UserOnlyResponse
)
from wcag_backend.database.repositories.user_repo import UserRepository
from wcag_backend.database.repositories.refresh_token_repo import RefreshTokenRepository
from wcag_backend.core.auth_service import AuthService
from wcag_backend.api.dependencies import (
    get_user_repository,
    get_refresh_token_repository,
    get_auth_service,
    CurrentUser
)
from wcag_backend.utils.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError
)
from wcag_backend.utils.security import hash_token


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.

    Creates a user account and returns access + refresh tokens.
    """
    try:
        # Create user
        user = await user_repo.create(
            name=request.name,
            email=request.email,
            password=request.password
        )

        # Generate token pair
        access_token, refresh_token, refresh_hash, expires_at = auth_service.create_token_pair(user.id)

        # Store refresh token
        await refresh_token_repo.create_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at
        )

        # Prepare response
        user_response = UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            createdAt=user.created_at
        )

        return AuthResponse.create(user_response, access_token, refresh_token)

    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": {
                    "code": "EMAIL_EXISTS",
                    "message": e.message
                }
            }
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return tokens.

    Validates email/password and returns access + refresh tokens.
    """
    try:
        # Authenticate user
        user = await user_repo.authenticate(request.email, request.password)

        # Generate token pair
        access_token, refresh_token, refresh_hash, expires_at = auth_service.create_token_pair(user.id)

        # Store refresh token
        await refresh_token_repo.create_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at
        )

        # Prepare response
        user_response = UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            createdAt=user.created_at
        )

        return AuthResponse.create(user_response, access_token, refresh_token)

    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": e.message
                }
            }
        )


@router.post("/refresh", response_model=TokenOnlyResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.

    Implements token rotation: generates new access + refresh tokens and revokes the old refresh token.
    """
    try:
        # Validate and get refresh token from database
        token_hash_value = hash_token(request.refreshToken)
        old_refresh_token = await refresh_token_repo.get_by_token_hash(token_hash_value)

        # Generate new token pair
        access_token, new_refresh_token, new_refresh_hash, expires_at = auth_service.create_token_pair(
            old_refresh_token.user_id
        )

        # Store new refresh token
        new_token = await refresh_token_repo.create_token(
            user_id=old_refresh_token.user_id,
            token_hash=new_refresh_hash,
            expires_at=expires_at
        )

        # Revoke old refresh token (token rotation)
        await refresh_token_repo.revoke_token(
            token_id=old_refresh_token.id,
            replaced_by=new_token.id
        )

        return TokenOnlyResponse(
            success=True,
            data={
                "accessToken": access_token,
                "refreshToken": new_refresh_token
            }
        )

    except (TokenExpiredError, TokenInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_EXPIRED" if isinstance(e, TokenExpiredError) else "TOKEN_INVALID",
                    "message": e.message
                }
            }
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: LogoutRequest,
    current_user: CurrentUser,
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository)
):
    """
    Logout user by revoking refresh token.

    Requires valid access token in Authorization header.
    """
    try:
        # Revoke refresh token
        token_hash_value = hash_token(request.refreshToken)
        refresh_token = await refresh_token_repo.get_by_token_hash(token_hash_value)
        await refresh_token_repo.revoke_token(refresh_token.id)

        return LogoutResponse()

    except (TokenExpiredError, TokenInvalidError):
        # Even if token is invalid, we still consider logout successful
        return LogoutResponse()


@router.get("/me", response_model=UserOnlyResponse)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user information.

    Requires valid access token in Authorization header.
    """
    user_response = UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        createdAt=current_user.created_at
    )

    return UserOnlyResponse(success=True, data=user_response)
