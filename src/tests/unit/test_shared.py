"""Tests for the _shared modules."""

from __future__ import annotations

import json


class TestConfig:
    def test_default_values(self):
        from handlers._shared.config import Settings, get_settings

        get_settings.cache_clear()
        s = Settings()
        assert s.app_name == "sentinel-academia"
        assert s.region == "us-east-1"
        assert "stage" in s.dynamodb_table

    def test_dynamodb_table_resolved(self):
        from handlers._shared.config import Settings, get_settings

        get_settings.cache_clear()
        s = Settings()
        # Default stage is "dev"
        assert s.dynamodb_table_resolved == "sentinel-quejas-dev"


class TestCorrelationId:
    def test_with_correlation_id(self):
        from handlers._shared.correlation_id import (
            get_correlation_id,
            with_correlation_id,
        )

        event = {"headers": {"x-correlation-id": "abc-123"}}
        with_correlation_id(event)
        assert get_correlation_id() == "abc-123"

    def test_generates_uuid_if_missing(self):
        import re

        from handlers._shared.correlation_id import (
            get_correlation_id,
            with_correlation_id,
        )

        event = {"headers": {}}
        with_correlation_id(event)
        cid = get_correlation_id()
        assert cid is not None
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", cid
        )


class TestHttpResponse:
    def test_ok(self):
        from handlers._shared.http_response import HttpResponse

        r = HttpResponse.ok({"foo": "bar"})
        assert r["statusCode"] == 200
        assert json.loads(r["body"]) == {"foo": "bar"}
        assert "Content-Type" in r["headers"]
        assert r["headers"]["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in r["headers"]

    def test_accepted(self):
        from handlers._shared.http_response import HttpResponse

        r = HttpResponse.accepted({"quejaId": "q-123"})
        assert r["statusCode"] == 202

    def test_no_content(self):
        from handlers._shared.http_response import HttpResponse

        r = HttpResponse.no_content()
        assert r["statusCode"] == 204
        assert r["body"] == ""

    def test_error_response_format(self):
        from handlers._shared.http_response import build_error_response

        r = build_error_response(400, "VALIDATION_ERROR", "Bad input", {"field": "x"})
        assert r["statusCode"] == 400
        body = json.loads(r["body"])
        assert body["code"] == "VALIDATION_ERROR"
        assert body["message"] == "Bad input"
        assert "timestamp" in body
        assert "correlationId" in body
        assert body["details"] == {"field": "x"}


class TestErrors:
    def test_app_error_defaults(self):
        from handlers._shared.errors import AppError

        e = AppError("oops")
        assert e.status_code == 500
        assert e.error_code == "INTERNAL_ERROR"
        assert e.message == "oops"
        assert e.details == {}

    def test_validation_error(self):
        from handlers._shared.errors import ValidationError

        e = ValidationError("bad", details={"field": "x"})
        assert e.status_code == 400
        assert e.error_code == "VALIDATION_ERROR"
        assert e.details == {"field": "x"}

    def test_unauthorized(self):
        from handlers._shared.errors import UnauthorizedError

        e = UnauthorizedError()
        assert e.status_code == 401

    def test_not_found(self):
        from handlers._shared.errors import NotFoundError

        e = NotFoundError()
        assert e.status_code == 404


class TestSchemas:
    def test_queja_create_valid(self):
        from handlers._shared.schemas import CategoriaEnum, QuejaCreate

        q = QuejaCreate(
            titulo="Test title here",
            descripcion="This is a description that is long enough",
            categoriaDeclarada="ACADEMICA",
        )
        assert q.titulo == "Test title here"
        assert q.categoriaDeclarada == CategoriaEnum.ACADEMICA

    def test_queja_create_too_short(self):
        import pytest
        from pydantic import ValidationError as PydanticValidationError

        from handlers._shared.schemas import QuejaCreate

        with pytest.raises(PydanticValidationError):
            QuejaCreate(titulo="abc", descripcion="too short")

    def test_queja_create_invalid_categoria(self):
        import pytest
        from pydantic import ValidationError as PydanticValidationError

        from handlers._shared.schemas import QuejaCreate

        with pytest.raises(PydanticValidationError):
            QuejaCreate(
                titulo="Test title here",
                descripcion="This is a description that is long enough",
                categoriaDeclarada="INVALIDA",
            )

    def test_queja_response_serialization(self):
        from handlers._shared.schemas import (
            CategoriaEnum,
            QuejaResponse,
            QuejaStatus,
        )

        q = QuejaResponse(
            quejaId="q-1",
            tenantId="t-1",
            titulo="Test titulo aqui",  # >=5 chars
            descripcion="Descripcion larga valida",  # >=20 chars
            categoriaDeclarada=CategoriaEnum.ACADEMICA,
            status=QuejaStatus.PENDIENTE,
            createdAt="2026-01-01T00:00:00",
            updatedAt="2026-01-01T00:00:00",
        )
        d = q.model_dump(mode="json")
        assert d["quejaId"] == "q-1"
        assert d["categoriaDeclarada"] == "ACADEMICA"
        assert d["status"] == "PENDIENTE"

    def test_chat_request_min_length(self):
        import pytest
        from pydantic import ValidationError as PydanticValidationError

        from handlers._shared.schemas import ChatRequest

        with pytest.raises(PydanticValidationError):
            ChatRequest(question="abc")  # too short

    def test_sqs_message_valid(self):
        from handlers._shared.schemas import SQSCreateQuejaMessage

        m = SQSCreateQuejaMessage(quejaId="q-1", tenantId="t-1")
        assert m.quejaId == "q-1"
        assert m.correlationId is None
