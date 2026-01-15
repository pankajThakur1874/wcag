"""Custom exceptions for WCAG Scanner V2."""

from typing import Optional, Any


class WCAGScannerException(Exception):
    """Base exception for WCAG Scanner."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(WCAGScannerException):
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


class ScannerException(WCAGScannerException):
    """Scanner-related exceptions."""
    pass


class ScannerTimeoutError(ScannerException):
    """Scanner operation timed out."""
    pass


class ScannerExecutionError(ScannerException):
    """Scanner execution failed."""
    pass


class CrawlerException(WCAGScannerException):
    """Crawler-related exceptions."""
    pass


class CrawlLimitExceededError(CrawlerException):
    """Crawl limit exceeded."""
    pass


class InvalidURLError(CrawlerException):
    """Invalid URL provided."""
    pass


class QueueException(WCAGScannerException):
    """Queue-related exceptions."""
    pass


class QueueFullError(QueueException):
    """Queue is full."""
    pass


class JobTimeoutError(QueueException):
    """Job execution timed out."""
    pass


class WorkerException(WCAGScannerException):
    """Worker-related exceptions."""
    pass


class WorkerPoolFullError(WorkerException):
    """Worker pool is at capacity."""
    pass


class ConfigurationException(WCAGScannerException):
    """Configuration-related exceptions."""
    pass


class ConfigFileNotFoundError(ConfigurationException):
    """Configuration file not found."""
    pass


class InvalidConfigError(ConfigurationException):
    """Invalid configuration."""
    pass


class AuthenticationException(WCAGScannerException):
    """Authentication-related exceptions."""
    pass


class InvalidCredentialsError(AuthenticationException):
    """Invalid credentials provided."""
    pass


class TokenExpiredError(AuthenticationException):
    """Authentication token expired."""
    pass


class UnauthorizedError(AuthenticationException):
    """Unauthorized access."""
    pass


class ValidationException(WCAGScannerException):
    """Validation-related exceptions."""
    pass


class InvalidInputError(ValidationException):
    """Invalid input provided."""
    pass


class ScanNotFoundException(DocumentNotFoundError):
    """Scan not found."""

    def __init__(self, scan_id: str):
        super().__init__(collection="scans", document_id=scan_id)


class ProjectNotFoundException(DocumentNotFoundError):
    """Project not found."""

    def __init__(self, project_id: str):
        super().__init__(collection="projects", document_id=project_id)


class PageNotFoundException(DocumentNotFoundError):
    """Page not found."""

    def __init__(self, page_id: str):
        super().__init__(collection="scanned_pages", document_id=page_id)


class IssueNotFoundException(DocumentNotFoundError):
    """Issue not found."""

    def __init__(self, issue_id: str):
        super().__init__(collection="issues", document_id=issue_id)
