"""Tests for the RAG knowledge service."""

from __future__ import annotations


class TestKnowledgeService:
    def test_search_returns_results(self):
        from src.services.knowledge_service import search

        results = search("acoso universidad", top_k=3)
        assert len(results) > 0
        assert all("id" in r and "title" in r and "content" in r for r in results)

    def test_search_relevant_for_acoso(self):
        from src.services.knowledge_service import search

        results = search("acoso")
        # The FAQ for acoso should be in top results
        assert any("acoso" in r["id"].lower() for r in results)

    def test_search_relevant_for_plazos(self):
        from src.services.knowledge_service import search

        results = search("plazos critica")
        # Should find something with plazos
        assert len(results) > 0

    def test_search_empty_query(self):
        from src.services.knowledge_service import search

        assert search("") == []
        assert search("   ") == []
        assert search(None) == []  # type: ignore

    def test_search_no_match(self):
        from src.services.knowledge_service import search

        # Random gibberish with no overlap
        results = search("xyzzy12345qwerty")
        assert results == []

    def test_search_top_k(self):
        from src.services.knowledge_service import search

        results = search("queja", top_k=2)
        assert len(results) <= 2

    def test_search_scores_descending(self):
        from src.services.knowledge_service import search

        results = search("acoso reglamento queja")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_build_context(self):
        from src.services.knowledge_service import build_context

        ctx = build_context("acoso", top_k=3)
        assert "Contexto relevante" in ctx
        assert "FAQ" in ctx or "Articulo" in ctx

    def test_build_context_no_match(self):
        from src.services.knowledge_service import build_context

        ctx = build_context("xyzqwerty123", top_k=3)
        assert ctx == ""

    def test_tokenize_basic(self):
        from src.services.knowledge_service import _tokenize

        tokens = _tokenize("Hola, Mundo! 123")
        assert "hola" in tokens
        assert "mundo" in tokens
        assert "123" in tokens
        # Punctuation removed
        assert "," not in tokens
        assert "!" not in tokens
