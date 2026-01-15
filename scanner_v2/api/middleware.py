"""FastAPI middleware for logging, error handling, and CORS."""

import time
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from scanner_v2.utils.logger import get_logger
from scanner_v2.utils.exceptions import (
    WCAGScannerException,
    DatabaseException,
    ValidationException,
)

logger = get_logger("api.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            f"Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )

        # Add custom headers
        response.headers["X-Process-Time"] = str(round(duration_ms, 2))

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with error handling.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response or error response
        """
        try:
            return await call_next(request)
        except ValidationException as e:
            logger.warning(
                f"Validation error: {e.message}",
                extra={"details": e.details}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Validation Error",
                    "message": e.message,
                    "details": e.details,
                }
            )
        except DatabaseException as e:
            logger.error(
                f"Database error: {e.message}",
                extra={"details": e.details}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Database Error",
                    "message": "A database error occurred",
                    "details": e.details if e.details else {},
                }
            )
        except WCAGScannerException as e:
            logger.error(
                f"Scanner error: {e.message}",
                extra={"details": e.details}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": e.__class__.__name__,
                    "message": e.message,
                    "details": e.details,
                }
            )
        except Exception as e:
            # Log unexpected errors with traceback
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "traceback": traceback.format_exc(),
                    "path": request.url.path,
                    "method": request.method,
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                }
            )


def setup_cors(app) -> None:
    """
    Setup CORS middleware.

    Args:
        app: FastAPI application
    """
    from scanner_v2.utils.config import get_config

    config = get_config()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info(
        f"CORS configured with origins: {config.security.cors_origins}"
    )


def setup_middleware(app) -> None:
    """
    Setup all middleware.

    Args:
        app: FastAPI application
    """
    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Setup CORS
    setup_cors(app)

    logger.info("Middleware configured")
