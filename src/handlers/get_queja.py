"""GET /api/quejas/{quejaId} - Retrieve a single complaint by ID.

Multi-tenant: only returns the queja if it belongs to the tenant in X-Tenant-ID.
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
from handlers._shared.schemas import QuejaResponse

log = get_logger(__name__)


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """GET /api/quejas/{quejaId}"""
    with_correlation_id(event)
    tenant_id = extract_tenant_id(event)
    log.append_keys(tenant_id=tenant_id)

    path_params = event.get("pathParameters") or {}
    queja_id = path_params.get("quejaId") or path_params.get("id")
    if not queja_id:
        raise ValidationError(message="Missing quejaId in path")

    log.info("Fetching queja", extra={"queja_id": queja_id})

    dynamo = get_dynamo_client()
    item = dynamo.get_queja(tenant_id=tenant_id, queja_id=queja_id)

    response = QuejaResponse.from_dynamo(item)
    return HttpResponse.ok(response.model_dump(mode="json", exclude={"pk", "sk"}))
