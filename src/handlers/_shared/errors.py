"""Custom exceptions and error handler for Lambda.

All errors caught here return a standardized JSON error response with:
- error_code: machine-readable code
- message: human-readable message
- correlation_id: for tracing
- details: optional context (validation errors, etc.)
"""

from __future__ import annotations

from typing import Any

from handlers._shared.correlation_id import get_correlation_id
from handlers._shared.http_response import build_error_response
from handlers._shared.logger import get_logger

log = get_logger(__name__)


class AppError(Exception):
    """Base application error.

    All custom errors should inherit from this. Catch this in handlers
    to convert to a proper HTTP response.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ValidationError(AppError):
    """400 Bad Request - input validation failed."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class UnauthorizedError(AppError):
    """401 Unauthorized - missing or invalid auth."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED")


class ForbiddenError(AppError):
    """403 Forbidden - authenticated but not allowed."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN")


class NotFoundError(AppError):
    """404 Not Found - resource doesn't exist."""

    def __init__(self, message: str = "Not found", details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class ConflictError(AppError):
    """409 Conflict - resource already exists or state mismatch."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


def error_handler(func):  # type: ignore[no-untyped-def]
    """Decorator to convert exceptions to standardized HTTP responses.

    Usage:
        @error_handler
        def lambda_handler(event, context):
            ...

    Order of error handling:
    1. AppError subclasses -> use their status_code and error_code
    2. Pydantic ValidationError -> 400 VALIDATION_ERROR
    3. Generic Exception -> 500 INTERNAL_ERROR (logged with traceback)
    """

    def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        try:
            return func(event, context)  # type: ignore[no-any-return]
        except AppError as e:
            # Known business error - log as warning, not error
            log.warning(
                "AppError raised",
                extra={
                    "error_code": e.error_code,
                    "status_code": e.status_code,
                    "error_message": e.message,  # not 'message' (reserved by stdlib logging)
                },
            )
            return build_error_response(
                status_code=e.status_code,
                error_code=e.error_code,
                message=e.message,
                details=e.details,
            )
        except Exception as e:  # noqa: BLE001 - catch-all for safety
            # Unknown error - log with full traceback
            log.exception("Unhandled exception in Lambda")
            return build_error_response(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                details={"exception_type": type(e).__name__},
            )

    wrapper.__name__ = func.__name__
    return wrapper
