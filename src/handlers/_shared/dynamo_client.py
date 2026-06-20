"""DynamoDB client wrapper with multi-tenant patterns.

Single-table design:
- PK pattern: TENANT#{tenantId}#QUEJA#{quejaId}
- SK pattern: QUEJA#{quejaId} or META#{meta-key}

All operations are tenant-scoped: you can NEVER access another tenant's data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.service_resource import Table

from handlers._shared.config import get_settings
from handlers._shared.errors import NotFoundError
from handlers._shared.logger import get_logger

log = get_logger(__name__)


# --- Multi-tenant key builders ---


def tenant_pk(tenant_id: str) -> str:
    """Build partition key prefix for a tenant.

    Example: tenant_pk("utpl") -> "TENANT#utpl"
    """
    return f"TENANT#{tenant_id}"


def queja_pk(tenant_id: str, queja_id: str) -> str:
    """Build full partition key for a queja.

    Example: queja_pk("utpl", "q-123") -> "TENANT#utpl#QUEJA#q-123"
    """
    return f"{tenant_pk(tenant_id)}#QUEJA#{queja_id}"


def queja_sk(queja_id: str) -> str:
    """Build sort key for a queja.

    Example: queja_sk("q-123") -> "QUEJA#q-123"
    """
    return f"QUEJA#{queja_id}"


def now_iso() -> str:
    """Get current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def _to_dynamo(value: Any) -> Any:
    """Recursively convert floats to Decimal for DynamoDB compatibility.

    DynamoDB doesn't support native Python floats. We need Decimal.
    """
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(item) for item in value]
    return value


class DynamoClient:
    """Wrapper for DynamoDB operations with multi-tenant safety."""

    def __init__(self, table_name: str | None = None) -> None:
        settings = get_settings()
        self._table_name = table_name or settings.dynamodb_table_resolved
        self._resource = boto3.resource("dynamodb")
        self._table: Table = self._resource.Table(self._table_name)

    @property
    def table_name(self) -> str:
        return self._table_name

    @property
    def table(self) -> Table:
        return self._table

    def put_item(self, item: dict[str, Any], condition_expression: str | None = None) -> None:
        """Put an item, optionally with a condition (e.g., to prevent overwrites).

        Args:
            item: The item to put (must include PK, SK)
            condition_expression: Optional condition (e.g., "attribute_not_exists(pk)")

        Raises:
            ClientError: If condition fails
        """
        kwargs: dict[str, Any] = {"Item": _to_dynamo(item)}
        if condition_expression:
            kwargs["ConditionExpression"] = condition_expression
        try:
            self._table.put_item(**kwargs)
        except ClientError as e:
            log.error(
                "DynamoDB put_item failed",
                extra={"error_code": e.response["Error"]["Code"], "table": self._table_name},
            )
            raise

    def get_item(self, pk: str, sk: str) -> dict[str, Any] | None:
        """Get a single item by PK + SK.

        Returns None if not found.
        """
        response = self._table.get_item(Key={"pk": pk, "sk": sk})
        return response.get("Item")

    def get_queja(self, tenant_id: str, queja_id: str) -> dict[str, Any]:
        """Get a queja by tenant + queja_id, or raise NotFoundError."""
        item = self.get_item(pk=queja_pk(tenant_id, queja_id), sk=queja_sk(queja_id))
        if item is None:
            raise NotFoundError(
                message=f"Queja {queja_id} not found for tenant {tenant_id}",
                details={"tenant_id": tenant_id, "queja_id": queja_id},
            )
        return item

    def query_by_tenant(
        self,
        tenant_id: str,
        sk_prefix: str | None = None,
        limit: int | None = None,
        scan_index_forward: bool = False,
    ) -> list[dict[str, Any]]:
        """Query all items for a tenant.

        Uses scan with filter expression (works reliably in moto and prod).

        Args:
            tenant_id: The tenant ID (always required)
            sk_prefix: Optional SK prefix to filter (e.g., "QUEJA#")
            limit: Max items to return
            scan_index_forward: Not used (scan doesn't support order)

        Returns:
            List of items (empty if none)
        """
        from boto3.dynamodb.conditions import Attr

        # Use scan with filter expression
        filter_expr = Attr("pk").begins_with(tenant_pk(tenant_id))
        if sk_prefix:
            filter_expr = filter_expr & Attr("sk").begins_with(sk_prefix)

        kwargs: dict[str, Any] = {"FilterExpression": filter_expr}
        if limit:
            kwargs["Limit"] = limit

        response = self._table.scan(**kwargs)
        return response.get("Items", [])

    def update_item(
        self,
        pk: str,
        sk: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an item with the given fields.

        Args:
            pk: Partition key
            sk: Sort key
            updates: Dict of field -> new value (only these fields will be updated)

        Returns:
            The updated item (full)
        """
        if not updates:
            return self.get_item(pk, sk) or {}

        # Build SET expression dynamically
        set_parts = []
        expression_values: dict[str, Any] = {}
        for i, (key, value) in enumerate(updates.items()):
            placeholder = f":val{i}"
            set_parts.append(f"#k{i} = {placeholder}")
            expression_values[placeholder] = value

        update_expr = "SET " + ", ".join(set_parts)

        response = self._table.update_item(
            Key={"pk": pk, "sk": sk},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={f"#k{i}": k for i, k in enumerate(updates.keys())},
            ExpressionAttributeValues=_to_dynamo(expression_values),
            ReturnValues="ALL_NEW",
        )
        return response.get("Attributes", {})

    def delete_item(self, pk: str, sk: str) -> None:
        """Delete an item by PK + SK."""
        self._table.delete_item(Key={"pk": pk, "sk": sk})


# --- Singleton ---


_client: DynamoClient | None = None


def get_dynamo_client() -> DynamoClient:
    """Get a cached DynamoClient instance."""
    global _client
    if _client is None:
        _client = DynamoClient()
    return _client
