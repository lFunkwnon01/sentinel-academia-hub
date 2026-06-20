"""Standardized HTTP responses with CORS handling.

All Lambda responses go through this module to ensure:
- CORS headers are always set
- Body is JSON-encoded with orjson (fast)
- Error responses include correlation_id
- Content-Type is always application/json
"""

from __future__ import annotations

from typing import Any

import orjson

from handlers._shared.config import get_settings
from handlers._shared.correlation_id import get_correlation_id

DEFAULT_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


class HttpResponse:
    """Helper to build API Gateway HTTP responses (REST API v1 or HTTP API v2)."""

    @staticmethod
    def ok(body: Any, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """200 OK with JSON body."""
        return build_response(200, body, headers)

    @staticmethod
    def created(body: Any, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """201 Created."""
        return build_response(201, body, headers)

    @staticmethod
    def accepted(body: Any, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """202 Accepted (async pattern per OpenAPI spec)."""
        return build_response(202, body, headers)

    @staticmethod
    def no_content(headers: dict[str, str] | None = None) -> dict[str, Any]:
        """204 No Content."""
        return build_response(204, None, headers)

    @staticmethod
    def bad_request(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """400 Bad Request."""
        return build_error_response(400, "VALIDATION_ERROR", message, details)

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> dict[str, Any]:
        """401 Unauthorized."""
        return build_error_response(401, "UNAUTHORIZED", message)

    @staticmethod
    def forbidden(message: str = "Forbidden") -> dict[str, Any]:
        """403 Forbidden."""
        return build_error_response(403, "FORBIDDEN", message)

    @staticmethod
    def not_found(message: str = "Not found") -> dict[str, Any]:
        """404 Not Found."""
        return build_error_response(404, "NOT_FOUND", message)

    @staticmethod
    def conflict(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """409 Conflict."""
        return build_error_response(409, "CONFLICT", message, details)

    @staticmethod
    def internal_error(message: str = "Internal server error") -> dict[str, Any]:
        """500 Internal Server Error."""
        return build_error_response(500, "INTERNAL_ERROR", message)


def _cors_headers() -> dict[str, str]:
    """Build CORS headers based on settings."""
    settings = get_settings()
    origins = settings.allowed_origins_list
    return {
        "Access-Control-Allow-Origin": ", ".join(origins),
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Correlation-ID,X-Tenant-ID",
        "Access-Control-Max-Age": "86400",
    }


def _serialize(obj: Any) -> str:
    """Serialize to JSON using orjson (faster than stdlib)."""
    return orjson.dumps(obj, default=str).decode("utf-8")


def build_response(
    status_code: int,
    body: Any,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a standard API Gateway response.

    Args:
        status_code: HTTP status code
        body: Any JSON-serializable object (None for 204)
        headers: Additional headers to merge
    """
    final_headers = {**DEFAULT_HEADERS, **_cors_headers()}
    if headers:
        final_headers.update(headers)

    # Add correlation_id to response
    correlation_id = get_correlation_id()
    if correlation_id:
        final_headers["X-Correlation-ID"] = correlation_id

    return {
        "statusCode": status_code,
        "headers": final_headers,
        "body": _serialize(body) if body is not None else "",
    }


def build_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardized error response aligned with OpenAPI spec.

    Per spec: { code, message, correlationId, timestamp, details? }
    """
    from datetime import datetime, timezone

    body: dict[str, Any] = {
        "code": error_code,
        "message": message,
        "correlationId": get_correlation_id() or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        body["details"] = details

    return build_response(status_code, body)
