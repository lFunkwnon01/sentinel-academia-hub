"""Tests for the DynamoDB client wrapper (with moto)."""

from __future__ import annotations

import pytest


class TestDynamoClient:
    def test_put_and_get(self, dynamo_client):
        dynamo_client.put_item(
            {
                "pk": "TENANT#utpl#QUEJA#q-1",
                "sk": "QUEJA#q-1",
                "quejaId": "q-1",
                "tenantId": "utpl",
                "titulo": "Test",
                "descripcion": "Descripcion test",
                "status": "PENDIENTE",
            }
        )
        item = dynamo_client.get_item(
            pk="TENANT#utpl#QUEJA#q-1", sk="QUEJA#q-1"
        )
        assert item is not None
        assert item["quejaId"] == "q-1"
        assert item["tenantId"] == "utpl"

    def test_get_queja_helper(self, dynamo_client):
        dynamo_client.put_item(
            {
                "pk": "TENANT#utpl#QUEJA#q-2",
                "sk": "QUEJA#q-2",
                "quejaId": "q-2",
                "tenantId": "utpl",
                "titulo": "X",
                "descripcion": "Y",
                "status": "PENDIENTE",
            }
        )
        item = dynamo_client.get_queja(tenant_id="utpl", queja_id="q-2")
        assert item["quejaId"] == "q-2"

    def test_get_queja_not_found(self, dynamo_client):
        from handlers._shared.errors import NotFoundError

        with pytest.raises(NotFoundError):
            dynamo_client.get_queja(tenant_id="utpl", queja_id="nope")

    def test_update_item(self, dynamo_client):
        dynamo_client.put_item(
            {
                "pk": "TENANT#utpl#QUEJA#q-3",
                "sk": "QUEJA#q-3",
                "quejaId": "q-3",
                "tenantId": "utpl",
                "status": "PENDIENTE",
            }
        )
        updated = dynamo_client.update_item(
            pk="TENANT#utpl#QUEJA#q-3",
            sk="QUEJA#q-3",
            updates={"status": "ANALIZADA"},
        )
        assert updated["status"] == "ANALIZADA"

    def test_query_by_tenant(self, dynamo_client):
        # Insert 3 quejas for utpl
        for i in range(3):
            dynamo_client.put_item(
                {
                    "pk": f"TENANT#utpl#QUEJA#q-{i}",
                    "sk": f"QUEJA#q-{i}",
                    "quejaId": f"q-{i}",
                    "tenantId": "utpl",
                    "status": "PENDIENTE",
                }
            )
        # Insert one for another tenant
        dynamo_client.put_item(
            {
                "pk": "TENANT#other#QUEJA#q-99",
                "sk": "QUEJA#q-99",
                "quejaId": "q-99",
                "tenantId": "other",
                "status": "PENDIENTE",
            }
        )

        # Query for utpl should return 3, not 4
        items = dynamo_client.query_by_tenant(tenant_id="utpl", sk_prefix="QUEJA#")
        assert len(items) == 3
        assert all(item["tenantId"] == "utpl" for item in items)

    def test_delete_item(self, dynamo_client):
        dynamo_client.put_item(
            {
                "pk": "TENANT#utpl#QUEJA#q-del",
                "sk": "QUEJA#q-del",
                "quejaId": "q-del",
                "tenantId": "utpl",
            }
        )
        dynamo_client.delete_item(
            pk="TENANT#utpl#QUEJA#q-del", sk="QUEJA#q-del"
        )
        item = dynamo_client.get_item(
            pk="TENANT#utpl#QUEJA#q-del", sk="QUEJA#q-del"
        )
        assert item is None

    def test_to_dynamo_converts_floats(self):
        from handlers._shared.dynamo_client import _to_dynamo

        # Float should become Decimal
        result = _to_dynamo({"score": 0.75})
        from decimal import Decimal

        assert isinstance(result["score"], Decimal)
        assert result["score"] == Decimal("0.75")

    def test_to_dynamo_nested(self):
        from decimal import Decimal

        from handlers._shared.dynamo_client import _to_dynamo

        result = _to_dynamo(
            {
                "items": [{"score": 0.5}, {"score": 0.8}],
                "name": "test",
            }
        )
        assert isinstance(result["items"][0]["score"], Decimal)
        assert isinstance(result["items"][1]["score"], Decimal)
        assert result["name"] == "test"  # strings pass through

    def test_tenant_pk_format(self):
        from handlers._shared.dynamo_client import queja_pk, queja_sk, tenant_pk

        assert tenant_pk("utpl") == "TENANT#utpl"
        assert (
            queja_pk("utpl", "q-1") == "TENANT#utpl#QUEJA#q-1"
        )
        assert queja_sk("q-1") == "QUEJA#q-1"
