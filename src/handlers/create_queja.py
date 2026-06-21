"""POST /api/quejas - Create a new complaint.

Async pattern: returns 202 Accepted immediately.
Sends message to SQS for background LLM analysis.

Aligned with api-mock/openapi.yaml.
"""

from __future__ import annotations

import json
import os
from typing import Any

import boto3
from pydantic import ValidationError as PydanticValidationError

from handlers._shared.auth import extract_tenant_id, extract_user_id
from handlers._shared.config import get_settings
from handlers._shared.correlation_id import (
    clear_correlation_id,
    get_correlation_id,
    with_correlation_id,
)
from handlers._shared.dynamo_client import (
    get_dynamo_client,
    now_iso,
    queja_pk,
    queja_sk,
)
from handlers._shared.errors import error_handler, ValidationError
from handlers._shared.http_response import HttpResponse
from handlers._shared.logger import get_logger
from handlers._shared.schemas import QuejaAccepted, QuejaCreate

log = get_logger(__name__)


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        raise ValueError("Missing request body")
    if event.get("isBase64Encoded"):
        import base64

        body = base64.b64decode(body).decode("utf-8")
    if isinstance(body, str):
        return json.loads(body)
    return body


def _send_to_sqs(queja_id: str, tenant_id: str, correlation_id: str) -> None:
    """Send message to SQS for background analysis."""
    settings = get_settings()
    queue_url = settings.analysis_queue_url
    if not queue_url:
        log.warning("ANALYSIS_QUEUE_URL not configured, skipping SQS send")
        return

    sqs = boto3.client("sqs")
    message_body = json.dumps(
        {
            "quejaId": queja_id,
            "tenantId": tenant_id,
            "correlationId": correlation_id,
        }
    )
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=message_body,
        MessageAttributes={
            "tenantId": {"StringValue": tenant_id, "DataType": "String"},
        },
    )
    log.info("Message sent to SQS", extra={"queue": queue_url.split("/")[-1]})


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    with_correlation_id(event)
    try:
        # 1. Auth
        tenant_id = extract_tenant_id(event)
        user_id = extract_user_id(event)
        log.append_keys(tenant_id=tenant_id)
        if user_id:
            log.append_keys(user_id=user_id)

        log.info("Creating new queja")

        # 2. Parse + validate
        body = _parse_body(event)
        try:
            input_data = QuejaCreate.model_validate(body)
        except PydanticValidationError as e:
            errors = [
                {
                    "field": ".".join(str(p) for p in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"],
                }
                for err in e.errors()
            ]
            raise ValidationError(
                message="Request body validation failed",
                details={"errors": errors},
            ) from e

        # 2b. Category-specific business rules
        # - ACADEMICA requires cursoCodigo
        # - ACOSO/ADMINISTRATIVA/SALUD require contactoEmail
        #   (cannot be anonymous, because 1 single queja is enough to act on)
        # - INFRAESTRUCTURA and OTRA may be anonymous
        cat = input_data.categoriaDeclarada.value
        business_errors: list[dict[str, str]] = []
        if cat == "ACADEMICA" and not input_data.cursoCodigo:
            business_errors.append({
                "field": "cursoCodigo",
                "message": "El código del curso es obligatorio para quejas ACADÉMICA",
            })
        if cat in ("ACADEMICA", "ACOSO", "ADMINISTRATIVA", "SALUD"):
            if input_data.anonima:
                business_errors.append({
                    "field": "anonima",
                    "message": (
                        f"Las quejas de tipo {cat} no pueden ser anónimas "
                        "porque se procesan individualmente"
                    ),
                })
            if not input_data.contactoEmail:
                business_errors.append({
                    "field": "contactoEmail",
                    "message": (
                        f"El email de contacto es obligatorio para quejas de tipo {cat} "
                        "para poder enviarte seguimiento"
                    ),
                })
        if business_errors:
            raise ValidationError(
                message="Business rule violation",
                details={"errors": business_errors},
            )

        # 3. Build accepted response
        now = now_iso()
        correlation_id = get_correlation_id() or ""
        accepted = QuejaAccepted(
            status="PENDIENTE",
            correlationId=correlation_id,
            createdAt=now,
            estimatedAnalysisTime=30,
        )

        # 4. Build DynamoDB item
        item = input_data.model_dump(mode="json")
        item["quejaId"] = accepted.quejaId
        item["tenantId"] = tenant_id
        item["userId"] = user_id if not input_data.anonima else None
        item["status"] = "PENDIENTE"
        item["createdAt"] = now
        item["updatedAt"] = now
        item["escalada"] = False
        item["pk"] = queja_pk(tenant_id, accepted.quejaId)
        item["sk"] = queja_sk(accepted.quejaId)
        item["gsi1pk"] = f"TENANT#{tenant_id}#STATUS#PENDIENTE"
        item["gsi1sk"] = now

        # 5. Persist
        dynamo = get_dynamo_client()
        dynamo.put_item(
            item=item,
            condition_expression="attribute_not_exists(pk)",
        )

        # 6. Send to SQS for async LLM analysis
        try:
            _send_to_sqs(accepted.quejaId, tenant_id, correlation_id)
        except Exception as e:
            # Log but don't fail the request - the queja is persisted
            log.error(
                "Failed to send SQS message (queja is still saved)",
                extra={"error": str(e)},
            )

        log.info(
            "Queja accepted",
            extra={"queja_id": accepted.quejaId, "status": "PENDIENTE"},
        )

        return HttpResponse.accepted(accepted.model_dump(mode="json"))
    finally:
        clear_correlation_id()
