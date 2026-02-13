"""Custom exceptions for WCAG Backend V2."""

from typing import Optional, Any


class WCAGBackendException(Exception):
    """Base exception for WCAG Backend."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(WCAGBackendException):
    """Database-related exceptions."""
    pass


class DatabaseConnectionError(DatabaseException):
    """Failed to connect to database."""
    pass


class DocumentNotFoundError(DatabaseException):
    """Document not found in database."""

    def __init__(self, collection: str, document_id: str):
        super().__init__(
            f"Document not found in {collection}",
            {"collection": collection, "id": document_id}
        )


class ScannerException(WCAGBackendException):
    """Scanner-related exceptions."""
    pass


class ScannerTimeoutError(ScannerException):
    """Scanner operation timed out."""
    pass


class ScannerExecutionError(ScannerException):
    """Scanner execution failed."""
    pass


class QueueException(WCAGBackendException):
    """Queue-related exceptions."""
    pass


class QueueFullError(QueueException):
    """Queue is full."""
    pass


class JobTimeoutError(QueueException):
    """Job execution timed out."""
    pass


class WorkerException(WCAGBackendException):
    """Worker-related exceptions."""
    pass


class WorkerPoolFullError(WorkerException):
    """Worker pool is at capacity."""
    pass


class ConfigurationException(WCAGBackendException):
    """Configuration-related exceptions."""
    pass


class ConfigFileNotFoundError(ConfigurationException):
    """Configuration file not found."""
    pass


class InvalidConfigError(ConfigurationException):
    """Invalid configuration."""
    pass


class AuthenticationException(WCAGBackendException):
    """Authentication-related exceptions."""
    pass


class InvalidCredentialsError(AuthenticationException):
    """Invalid credentials provided."""
    pass


class TokenExpiredError(AuthenticationException):
    """Authentication token expired."""
    pass


class TokenInvalidError(AuthenticationException):
    """Authentication token is invalid."""
    pass


class UnauthorizedError(AuthenticationException):
    """Unauthorized access."""
    pass


class ForbiddenError(WCAGBackendException):
    """Forbidden access - user lacks permission."""
    pass


class ValidationException(WCAGBackendException):
    """Validation-related exceptions."""
    pass


class InvalidInputError(ValidationException):
    """Invalid input provided."""
    pass


class EmailAlreadyExistsError(ValidationException):
    """Email already exists in the system."""

    def __init__(self, email: str):
        super().__init__(
            f"A user with email '{email}' already exists.",
            {"email": email}
        )


class UserNotFoundException(DocumentNotFoundError):
    """User not found."""

    def __init__(self, user_id: str):
        super().__init__(collection="users", document_id=user_id)


class RefreshTokenNotFoundException(DocumentNotFoundError):
    """Refresh token not found."""

    def __init__(self, token_id: str):
        super().__init__(collection="refresh_tokens", document_id=token_id)


class ProjectNotFoundException(DocumentNotFoundError):
    """Project not found."""

    def __init__(self, project_id: str):
        super().__init__(collection="projects", document_id=project_id)


class ScanNotFoundException(DocumentNotFoundError):
    """Scan not found."""

    def __init__(self, scan_id: str):
        super().__init__(collection="scans", document_id=scan_id)


class IssueNotFoundException(DocumentNotFoundError):
    """Issue not found."""

    def __init__(self, issue_id: str):
        super().__init__(collection="issues", document_id=issue_id)


class RateLimitExceededError(WCAGBackendException):
    """Rate limit exceeded."""
    pass
