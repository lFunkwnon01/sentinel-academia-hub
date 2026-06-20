"""Integration tests for Lambda handlers."""

from __future__ import annotations

import json
import sys


# Make sure we use the same module path as the runtime
# The runtime uses `handlers._shared.X` (no `src.` prefix)
# because Python adds the handler dir to the path
# We add src/ to PYTHONPATH so both paths work
# But the singleton exceptions need to be the SAME class

class TestHealthCheck:
    def test_returns_healthy(self, api_event):
        from handlers.health_check import lambda_handler

        event = api_event(method="GET", path="/health")
        result = lambda_handler(event, context={})
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "healthy"
        assert body["service"] == "sentinel-academia"


class TestCreateQueja:
    def test_creates_queja(self, api_event, sample_queja, dynamo_client):
        from handlers.create_queja import lambda_handler

        event = api_event(method="POST", path="/api/quejas", body=sample_queja)
        # Mock SQS to avoid real AWS call
        import unittest.mock

        with unittest.mock.patch(
            "src.handlers.create_queja._send_to_sqs"
        ) as mock_sqs:
            result = lambda_handler(event, context={})

        assert result["statusCode"] == 202
        body = json.loads(result["body"])
        assert "quejaId" in body
        assert body["status"] == "PENDIENTE"
        assert body["correlationId"] == "test-correlation-123"

        # Verify it was stored
        items = dynamo_client.query_by_tenant(tenant_id="test-tenant")
        assert len(items) == 1
        assert items[0]["titulo"] == sample_queja["titulo"]

    def test_validation_error_short_titulo(self, api_event, dynamo_client):
        from handlers.create_queja import lambda_handler

        bad = {
            "titulo": "abc",  # too short
            "descripcion": "Descripcion larga",
            "categoriaDeclarada": "OTRA",
        }
        event = api_event(method="POST", path="/api/quejas", body=bad)
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["code"] == "VALIDATION_ERROR"

    def test_validation_error_invalid_categoria(self, api_event, dynamo_client):
        from handlers.create_queja import lambda_handler

        bad = {
            "titulo": "Titulo valido aqui",
            "descripcion": "Descripcion valida larga",
            "categoriaDeclarada": "INVALIDA",
        }
        event = api_event(method="POST", path="/api/quejas", body=bad)
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 400

    def test_requires_tenant_id(self, api_event, sample_queja, dynamo_client):
        from src.handlers.create_queja import lambda_handler

        # Explicitly set headers to None/empty so X-Tenant-ID is missing
        event = api_event(
            method="POST",
            path="/api/quejas",
            body=sample_queja,
        )
        # Remove X-Tenant-ID header
        del event["headers"]["X-Tenant-ID"]
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert body["code"] == "UNAUTHORIZED"


class TestGetQueja:
    def test_get_existing(self, api_event, dynamo_client):
        from handlers.get_queja import lambda_handler

        dynamo_client.put_item(
            {
                "pk": "TENANT#test-tenant#QUEJA#q-1",
                "sk": "QUEJA#q-1",
                "quejaId": "q-1",
                "tenantId": "test-tenant",
                "titulo": "Test titulo valido",
                "descripcion": "Descripcion valida de al menos 20 chars",
                "categoriaDeclarada": "OTRA",
                "status": "PENDIENTE",
                "createdAt": "2026-01-01T00:00:00",
                "updatedAt": "2026-01-01T00:00:00",
            }
        )
        event = api_event(
            method="GET",
            path="/api/quejas/q-1",
            path_params={"quejaId": "q-1"},
        )
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["quejaId"] == "q-1"
        assert "pk" not in body  # internal field excluded
        assert "sk" not in body

    def test_get_not_found(self, api_event, dynamo_client):
        from handlers.get_queja import lambda_handler

        event = api_event(
            method="GET",
            path="/api/quejas/missing",
            path_params={"quejaId": "missing"},
        )
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["code"] == "NOT_FOUND"

    def test_get_tenant_isolation(self, api_event, dynamo_client):
        """Queja in tenant A should not be accessible from tenant B."""
        from handlers.get_queja import lambda_handler

        # Insert queja in tenant A
        dynamo_client.put_item(
            {
                "pk": "TENANT#tenant-a#QUEJA#q-1",
                "sk": "QUEJA#q-1",
                "quejaId": "q-1",
                "tenantId": "tenant-a",
                "titulo": "Titulo valido aqui",
                "descripcion": "Descripcion valida de al menos 20 caracteres",
                "categoriaDeclarada": "OTRA",
                "status": "PENDIENTE",
                "createdAt": "2026-01-01",
                "updatedAt": "2026-01-01",
            }
        )
        # Try to access from tenant B
        event = api_event(
            method="GET",
            path="/api/quejas/q-1",
            path_params={"quejaId": "q-1"},
            headers={"X-Tenant-ID": "tenant-b"},
        )
        result = lambda_handler(event, context={})
        assert result["statusCode"] == 404  # Not found for tenant B


class TestListQuejas:
    def test_list_empty(self, api_event, dynamo_client):
        from handlers.list_quejas import lambda_handler

        event = api_event(method="GET", path="/api/quejas")
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["items"] == []
        assert body["total"] == 0

    def test_list_with_items(self, api_event, dynamo_client):
        from handlers.list_quejas import lambda_handler

        for i in range(3):
            dynamo_client.put_item(
                {
                    "pk": f"TENANT#test-tenant#QUEJA#q-{i}",
                    "sk": f"QUEJA#q-{i}",
                    "quejaId": f"q-{i}",
                    "tenantId": "test-tenant",
                    "status": "PENDIENTE",
                }
            )

        event = api_event(method="GET", path="/api/quejas")
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["total"] == 3
        assert len(body["items"]) == 3


class TestChat:
    def test_chat_returns_answer_and_sources(
        self, api_event, sample_chat_request
    ):
        from handlers.chat import lambda_handler

        event = api_event(method="POST", path="/api/chat", body=sample_chat_request)
        result = lambda_handler(event, context={})

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "answer" in body
        assert "sources" in body
        assert len(body["sources"]) > 0
        # Each source has the required fields
        for s in body["sources"]:
            assert "id" in s
            assert "title" in s
            assert "content" in s
            assert "score" in s

    def test_chat_validation_error_short_question(self, api_event):
        from handlers.chat import lambda_handler

        event = api_event(
            method="POST",
            path="/api/chat",
            body={"question": "abc"},  # too short
        )
        result = lambda_handler(event, context={})
        assert result["statusCode"] == 400

    def test_chat_requires_tenant(self, api_event, sample_chat_request):
        from src.handlers.chat import lambda_handler

        event = api_event(
            method="POST",
            path="/api/chat",
            body=sample_chat_request,
        )
        del event["headers"]["X-Tenant-ID"]
        result = lambda_handler(event, context={})
        assert result["statusCode"] == 401
