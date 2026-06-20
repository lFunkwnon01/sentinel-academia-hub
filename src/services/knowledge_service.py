"""Knowledge service for RAG.

Searches across per-tenant knowledge chunks stored in DynamoDB.
Falls back to hardcoded docs if no chunks exist for the tenant.

For production: replace keyword search with OCI Generative AI Agents
(managed RAG) or vector embeddings (Cohere embed-multilingual-v3.0).
"""

from __future__ import annotations

import os
import re
import threading
from functools import lru_cache
from typing import Any

from handlers._shared.logger import get_logger

log = get_logger(__name__)

# Minimum score to consider a match "relevant" (else fall through to fallback).
# 2 = at least 2 query tokens must match in the document.
RELEVANCE_THRESHOLD = 2


# The hardcoded fallback knowledge base (used only if a tenant has no chunks).
KNOWLEDGE_BASE: list[dict[str, str]] = [
    {
        "id": "reglamento-cap1",
        "title": "Capitulo 1: Disposiciones generales",
        "content": (
            "Articulo 1. Toda queja sera registrada en el sistema Sentinel AcademIA. "
            "Articulo 4. Las categorias son: ACADEMICA (profesores, cursos), "
            "INFRAESTRUCTURA (aulas, edificios), ACOSO (hostigamiento, violencia), "
            "ADMINISTRATIVA (matriculas, tramites), SALUD (salud mental), OTRA."
        ),
    },
    {
        "id": "reglamento-cap2",
        "title": "Capitulo 2: Proceso de atencion",
        "content": (
            "Articulo 5. Criticidad: BAJA (informativos), MEDIA (5 dias), "
            "ALTA (48 horas), CRITICA (notificacion INMEDIATA). "
            "Articulo 6. Las quejas CRITICAS notifican a BIENESTAR, DIRECCION, "
            "RECURSOS_HUMANOS, SEGURIDAD. "
            "Articulo 8. Plazos: CRITICA 24h, ALTA 3 dias, MEDIA 5 dias, BAJA 10 dias."
        ),
    },
    {
        "id": "reglamento-cap3",
        "title": "Capitulo 3: Derechos del reportante",
        "content": (
            "Articulo 9. El reportante tiene derecho a: conocer el estado, "
            "recibir notificaciones, escalar la queja, solicitar revision. "
            "Articulo 10. La identidad es confidencial (excepto quejas anonimas). "
            "Articulo 11. Quejas escaladas son revisadas por un comite de 3 miembros."
        ),
    },
    {
        "id": "reglamento-cap4",
        "title": "Capitulo 4: Sanciones",
        "content": (
            "Articulo 12. Las sanciones dependen de la gravedad: "
            "BAJA (amonestacion verbal), MEDIA (amonestacion escrita), "
            "ALTA (suspension 5-15 dias), CRITICA (suspension 30+ dias o expulsion). "
            "Articulo 13. Plazo maximo para aplicar sancion: 30 dias habiles."
        ),
    },
    {
        "id": "reglamento-cap5",
        "title": "Capitulo 5: Procedimiento de escalamiento",
        "content": (
            "Articulo 15. Escalar requiere motivo de 10+ caracteres. Al escalar, "
            "la queja cambia a prioridad ALTA. Articulo 16. Autoridades responden "
            "en 24h. Articulo 17. Dashboard disponible con metricas por "
            "categoria, criticidad, sede y facultad."
        ),
    },
    {
        "id": "reglamento-faq-acoso",
        "title": "FAQ: Que hacer en caso de acoso",
        "content": (
            "Si sufres acoso: 1) Reporta inmediatamente con tu queja anonima. "
            "2) El sistema clasifica como CRITICA automaticamente. "
            "3) Se notifica a BIENESTAR y SEGURIDAD. "
            "4) Puedes escalar para revision por comite. "
            "5) Tienes derecho a confidencialidad total."
        ),
    },
    {
        "id": "reglamento-faq-infraestructura",
        "title": "FAQ: Problemas de infraestructura",
        "content": (
            "Para aulas danadas, banos, electricidad, filtraciones: "
            "1) Reporta con categoria INFRAESTRUCTURA. "
            "2) Adjunta fotos como evidencia. "
            "3) Si afecta la salud (filtraciones, moho), prioridad MEDIA pero "
            "se atiende en 48h maximo segun Articulo 13. "
            "4) Si es urgente, contacta directamente a +1-800-QUEJAS."
        ),
    },
    {
        "id": "reglamento-faq-salud",
        "title": "FAQ: Bienestar y salud mental",
        "content": (
            "Si necesitas apoyo psicologico o reportar situacion de salud mental: "
            "1) Contacta a BIENESTAR (bienestar@universidad.edu). "
            "2) Si es urgente, llama a la linea de crisis 24/7. "
            "3) Puedes reportar anonimamente si lo prefieres. "
            "4) La universidad ofrece hasta 8 sesiones gratis con psicologo."
        ),
    },
]


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------
def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words (no punctuation)."""
    return re.findall(r"\b\w+\b", text.lower())


# ---------------------------------------------------------------------------
# DDB chunks (per-tenant)
# ---------------------------------------------------------------------------
_dynamo_resource = None
_dynamo_resource_lock = threading.Lock()
_ddb_cache: dict[str, list[dict[str, Any]]] = {}
_ddb_cache_ttl: dict[str, float] = {}
DDB_CACHE_TTL_SECONDS = 60


def _get_dynamo_resource():
    """Lazy singleton DynamoDB resource (avoids import-time boto3 issues)."""
    global _dynamo_resource
    if _dynamo_resource is None:
        with _dynamo_resource_lock:
            if _dynamo_resource is None:
                import boto3

                stage = os.environ.get("STAGE", "dev")
                table_name = f"sentinel-knowledge-chunks-{stage}"
                _dynamo_resource = {
                    "table_name": table_name,
                    "resource": boto3.resource("dynamodb"),
                }
    return _dynamo_resource


def _get_table():
    return _get_dynamo_resource()["resource"].Table(_get_dynamo_resource()["table_name"])


def _fetch_tenant_chunks(tenant_id: str) -> list[dict[str, Any]]:
    """Fetch all chunks for a tenant from DynamoDB (with TTL cache)."""
    import time

    cached = _ddb_cache.get(tenant_id)
    cache_time = _ddb_cache_ttl.get(tenant_id, 0)
    if cached is not None and (time.time() - cache_time) < DDB_CACHE_TTL_SECONDS:
        return cached

    try:
        table = _get_table()
    except Exception as e:  # noqa: BLE001
        log.warning("Could not get DDB table", extra={"error": str(e)})
        return []

    chunks: list[dict[str, Any]] = []
    last_key: dict[str, Any] | None = None
    pk_prefix = f"TENANT#{tenant_id}#"

    try:
        while True:
            scan_kwargs: dict[str, Any] = {
                "FilterExpression": "begins_with(pk, :prefix)",
                "ExpressionAttributeValues": {":prefix": pk_prefix},
            }
            if last_key:
                scan_kwargs["ExclusiveStartKey"] = last_key
            resp = table.scan(**scan_kwargs)
            for item in resp.get("Items", []):
                chunks.append(
                    {
                        "id": f"{item.get('docId', 'unknown')}#{item.get('chunkIdx', 0)}",
                        "title": item.get("docTitle", item.get("docId", "Documento")),
                        "content": item.get("content", ""),
                        "page": int(item.get("page", 0)),
                        "source": item.get("source", ""),
                        "docId": item.get("docId", ""),
                    }
                )
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
        log.info(
            "Loaded tenant chunks from DDB",
            extra={"tenant_id": tenant_id, "chunk_count": len(chunks)},
        )
    except Exception as e:  # noqa: BLE001
        log.warning(
            "Could not fetch tenant chunks", extra={"tenant_id": tenant_id, "error": str(e)}
        )
        return []

    _ddb_cache[tenant_id] = chunks
    _ddb_cache_ttl[tenant_id] = time.time()
    return chunks


def invalidate_cache(tenant_id: str | None = None) -> None:
    """Clear the DDB cache (call after re-ingestion)."""
    if tenant_id:
        _ddb_cache.pop(tenant_id, None)
        _ddb_cache_ttl.pop(tenant_id, None)
    else:
        _ddb_cache.clear()
        _ddb_cache_ttl.clear()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def _score_doc(query_tokens: list[str], doc: dict[str, Any]) -> int:
    """Score a document by how many query tokens it contains."""
    doc_tokens = set(_tokenize(str(doc.get("title", "")) + " " + str(doc.get("content", ""))))
    return sum(1 for tok in query_tokens if tok in doc_tokens)


def _search_in_docs(query_tokens: list[str], docs: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    if not query_tokens or not docs:
        return []
    scored = [(doc, _score_doc(query_tokens, doc)) for doc in docs]
    scored = [(doc, score) for doc, score in scored if score > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        {
            "id": doc.get("id", ""),
            "title": doc.get("title", "Documento"),
            "content": doc.get("content", ""),
            "page": doc.get("page"),
            "source": doc.get("source", doc.get("title", "")),
            "docId": doc.get("docId"),
            "score": score,
        }
        for doc, score in scored[:top_k]
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def search(query: str, top_k: int = 3, tenant_id: str | None = None) -> list[dict[str, Any]]:
    """Search the knowledge base for the most relevant documents.

    Strategy:
    1. If tenant_id provided, search tenant-specific chunks in DynamoDB.
    2. Only use DDB results if score >= RELEVANCE_THRESHOLD (otherwise the
       match is likely spurious and we should fall through to hardcoded).
    3. Fall back to the hardcoded KNOWLEDGE_BASE (which has the Sentinel
       queja process info that the tenant PDFs may not contain).

    Returns:
        List of {id, title, content, page, source, score} sorted by relevance.
    """
    if not query or not query.strip():
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    if tenant_id:
        tenant_chunks = _fetch_tenant_chunks(tenant_id)
        if tenant_chunks:
            results = _search_in_docs(query_tokens, tenant_chunks, top_k)
            top_score = results[0]["score"] if results else 0
            # Only use tenant chunks if the best match is genuinely relevant
            if results and top_score >= RELEVANCE_THRESHOLD:
                log.info(
                    "RAG search (DDB chunks - high relevance)",
                    extra={
                        "tenant_id": tenant_id,
                        "results": len(results),
                        "top_score": top_score,
                    },
                )
                return results
            else:
                log.info(
                    "RAG search (DDB chunks - low relevance, using fallback)",
                    extra={
                        "tenant_id": tenant_id,
                        "results": len(results),
                        "top_score": top_score,
                    },
                )

    results = _search_in_docs(query_tokens, KNOWLEDGE_BASE, top_k)
    log.info(
        "RAG search (hardcoded fallback)",
        extra={"results": len(results), "top_score": results[0]["score"] if results else 0},
    )
    return results


def build_context(query: str, top_k: int = 3, tenant_id: str | None = None) -> str:
    """Build a context string for the LLM from the search results."""
    results = search(query, top_k=top_k, tenant_id=tenant_id)
    if not results:
        return ""

    lines = ["[Contexto relevante del reglamento:]"]
    for r in results:
        page_info = f" (pag. {r['page']})" if r.get("page") else ""
        lines.append(f"\n--- {r['title']}{page_info} ---")
        lines.append(r["content"])
    return "\n".join(lines)
