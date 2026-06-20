"""Correlation ID middleware.

Reads X-Correlation-ID from request headers (or generates one).
Propagates to:
- Logger context
- Response headers
- Downstream services (HTTP, boto3, OCI)
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any

# ContextVar to track correlation_id per request (Lambda execution context)
_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Get the current correlation ID (set by with_correlation_id)."""
    return _correlation_id_var.get()


def with_correlation_id(event: dict[str, Any]) -> str:
    """Extract or generate a correlation ID from an API Gateway event.

    Looks for:
    - HTTP API v2: event["headers"]["x-correlation-id"]
    - REST API v1: event["headers"]["X-Correlation-ID"]
    - Generates UUID4 if not present

    Sets it in the ContextVar so logger and responses pick it up.

    Returns:
        The correlation ID (always non-None)
    """
    headers = event.get("headers", {}) or {}
    # Headers are case-insensitive in API Gateway; normalize
    correlation_id = (
        headers.get("x-correlation-id")
        or headers.get("X-Correlation-ID")
        or headers.get("X-Correlation-Id")
    )

    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    _correlation_id_var.set(correlation_id)
    return correlation_id


def clear_correlation_id() -> None:
    """Clear the correlation ID (call at end of Lambda execution)."""
    _correlation_id_var.set(None)
