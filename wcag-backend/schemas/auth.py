"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# Request Schemas

class RegisterRequest(BaseModel):
    """User registration request."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""

    refreshToken: str = Field(..., alias="refreshToken")


class LogoutRequest(BaseModel):
    """Logout request."""

    refreshToken: str = Field(..., alias="refreshToken")


# Response Schemas

class UserResponse(BaseModel):
    """User data response."""

    id: str
    name: str
    email: str
    createdAt: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class TokenResponse(BaseModel):
    """Token pair response."""

    accessToken: str = Field(..., alias="accessToken")
    refreshToken: str = Field(..., alias="refreshToken")

    model_config = {"populate_by_name": True}


class AuthResponse(BaseModel):
    """Authentication response with user and tokens."""

    success: bool = True
    data: dict

    @classmethod
    def create(cls, user: UserResponse, access_token: str, refresh_token: str):
        """Create auth response with user and tokens."""
        return cls(
            success=True,
            data={
                "user": user.model_dump(by_alias=True),
                "accessToken": access_token,
                "refreshToken": refresh_token
            }
        )


class UserOnlyResponse(BaseModel):
    """User-only response (for /auth/me)."""

    success: bool = True
    data: UserResponse


class TokenOnlyResponse(BaseModel):
    """Token-only response (for refresh)."""

    success: bool = True
    data: TokenResponse


class LogoutResponse(BaseModel):
    """Logout response."""

    success: bool = True
    message: str = "Logged out successfully. Refresh token revoked."
