"""GET /health - Health check endpoint.

No auth, no DynamoDB - just confirms the API is alive.
Used by load balancers, monitoring, and smoke tests post-deploy.
"""

from __future__ import annotations

from typing import Any

from handlers._shared.config import get_settings
from handlers._shared.correlation_id import with_correlation_id
from handlers._shared.errors import error_handler
from handlers._shared.http_response import HttpResponse

log = None  # Lazy import to avoid cold-start overhead


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Health check - returns 200 with service info."""
    with_correlation_id(event)
    settings = get_settings()
    return HttpResponse.ok(
        {
            "status": "healthy",
            "service": settings.app_name,
            "stage": settings.stage,
            "region": settings.region,
        }
    )
