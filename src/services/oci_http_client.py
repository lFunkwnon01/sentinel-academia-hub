"""OCI Cohere client using direct HTTP (no SDK).

Uses only stdlib + cryptography (already in Lambda runtime).
Implements OCI's request signing with RSA-SHA256.

API endpoint: https://inference.generativeai.{region}.oci.oraclecloud.com

Sign format (per OCI spec, matched to oci-python-sdk output):
- Headers signed: date, (request-target), host, content-length, content-type, x-content-sha256
- x-content-sha256 is base64-encoded SHA256 of the body (NOT hex)
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from handlers._shared.logger import get_logger

log = get_logger(__name__)


class OCIError(Exception):
    """OCI API error."""


def _load_private_key(key_path: str):
    with open(key_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _sign_request(
    method: str,
    url: str,
    body: bytes,
    *,
    user_ocid: str,
    tenancy_ocid: str,
    fingerprint: str,
    private_key,
) -> dict[str, str]:
    """Sign an OCI API request using the oci-python-sdk format."""
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    # x-content-sha256 is base64-encoded SHA256 (matches oci-python-sdk)
    content_sha256_b64 = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
    content_length = str(len(body))
    date_str = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Build signing string in the order: date, (request-target), host,
    # content-length, content-type, x-content-sha256
    signing_lines = [
        f"date: {date_str}",
        f"(request-target): {method.lower()} {path}",
        f"host: {host}",
        f"content-length: {content_length}",
        f"content-type: application/json",
        f"x-content-sha256: {content_sha256_b64}",
    ]
    signing_string = "\n".join(signing_lines)

    signature_bytes = private_key.sign(
        signing_string.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    key_id = f"{tenancy_ocid}/{user_ocid}/{fingerprint}"
    headers_in_sig = "date (request-target) host content-length content-type x-content-sha256"
    signature_header = (
        f'Signature algorithm="rsa-sha256",'
        f'headers="{headers_in_sig}",'
        f'keyId="{key_id}",'
        f'signature="{signature_b64}",'
        f'version="1"'
    )

    return {
        "host": host,
        "date": date_str,
        "content-length": content_length,
        "content-type": "application/json",
        "x-content-sha256": content_sha256_b64,
        "authorization": signature_header,
    }


def call_oci_cohere_chat(
    *,
    user_ocid: str,
    tenancy_ocid: str,
    fingerprint: str,
    key_file: str,
    compartment_id: str,
    model_ocid: str,
    region: str,
    message: str,
    preamble: str | None = None,
    max_tokens: int = 600,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """Call OCI Cohere Chat API via direct HTTP. Returns parsed response + latency."""
    endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"
    url = f"{endpoint}/20231130/actions/chat"

    cohere_request: dict[str, Any] = {
        "apiFormat": "COHERE",
        "message": message,
        "isStream": False,
        "maxTokens": max_tokens,
        "temperature": temperature,
    }
    if preamble:
        cohere_request["preambleOverride"] = preamble

    body_dict = {
        "compartmentId": compartment_id,
        "servingMode": {
            "servingType": "ON_DEMAND",
            "modelId": model_ocid,
        },
        "chatRequest": cohere_request,
    }
    body_bytes = json.dumps(body_dict).encode("utf-8")

    private_key = _load_private_key(key_file)
    auth_headers = _sign_request(
        method="POST",
        url=url,
        body=body_bytes,
        user_ocid=user_ocid,
        tenancy_ocid=tenancy_ocid,
        fingerprint=fingerprint,
        private_key=private_key,
    )

    req = Request(url=url, data=body_bytes, method="POST", headers=auth_headers)
    start = time.time()
    try:
        with urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        log.error("OCI Cohere HTTP error", extra={"status": e.code, "body": error_body[:500]})
        raise OCIError(f"OCI Cohere HTTP {e.code}: {error_body[:200]}") from e
    except URLError as e:
        log.error("OCI Cohere URL error", extra={"error": str(e)})
        raise OCIError(f"OCI Cohere URL error: {e}") from e

    latency_ms = int((time.time() - start) * 1000)
    log.info("OCI Cohere call success", extra={"latency_ms": latency_ms, "region": region})
    return {"payload": payload, "latency_ms": latency_ms}
