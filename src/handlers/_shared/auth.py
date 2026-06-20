"""Auth helpers - extract tenant_id and user_id from API Gateway event.

For Fase 1 we use simple header-based auth:
- X-Tenant-ID: the tenant identifier (multi-tenant key)
- X-User-ID: optional user identifier (for non-anonymous quejas)

In Fase 5 we'll add JWT validation.
"""

from __future__ import annotations

from typing import Any

from handlers._shared.errors import UnauthorizedError


def extract_tenant_id(event: dict[str, Any]) -> str:
    """Extract tenant ID from request headers.

    Looks for:
    - X-Tenant-ID header (case-insensitive)
    - tenantId in requestContext.authorizer.claims (JWT mode, future)

    Raises:
        UnauthorizedError: if tenant_id is missing
    """
    headers = event.get("headers", {}) or {}

    # Try direct header (case-insensitive)
    tenant_id = (
        headers.get("X-Tenant-ID")
        or headers.get("x-tenant-id")
        or headers.get("X-Tenant-Id")
    )

    if not tenant_id:
        # Future: try JWT claims
        # authorizer = event.get("requestContext", {}).get("authorizer", {})
        # claims = authorizer.get("claims", {})
        # tenant_id = claims.get("custom:tenant_id")
        raise UnauthorizedError(
            message="Missing X-Tenant-ID header. Multi-tenant access requires a tenant identifier."
        )

    # Sanitize: alphanumeric + hyphens only
    tenant_id = tenant_id.strip()
    if not tenant_id or not all(c.isalnum() or c in "-_" for c in tenant_id):
        raise UnauthorizedError(message="Invalid X-Tenant-ID format")

    return tenant_id


def extract_user_id(event: dict[str, Any]) -> str | None:
    """Extract user ID (optional - anonymous complaints don't have one)."""
    headers = event.get("headers", {}) or {}
    user_id = (
        headers.get("X-User-ID")
        or headers.get("x-user-id")
        or headers.get("X-User-Id")
    )
    return user_id.strip() if user_id else None
