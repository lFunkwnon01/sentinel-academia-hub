#!/usr/bin/env python3
"""Ingest PDFs into the per-tenant knowledge base.

For each (tenant_id, pdf_path) pair:
1. Parse the PDF (extract text per page)
2. Chunk into ~1000 char segments with 200 char overlap
3. Upload chunks to DynamoDB (sentinel-knowledge-chunks-{stage})
4. Upload original PDF to S3 (tenant-knowledge/{tenantId}/{docId}.pdf)

Usage:
    export PYTHONPATH=src:$PYTHONPATH
    export AWS_PROFILE=academy
    python3 scripts/ingest_knowledge.py

The PDF_LIBRARY below is the source of truth for what gets ingested.
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import boto3
import fitz  # pymupdf - much better Spanish text extraction than pypdf/pdfplumber
from botocore.exceptions import ClientError


# ---------------------------------------------------------------------------
# Configuration: which PDFs to ingest for which tenants
# ---------------------------------------------------------------------------
PDF_LIBRARY: list[dict[str, str]] = [
    {
        "tenantId": "demo-utec",
        "docId": "reglamento-academico",
        "title": "Reglamento Academico UTEC",
        "path": "/home/lFunknown/Descargas/Reglamento Academico_0.pdf",
    },
    {
        "tenantId": "demo-utec",
        "docId": "reglamento-disciplina",
        "title": "Reglamento de Disciplina - Estudiantes 2024",
        "path": "/home/lFunknown/Descargas/reglamento_de_disciplina_de_los_estudiantes_2024.pdf",
    },
]


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
STAGE = os.environ.get("STAGE", "dev")
TABLE_NAME = f"sentinel-knowledge-chunks-{STAGE}"
BUCKET_NAME = f"sentinel-knowledge-{STAGE}-227165337884"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Normalize unicode and clean up PDF extraction artifacts.

    pymupdf extracts text cleanly with tildes intact, so we only need
    minimal cleanup: collapse whitespace, normalize quotes/dashes.
    """
    # NFKC keeps accents (á é í ó ú ñ) intact, just normalizes compatibility forms
    text = unicodedata.normalize("NFKC", text)
    # Normalize smart quotes/dashes
    text = text.replace("\u2013", "-").replace("\u2014", " - ")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    # Collapse whitespace (keep newlines, collapse spaces/tabs)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pages(pdf_path: str) -> list[dict[str, Any]]:
    """Extract text per page from a PDF using pymupdf (best for Spanish)."""
    pages: list[dict[str, Any]] = []
    doc = fitz.open(pdf_path)
    try:
        for idx, page in enumerate(doc, start=1):
            try:
                # "text" mode preserves spacing and unicode (tildes)
                text = page.get_text("text") or ""
            except Exception as e:  # noqa: BLE001
                print(f"  Warning: could not extract page {idx}: {e}")
                text = ""
            text = _normalize(text)
            if text:
                pages.append({"page": idx, "text": text})
    finally:
        doc.close()
    return pages


def _chunk_pages(pages: list[dict[str, Any]], size: int, overlap: int) -> list[dict[str, Any]]:
    """Split pages into chunks of ~size characters, respecting paragraph breaks.

    Strategy:
    - Group paragraphs from the same page into chunks of ~size characters.
    - Break on double-newlines (paragraph boundaries) when possible.
    - Track which page each chunk came from.
    """
    chunks: list[dict[str, Any]] = []
    # Build list of (page, paragraph) tuples
    units: list[tuple[int, str]] = []
    for p in pages:
        for para in p["text"].split("\n\n"):
            para = para.strip()
            if para:
                units.append((p["page"], para))

    if not units:
        return chunks

    current: list[str] = []
    current_len = 0
    current_page = units[0][0]

    for page, para in units:
        para_len = len(para) + 2  # +2 for "\n\n"
        if current_len + para_len > size and current:
            # Flush current chunk
            chunks.append({"content": "\n\n".join(current).strip(), "page": current_page})
            # Keep last paragraph as overlap if it's not too long
            if current and len(current[-1]) <= overlap:
                current = [current[-1], para]
                current_len = len(current[-1]) + para_len
                current_page = page
            else:
                current = [para]
                current_len = para_len
                current_page = page
        else:
            current.append(para)
            current_len += para_len
            current_page = page

    if current:
        chunks.append({"content": "\n\n".join(current).strip(), "page": current_page})

    return chunks


