"""S3 file service for evidence uploads.

Pattern: Presigned URLs
- Client requests upload URL from API
- API returns presigned PUT URL (valid for X minutes)
- Client uploads directly to S3 (bypasses API)
- S3 event triggers file_processor Lambda
- file_processor updates queja with file URL
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3

from handlers._shared.config import get_settings
from handlers._shared.errors import AppError
from handlers._shared.logger import get_logger

log = get_logger(__name__)


ALLOWED_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
]

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class FileError(AppError):
    """Error related to file operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message, status_code=400, error_code="FILE_ERROR", details=details
        )


def build_s3_key(tenant_id: str, queja_id: str, filename: str) -> str:
    """Build the S3 key for a file.

    Pattern: tenants/{tenantId}/quejas/{quejaId}/{uuid}-{filename}
    """
    # Sanitize filename
    safe_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    file_id = uuid.uuid4().hex[:12]
    return f"tenants/{tenant_id}/quejas/{queja_id}/{file_id}-{safe_filename}"


def build_s3_url(bucket: str, key: str, region: str = "us-east-1") -> str:
    """Build the public S3 URL for a key."""
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def generate_presigned_upload_url(
    queja_id: str,
    tenant_id: str,
    filename: str,
    content_type: str,
    file_size: int | None = None,
) -> dict[str, Any]:
    """Generate a presigned URL for uploading a file to S3.

    Args:
        queja_id: The queja this file belongs to
        tenant_id: The tenant ID (multi-tenant)
        filename: Original filename
        content_type: MIME type
        file_size: Optional file size in bytes (validated)

    Returns:
        dict with uploadUrl, fileKey, fileUrl, expiresIn
    """
    settings = get_settings()
    bucket = settings.files_bucket_resolved

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise FileError(
            f"Content type {content_type} not allowed",
            details={"allowed": ALLOWED_CONTENT_TYPES},
        )

    if file_size is not None and file_size > MAX_FILE_SIZE_BYTES:
        raise FileError(
            f"File too large: {file_size} bytes (max {MAX_FILE_SIZE_BYTES})",
            details={"maxSize": MAX_FILE_SIZE_BYTES},
        )

    s3_key = build_s3_key(tenant_id, queja_id, filename)
    s3 = boto3.client("s3")
    expires_in = 900  # 15 minutes

    try:
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
    except Exception as e:
        log.error("Failed to generate presigned URL", extra={"error": str(e)})
        raise FileError("Could not generate upload URL") from e

    return {
        "uploadUrl": upload_url,
        "fileKey": s3_key,
        "fileUrl": build_s3_url(bucket, s3_key),
        "expiresIn": expires_in,
        "maxSize": MAX_FILE_SIZE_BYTES,
    }


def generate_presigned_download_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for downloading a file from S3."""
    settings = get_settings()
    bucket = settings.files_bucket_resolved
    s3 = boto3.client("s3")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expires_in,
    )


def list_queja_files(tenant_id: str, queja_id: str) -> list[dict[str, Any]]:
    """List all files for a queja from S3."""
    settings = get_settings()
    bucket = settings.files_bucket_resolved
    prefix = f"tenants/{tenant_id}/quejas/{queja_id}/"
    s3 = boto3.client("s3")
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files = []
        for obj in response.get("Contents", []):
            files.append(
                {
                    "key": obj["Key"],
                    "url": build_s3_url(bucket, obj["Key"]),
                    "size": obj["Size"],
                    "lastModified": obj["LastModified"].isoformat(),
                }
            )
        return files
    except Exception as e:
        log.error("Failed to list files", extra={"error": str(e)})
        return []


def now_iso() -> str:
    """Get current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).isoformat()
