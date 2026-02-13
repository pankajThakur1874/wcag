"""Common schemas used across the application."""

from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field


# Generic type for pagination
T = TypeVar('T')


class PaginationMetadata(BaseModel):
    """Pagination metadata."""

    page: int
    limit: int
    totalPages: int = Field(..., alias="totalPages")
    totalItems: int = Field(..., alias="totalItems")

    model_config = {"populate_by_name": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    success: bool = True
    data: List[T]
    pagination: PaginationMetadata


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: ErrorDetail
