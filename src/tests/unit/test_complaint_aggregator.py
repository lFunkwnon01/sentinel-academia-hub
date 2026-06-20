"""Tests for complaint_aggregator service."""

from __future__ import annotations

import pytest

from services.complaint_aggregator import (
    INFRAESTRUCTURA_SAMPLE_SIZE,
    _keyword_signature,
    _similarity,
    find_similar_complaints,
    should_trigger_aggregate_notification,
    summarize_cluster,
)


class TestKeywordSignature:
    def test_returns_set(self):
        sig = _keyword_signature("Los banos del segundo piso estan sucios")
        assert isinstance(sig, frozenset)
        assert "banos" in sig or "sucios" in sig

    def test_excludes_stopwords(self):
        sig = _keyword_signature("el la los las de en un una que a es se")
        assert len(sig) == 0

    def test_lowercases(self):
        sig1 = _keyword_signature("Banos SUCIOS")
        sig2 = _keyword_signature("banos sucios")
        assert sig1 == sig2


class TestSimilarity:
    def test_identical_sets(self):
        a = frozenset({"banos", "sucios", "edificio"})
        b = frozenset({"banos", "sucios", "edificio"})
        assert _similarity(a, b) == 1.0

    def test_disjoint_sets(self):
        a = frozenset({"banos", "sucios"})
        b = frozenset({"notas", "profesor"})
        assert _similarity(a, b) == 0.0

    def test_partial_overlap(self):
        a = frozenset({"banos", "sucios", "edificio"})
        b = frozenset({"banos", "sucios", "profesor"})
        # 2 / 4 = 0.5
        assert _similarity(a, b) == 0.5


class TestShouldTriggerAggregate:
    def test_below_threshold(self, dynamodb):
        """With no existing complaints, even 1 new one is below threshold."""
        should, similar = should_trigger_aggregate_notification(
            "test-tenant",
            {"titulo": "Banos sucios", "descripcion": "banos sucios segundo piso", "categoriaDeclarada": "INFRAESTRUCTURA"},
            threshold=10,
        )
        assert should is False
        assert similar == []

    def test_at_threshold(self, dynamo_client, sample_queja):
        """When we have enough similar complaints, trigger."""
        # Insert 9 similar complaints via the client
        for i in range(9):
            item = dict(sample_queja)
            item["quejaId"] = f"q-{i:04d}"
            item["pk"] = f"TENANT#test-tenant#QUEJA#q-{i:04d}"
            item["sk"] = f"QUEJA#q-{i:04d}"
            item["categoriaDeclarada"] = "INFRAESTRUCTURA"
            item["titulo"] = f"Banos sucios piso {i}"
            item["descripcion"] = "Los banos estan sucios y malolientes"
            dynamo_client.put_item(item=item)

        # New complaint (10th)
        should, similar = should_trigger_aggregate_notification(
            "test-tenant",
            {"titulo": "Banos sucios", "descripcion": "Los banos del segundo piso estan sucios", "categoriaDeclarada": "INFRAESTRUCTURA"},
            threshold=10,
        )
        assert should is True
        assert len(similar) >= 9


class TestSummarizeCluster:
    def test_empty_cluster(self):
        result = summarize_cluster([])
        assert result["count"] == 0

    def test_extracts_common_keywords(self, sample_queja):
        cluster = []
        for i in range(5):
            item = dict(sample_queja)
            item["titulo"] = f"Banos sucios piso {i}"
            item["descripcion"] = "Los banos del piso estan sucios"
            item["sede"] = "Sede Norte" if i < 3 else "Sede Sur"
            cluster.append(item)
        result = summarize_cluster(cluster)
        assert result["count"] == 5
        assert "banos" in result["common_keywords"]
        assert "Sede Norte" in result["top_sedes"]
