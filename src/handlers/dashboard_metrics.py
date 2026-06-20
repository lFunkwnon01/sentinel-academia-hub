"""GET /api/dashboard/metrics - Dashboard metrics for authorities.

Returns aggregated statistics about quejas for the tenant.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from boto3.dynamodb.conditions import Attr

from handlers._shared.auth import extract_tenant_id
from handlers._shared.correlation_id import (
    clear_correlation_id,
    with_correlation_id,
)
from handlers._shared.dynamo_client import get_dynamo_client
from handlers._shared.errors import error_handler
from handlers._shared.http_response import HttpResponse
from handlers._shared.logger import get_logger

log = get_logger(__name__)


def _aggregate_metrics(items: list[dict[str, Any]], rango: int) -> dict[str, Any]:
    """Aggregate queja metrics from DDB items."""
    total = len(items)
    crit_counter: Counter[str] = Counter()
    cat_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    sede_counter: Counter[str] = Counter()
    facultad_counter: Counter[str] = Counter()
    prioridad_sum = 0
    prioridad_count = 0
    requiere_notif = 0
    tiempo_resolucion_horas: list[float] = []

    for item in items:
        if item.get("status"):
            status_counter[item["status"]] += 1
        # Sede / Facultad (top groups)
        if item.get("sede"):
            sede_counter[item["sede"]] += 1
        if item.get("facultad"):
            facultad_counter[item["facultad"]] += 1
        # Get analysis fields if present
        analysis = item.get("analysis", {})
        if isinstance(analysis, dict):
            if analysis.get("criticidad"):
                crit_counter[analysis["criticidad"]] += 1
            if analysis.get("categoria"):
                cat_counter[analysis["categoria"]] += 1
            if analysis.get("prioridad"):
                prioridad_sum += analysis["prioridad"]
                prioridad_count += 1
            if analysis.get("requiereNotificacionInmediata"):
                requiere_notif += 1
        # Time to resolution: createdAt -> updatedAt for ANALIZADA/ERROR status
        if item.get("status") in ("ANALIZADA", "RESUELTA") and item.get("createdAt") and item.get("updatedAt"):
            try:
                from datetime import datetime
                t_create = datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00"))
                t_update = datetime.fromisoformat(item["updatedAt"].replace("Z", "+00:00"))
                delta_h = (t_update - t_create).total_seconds() / 3600
                tiempo_resolucion_horas.append(delta_h)
            except (ValueError, TypeError):
                pass

    return {
        "resumen": {
            "totalQuejas": total,
            "quejasCriticas": crit_counter.get("CRITICA", 0),
            "quejasAltas": crit_counter.get("ALTA", 0),
            "quejasMedias": crit_counter.get("MEDIA", 0),
            "quejasBajas": crit_counter.get("BAJA", 0),
            "quejasPendientes": status_counter.get("PENDIENTE", 0),
            "quejasAnalizadas": status_counter.get("ANALIZADA", 0),
            "quejasRequierenNotificacion": requiere_notif,
            "prioridadPromedio": (
                round(prioridad_sum / prioridad_count, 1)
                if prioridad_count > 0
                else 0
            ),
            "tiempoPromedioResolucion": (
                round(sum(tiempo_resolucion_horas) / len(tiempo_resolucion_horas), 1)
                if tiempo_resolucion_horas
                else 0
            ),
        },
        "distribucionPorCategoria": dict(cat_counter),
        "distribucionPorCriticidad": dict(crit_counter),
        "distribucionPorStatus": dict(status_counter),
        "topSedes": [
            {"sede": s, "count": c} for s, c in sede_counter.most_common(5)
        ],
        "topFacultades": [
            {"facultad": f, "count": c} for f, c in facultad_counter.most_common(5)
        ],
        "rangoDias": rango,
    }


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """GET /api/dashboard/metrics?rango=30"""
    with_correlation_id(event)
    try:
        tenant_id = extract_tenant_id(event)
        log.append_keys(tenant_id=tenant_id)

        # Parse rango param (default 30)
        query = event.get("queryStringParameters") or {}
        try:
            rango = int(query.get("rango", 30))
        except (TypeError, ValueError):
            rango = 30
        if rango not in (7, 30, 90):
            rango = 30

        # Query all quejas for this tenant
        dynamo = get_dynamo_client()
        items = dynamo._table.scan(
            FilterExpression=Attr("pk").begins_with(f"TENANT#{tenant_id}#QUEJA#")
        ).get("Items", [])

        metrics = _aggregate_metrics(items, rango)
        log.info("Dashboard metrics computed", extra={"total": metrics["resumen"]["totalQuejas"]})

        return HttpResponse.ok(metrics)
    finally:
        clear_correlation_id()
