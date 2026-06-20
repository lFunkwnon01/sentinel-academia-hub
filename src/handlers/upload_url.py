"""POST /api/quejas/{quejaId}/upload-url - Request presigned upload URL.

Flow:
1. Client creates a queja (POST /api/quejas)
2. Client wants to attach evidence
3. Client calls POST /api/quejas/{id}/upload-url with {filename, contentType}
4. API returns presigned URL
5. Client uploads file directly to S3
6. S3 event triggers file_processor Lambda
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from handlers._shared.auth import extract_tenant_id
from handlers._shared.correlation_id import with_correlation_id
from handlers._shared.dynamo_client import get_dynamo_client
from handlers._shared.errors import error_handler, NotFoundError, ValidationError
from handlers._shared.http_response import HttpResponse
from handlers._shared.logger import get_logger
from services.file_service import generate_presigned_upload_url

log = get_logger(__name__)


class UploadURLRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    contentType: str = Field(min_length=1, max_length=100)
    fileSize: int | None = Field(default=None, ge=0, le=10_485_760)  # max 10MB


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


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """POST /api/quejas/{quejaId}/upload-url"""
    with_correlation_id(event)
    tenant_id = extract_tenant_id(event)
    log.append_keys(tenant_id=tenant_id)

    # Extract quejaId from path
    path_params = event.get("pathParameters") or {}
    queja_id = path_params.get("quejaId") or path_params.get("id")
    if not queja_id:
        raise ValidationError(message="Missing quejaId in path")

    log.append_keys(queja_id=queja_id)

    # Verify the queja exists and belongs to the tenant
    dynamo = get_dynamo_client()
    try:
        dynamo.get_queja(tenant_id=tenant_id, queja_id=queja_id)
    except NotFoundError as e:
        log.warning("Queja not found for upload-url")
        raise

    # Parse and validate the body
    body = _parse_body(event)
    try:
        req = UploadURLRequest.model_validate(body)
    except Exception as e:
        raise ValidationError(
            message="Invalid request body",
            details={"errors": str(e)},
        ) from e

    # Generate presigned URL
    result = generate_presigned_upload_url(
        queja_id=queja_id,
        tenant_id=tenant_id,
        filename=req.filename,
        content_type=req.contentType,
        file_size=req.fileSize,
    )

    log.info(
        "Presigned URL generated",
        extra={"file_name": req.filename, "expires_in": result["expiresIn"]},
    )

    return HttpResponse.ok(result)
