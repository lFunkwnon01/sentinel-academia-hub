"""Tenant configuration service.

Per-tenant settings: emails for notifications, threshold for triggering.
"""

from __future__ import annotations

import json
from typing import Any

import boto3

from handlers._shared.config import get_settings
from handlers._shared.errors import NotFoundError
from handlers._shared.logger import get_logger

log = get_logger(__name__)

_client_cache: dict[str, Any] = {}


def _get_s3_client():
    """Lazy singleton S3 client."""
    if "s3" not in _client_cache:
        _client_cache["s3"] = boto3.client("s3")
    return _client_cache["s3"]


DEFAULT_TENANT_CONFIG: dict[str, Any] = {
    "name": "Demo University",
    "emails": {
        "BIENESTAR": "bienestar@example.edu",
        "DIRECCION": "direccion@example.edu",
        "SEGURIDAD": "seguridad@example.edu",
        "DEFAULT": "sentinel@example.edu",
    },
    "threshold": 6,
    "notificaciones": {
        "ACOSO": True,
        "CRITICA": True,
        "ALTA": True,
        "MEDIA": False,
        "BAJA": False,
    },
}


def get_tenant_config(tenant_id: str) -> dict[str, Any]:
    """Get tenant configuration, with sensible defaults.

    For the demo, we use hardcoded tenant configs. In production, this
    would query a TenantConfig table in DynamoDB.
    """
    settings = get_settings()
    bucket = settings.files_bucket_resolved
    s3 = _get_s3_client()
    key = f"tenants/{tenant_id}/config.json"

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        config = json.loads(response["Body"].read().decode("utf-8"))
        log.info("Loaded tenant config from S3", extra={"tenant_id": tenant_id})
        return config
    except s3.exceptions.NoSuchKey:
        log.info("No config found, using defaults", extra={"tenant_id": tenant_id})
        return DEFAULT_TENANT_CONFIG
    except Exception as e:
        log.warning(
            "Error loading tenant config, using defaults",
            extra={"error": str(e), "tenant_id": tenant_id},
        )
        return DEFAULT_TENANT_CONFIG


def should_notify(tenant_id: str, analysis: dict[str, Any]) -> bool:
    """Decide if a queja should trigger notifications.

    Returns True if:
    - analysis.prioridad >= tenant threshold, OR
    - analysis.requiereNotificacionInmediata is True
    """
    config = get_tenant_config(tenant_id)
    threshold = config.get("threshold", 6)
    prioridad = analysis.get("prioridad", 0)
    inmediata = analysis.get("requiereNotificacionInmediata", False)

    return prioridad >= threshold or inmediata


def get_recipients(tenant_id: str, categoria: str) -> list[str]:
    """Get list of email recipients for a given category."""
    config = get_tenant_config(tenant_id)
    emails_config = config.get("emails", {})

    # Map categoria to recipient type
    if categoria in ("ACOSO", "SALUD"):
        # Sensitive categories: bienestar + seguridad
        recipients = [
            emails_config.get("BIENESTAR"),
            emails_config.get("SEGURIDAD"),
            emails_config.get("DEFAULT"),
        ]
    elif categoria in ("INFRAESTRUCTURA", "ADMINISTRATIVA"):
        recipients = [
            emails_config.get("DIRECCION"),
            emails_config.get("DEFAULT"),
        ]
    else:
        recipients = [emails_config.get("DEFAULT")]

    return [r for r in recipients if r]
