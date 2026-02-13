"""API middleware for error handling, CORS, and logging."""

import time
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from wcag_backend.utils.logger import get_logger
from wcag_backend.utils.exceptions import (
    WCAGBackendException,
    ValidationException,
    AuthenticationException,
    DatabaseException,
    QueueException,
    TokenExpiredError,
    TokenInvalidError,
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    ForbiddenError
)

logger = get_logger("middleware")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next):
        """
        Handle all requests and catch exceptions.

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response

        except ValidationException as e:
            logger.warning(f"Validation error: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": e.message
                    }
                }
            )

        except EmailAlreadyExistsError as e:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "success": False,
                    "error": {
                        "code": "EMAIL_EXISTS",
                        "message": e.message
                    }
                }
            )

        except InvalidCredentialsError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": e.message
                    }
                }
            )

        except TokenExpiredError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": e.message
                    }
                }
            )

        except TokenInvalidError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": e.message
                    }
                }
            )

        except ForbiddenError as e:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": e.message
                    }
                }
            )

        except QueueException as e:
            logger.error(f"Queue error: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "success": False,
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "System is currently busy. Please try again later."
                    }
                }
            )

        except DatabaseException as e:
            logger.error(f"Database error: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "DATABASE_ERROR",
                        "message": "A database error occurred. Please try again."
                    }
                }
            )

        except WCAGBackendException as e:
            logger.error(f"Application error: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": e.message
                    }
                }
            )

        except Exception as e:
            logger.error(f"Unexpected error: {e}", extra={
                "traceback": traceback.format_exc()
            })
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred. Please try again."
                    }
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests (only for errors and slow requests)."""

    async def dispatch(self, request: Request, call_next):
        """
        Log request details for errors and slow requests only.

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Only log errors or slow requests (>2 seconds)
        if response.status_code >= 400 or duration_ms > 2000:
            logger.warning(
                f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )

        return response


def setup_middleware(app):
    """
    Setup all middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Will be configured from config
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)

    logger.info("Middleware configured")