def _ensure_dynamo_table(dynamo_client) -> None:
    """Create the knowledge-chunks table if it doesn't exist."""
    try:
        dynamo_client.describe_table(TableName=TABLE_NAME)
        print(f"  Table {TABLE_NAME} already exists")
        return
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise

    print(f"  Creating table {TABLE_NAME}...")
    dynamo_client.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    waiter = dynamo_client.get_waiter("table_exists")
    waiter.wait(TableName=TABLE_NAME, WaiterConfig={"Delay": 2, "MaxAttempts": 30})
    print(f"  Table {TABLE_NAME} created")


def _delete_existing_chunks(dynamo_resource, tenant_id: str, doc_id: str) -> int:
    """Remove all chunks for a (tenantId, docId) before re-ingesting."""
    table = dynamo_resource.Table(TABLE_NAME)
    pk_prefix = f"TENANT#{tenant_id}#DOC#{doc_id}#"
    last_key: dict[str, Any] | None = None
    deleted = 0

    while True:
        scan_kwargs: dict[str, Any] = {
            "FilterExpression": "begins_with(pk, :prefix)",
            "ExpressionAttributeValues": {":prefix": pk_prefix},
            "ProjectionExpression": "pk, sk",
        }
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key
        resp = table.scan(**scan_kwargs)
        with table.batch_writer() as batch:
            for item in resp.get("Items", []):
                batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
                deleted += 1
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
    return deleted


def _upload_chunks(dynamo_resource, tenant_id: str, doc_id: str, doc_title: str, chunks: list[dict[str, Any]]) -> int:
    """Upload chunks to DynamoDB."""
    table = dynamo_resource.Table(TABLE_NAME)
    total = len(chunks)
    print(f"  Uploading {total} chunks...")
    with table.batch_writer() as batch:
        for idx, chunk in enumerate(chunks):
            batch.put_item(
                Item={
                    "pk": f"TENANT#{tenant_id}#DOC#{doc_id}#CHUNK#{idx:04d}",
                    "sk": f"CHUNK#{idx:04d}",
                    "tenantId": tenant_id,
                    "docId": doc_id,
                    "docTitle": doc_title,
                    "chunkIdx": idx,
                    "totalChunks": total,
                    "content": chunk["content"],
                    "source": doc_title,
                    "page": chunk["page"],
                    "charCount": len(chunk["content"]),
                }
            )
    return total


def _upload_pdf_to_s3(s3_client, tenant_id: str, doc_id: str, pdf_path: str) -> str:
    """Upload the original PDF to S3 for reference."""
    key = f"tenant-knowledge/{tenant_id}/{doc_id}.pdf"
    s3_client.upload_file(pdf_path, BUCKET_NAME, key)
    return f"s3://{BUCKET_NAME}/{key}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print(f"=== Ingest Knowledge Base (stage={STAGE}) ===")
    print(f"  Target table: {TABLE_NAME}")
    print(f"  Target bucket: {BUCKET_NAME}")
    print()

    session = boto3.Session()
    region = session.region_name or "us-east-1"
    dynamo_client = session.client("dynamodb", region_name=region)
    dynamo_resource = session.resource("dynamodb", region_name=region)
    s3_client = session.client("s3", region_name=region)

    _ensure_dynamo_table(dynamo_client)

    total_chunks_uploaded = 0
    for entry in PDF_LIBRARY:
        path = Path(entry["path"])
        if not path.exists():
            print(f"[SKIP] {entry['tenantId']}/{entry['docId']}: file not found {path}")
            continue

        print(f"[INGEST] {entry['tenantId']} <- {path.name}")
        pages = _extract_pages(str(path))
        print(f"  Extracted {len(pages)} pages, {sum(len(p['text']) for p in pages)} chars")
        if not pages:
            print(f"  [WARN] no text extracted, skipping")
            continue

        chunks = _chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"  Chunked into {len(chunks)} segments (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

        deleted = _delete_existing_chunks(dynamo_resource, entry["tenantId"], entry["docId"])
        if deleted:
            print(f"  Removed {deleted} old chunks")

        uploaded = _upload_chunks(
            dynamo_resource, entry["tenantId"], entry["docId"], entry["title"], chunks
        )
        try:
            s3_uri = _upload_pdf_to_s3(s3_client, entry["tenantId"], entry["docId"], str(path))
            print(f"  PDF uploaded to {s3_uri}")
        except ClientError as e:
            print(f"  [WARN] could not upload PDF to S3: {e}")
        total_chunks_uploaded += uploaded
        print()

    print(f"=== Done: {total_chunks_uploaded} chunks across {len(PDF_LIBRARY)} documents ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
