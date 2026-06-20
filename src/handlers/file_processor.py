"""S3 event consumer: file_processor.

Triggered when a file is uploaded to the S3 bucket.
Updates the queja in DynamoDB with the file URL.
"""

from __future__ import annotations

import re
from typing import Any

from handlers._shared.config import get_settings
from handlers._shared.correlation_id import clear_correlation_id, with_correlation_id
from handlers._shared.dynamo_client import (
    get_dynamo_client,
    now_iso,
    queja_pk,
    queja_sk,
)
from handlers._shared.errors import error_handler
from handlers._shared.http_response import HttpResponse  # for compatibility
from handlers._shared.logger import get_logger
from services.file_service import build_s3_url

log = get_logger(__name__)


def _parse_key(s3_key: str) -> tuple[str, str] | None:
    """Extract tenant_id and queja_id from S3 key.

    Pattern: tenants/{tenantId}/quejas/{quejaId}/{fileId}-{filename}
    """
    match = re.match(r"^tenants/([^/]+)/quejas/([^/]+)/", s3_key)
    if not match:
        return None
    return match.group(1), match.group(2)


def _process_record(record: dict[str, Any]) -> None:
    """Process a single S3 event record."""
    bucket = record["s3"]["bucket"]["name"]
    s3_key = record["s3"]["object"]["key"]

    parsed = _parse_key(s3_key)
    if not parsed:
        log.warning("Could not parse S3 key, skipping", extra={"key": s3_key})
        return
    tenant_id, queja_id = parsed
    log.append_keys(tenant_id=tenant_id, queja_id=queja_id)

    # Build the public URL
    file_url = build_s3_url(bucket, s3_key, region=get_settings().region)
    log.info(f"File uploaded: {s3_key} -> {file_url}")

    # Update the queja with this file URL (append to adjuntos if not already there)
    dynamo = get_dynamo_client()
    try:
        item = dynamo.get_queja(tenant_id=tenant_id, queja_id=queja_id)
    except Exception:
        log.warning("Queja not found for file, skipping")
        return

    adjuntos = item.get("adjuntos", []) or []
    if file_url not in adjuntos:
        adjuntos.append(file_url)
        dynamo.update_item(
            pk=queja_pk(tenant_id, queja_id),
            sk=queja_sk(queja_id),
            updates={
                "adjuntos": adjuntos,
                "updatedAt": now_iso(),
            },
        )
        log.info("Queja updated with new file URL")


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """S3 event handler."""
    with_correlation_id(event)
    try:
        records = event.get("Records", [])
        log.info(f"Processing {len(records)} S3 records")

        for record in records:
            try:
                _process_record(record)
            except Exception:
                log.exception("Failed to process S3 record")

        return {"statusCode": 200, "body": "OK"}
    finally:
        clear_correlation_id()
