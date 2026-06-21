"""GET /api/quejas - List all complaints for a tenant.

Supports pagination via ?limit=N&cursor=TOKEN and filtering by categoria, criticidad, status.
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

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

VALID_CATEGORIAS = {"ACADEMICA", "INFRAESTRUCTURA", "ACOSO", "ADMINISTRATIVA", "SALUD", "OTRA"}
VALID_CRITICIDADES = {"BAJA", "MEDIA", "ALTA", "CRITICA"}
VALID_STATUS = {"PENDIENTE", "EN_COLA", "PROCESANDO", "ANALIZADA", "NOTIFICADA", "ERROR"}


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """GET /api/quejas?limit=50&cursor=xxx&categoria=ACOSO&criticidad=ALTA&status=ANALIZADA"""
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

    categoria = query.get("categoria")
    criticidad = query.get("criticidad")
    status_filter = query.get("status")
    if categoria and categoria not in VALID_CATEGORIAS:
        raise ValidationError(message="Invalid categoria", details={"categoria": categoria})
    if criticidad and criticidad not in VALID_CRITICIDADES:
        raise ValidationError(message="Invalid criticidad", details={"criticidad": criticidad})
    if status_filter and status_filter not in VALID_STATUS:
        raise ValidationError(message="Invalid status", details={"status": status_filter})

    log.info("Listing quejas", extra={"limit": limit, "categoria": categoria, "criticidad": criticidad, "status": status_filter})

    dynamo = get_dynamo_client()
    raw_items = dynamo.query_by_tenant(
        tenant_id=tenant_id,
        sk_prefix="QUEJA#",
        limit=limit,
        scan_index_forward=False,  # newest first
    )

    def _to_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def to_list_item(item: dict[str, Any]) -> dict[str, Any]:
        analysis = item.get("analysis") or {}
        return {
            "quejaId": item.get("quejaId") or item.get("sk", "").split("#")[-1],
            "titulo": item.get("titulo", ""),
            "categoria": analysis.get("categoria") or item.get("categoriaDeclarada"),
            "criticidad": analysis.get("criticidad"),
            "status": item.get("status"),
            "createdAt": item.get("createdAt"),
            "prioridad": _to_int(analysis.get("prioridad")),
            "sede": item.get("sede"),
            "facultad": item.get("facultad"),
            "anonima": item.get("anonima"),
        }

    list_items = [to_list_item(it) for it in raw_items]

    def matches(item: dict[str, Any]) -> bool:
        if categoria and item.get("categoria") != categoria:
            return False
        if criticidad and item.get("criticidad") != criticidad:
            return False
        if status_filter and item.get("status") != status_filter:
            return False
        return True

    filtered = [it for it in list_items if matches(it)]

    return HttpResponse.ok(
        {
            "items": filtered,
            "total": len(filtered),
            "nextCursor": None,
        }
    )
