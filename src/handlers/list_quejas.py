"""GET /api/quejas - List all complaints for a tenant.

Supports pagination via ?limit=N&cursor=TOKEN.
Returns most recent first.

Aligned with api-mock/openapi.yaml.
"""

from __future__ import annotations

from typing import Any

from handlers._shared.auth import extract_tenant_id
from handlers._shared.correlation_id import with_correlation_id
from handlers._shared.dynamo_client import get_dynamo_client
from handlers._shared.errors import error_handler, ValidationError
from handlers._shared.http_response import HttpResponse
from handlers._shared.logger import get_logger

log = get_logger(__name__)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """GET /api/quejas?limit=20&cursor=xxx"""
    with_correlation_id(event)
    tenant_id = extract_tenant_id(event)
    log.append_keys(tenant_id=tenant_id)

    query = event.get("queryStringParameters") or {}
    try:
        limit = int(query.get("limit", DEFAULT_LIMIT))
    except (TypeError, ValueError) as e:
        raise ValidationError(
            message="Invalid limit parameter",
            details={"limit": str(query.get("limit"))},
        ) from e

    if limit < 1 or limit > MAX_LIMIT:
        raise ValidationError(
            message=f"Limit must be between 1 and {MAX_LIMIT}",
            details={"limit": limit},
        )

    log.info("Listing quejas", extra={"limit": limit})

    dynamo = get_dynamo_client()
    items = dynamo.query_by_tenant(
        tenant_id=tenant_id,
        sk_prefix="QUEJA#",
        limit=limit,
        scan_index_forward=False,  # newest first
    )

    # Return per OpenAPI spec: items + total + nextCursor
    return HttpResponse.ok(
        {
            "items": items,
            "total": len(items),
            "nextCursor": None,  # TODO: implement pagination in Fase 4
        }
    )
