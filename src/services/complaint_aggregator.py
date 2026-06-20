"""Complaint aggregation service.

For INFRAESTRUCTURA category, wait for a sample size (default 10) of similar
complaints before triggering analysis/notification. Uses keyword overlap to
find similar complaints.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from boto3.dynamodb.conditions import Attr

from handlers._shared.dynamo_client import get_dynamo_client
from handlers._shared.logger import get_logger

log = get_logger(__name__)

# Minimum sample size before triggering notification for collective categories
INFRAESTRUCTURA_SAMPLE_SIZE = 10

# Stop words for keyword extraction
_STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "en", "un", "una", "y", "o",
    "que", "a", "es", "se", "no", "con", "para", "por", "al", "le", "lo",
    "si", "su", "sus", "le", "les", "ha", "han", "este", "esta", "esto",
    "estos", "estas", "ese", "esa", "eso", "muy", "mas", "pero", "porque",
    "como", "cuando", "donde", "desde", "hasta", "tambien", "tambien",
    "tener", "tengo", "tienes", "tenemos", "son", "ser", "estar", "esta",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words (excluding stopwords)."""
    tokens = re.findall(r"\b[a-záéíóúñ]{4,}\b", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _keyword_signature(text: str, top_k: int = 5) -> frozenset[str]:
    """Return the top-K most relevant keywords for similarity matching."""
    tokens = _tokenize(text)
    if not tokens:
        return frozenset()
    counter = Counter(tokens)
    return frozenset(word for word, _ in counter.most_common(top_k))


def _similarity(a: frozenset[str], b: frozenset[str]) -> float:
    """Jaccard similarity between two keyword sets."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_similar_complaints(
    tenant_id: str,
    title: str,
    description: str,
    categoria: str,
    *,
    min_similarity: float = 0.3,
    max_age_days: int = 90,
) -> list[dict[str, Any]]:
    """Find existing complaints similar to the given one (by keyword overlap).

    Returns list of similar complaints with similarity scores, sorted desc.
    """
    dynamo = get_dynamo_client()
    signature = _keyword_signature(f"{title} {description}")
    if not signature:
        return []

    items = dynamo._table.scan(
        FilterExpression=(
            Attr("pk").begins_with(f"TENANT#{tenant_id}#QUEJA#")
            & Attr("categoriaDeclarada").eq(categoria)
        )
    ).get("Items", [])

    similar: list[dict[str, Any]] = []
    for item in items:
        other_text = f"{item.get('titulo', '')} {item.get('descripcion', '')}"
        other_sig = _keyword_signature(other_text)
        sim = _similarity(signature, other_sig)
        if sim >= min_similarity:
            similar.append({**item, "similarity": sim})
    similar.sort(key=lambda x: x["similarity"], reverse=True)
    return similar


def should_trigger_aggregate_notification(
    tenant_id: str,
    new_complaint: dict[str, Any],
    *,
    threshold: int = INFRAESTRUCTURA_SAMPLE_SIZE,
) -> tuple[bool, list[dict[str, Any]]]:
    """Decide if we have enough similar complaints to notify.

    Returns:
        (should_notify, similar_complaints_list)
    """
    similar = find_similar_complaints(
        tenant_id=tenant_id,
        title=new_complaint.get("titulo", ""),
        description=new_complaint.get("descripcion", ""),
        categoria=new_complaint.get("categoriaDeclarada", ""),
    )
    # The new complaint is +1, so threshold means we need threshold total
    return (len(similar) + 1 >= threshold, similar)


def summarize_cluster(complaints: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a summary of a cluster of similar complaints for the notification."""
    if not complaints:
        return {"count": 0, "common_keywords": [], "sedes": [], "facultades": []}

    all_keywords: list[str] = []
    sedes: Counter[str] = Counter()
    facultades: Counter[str] = Counter()

    for c in complaints:
        all_keywords.extend(_tokenize(f"{c.get('titulo', '')} {c.get('descripcion', '')}"))
        if c.get("sede"):
            sedes[c["sede"]] += 1
        if c.get("facultad"):
            facultades[c["facultad"]] += 1

    return {
        "count": len(complaints),
        "common_keywords": [w for w, _ in Counter(all_keywords).most_common(10)],
        "top_sedes": [s for s, _ in sedes.most_common(3)],
        "top_facultades": [f for f, _ in facultades.most_common(3)],
        "sample_titles": [c.get("titulo", "") for c in complaints[:3]],
    }
