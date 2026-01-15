"""Pydantic schemas for user API requests and responses."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

from scanner_v2.database.models import UserRole


class UserCreateRequest(BaseModel):
    """Request to create a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserUpdateRequest(BaseModel):
    """Request to update a user."""

    name: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    """User response schema (without password)."""

    id: str = Field(..., alias="_id")
    email: str
    name: Optional[str]
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with token."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
