"""Shared pytest fixtures for all tests."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import boto3
import pytest


# ============================================================
# Environment fixtures
# ============================================================


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """Set required env vars for all tests (Settings is cached)."""
    monkeypatch.setenv("STAGE", "dev")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")  # Less noise in tests
    monkeypatch.setenv("MOCK_LLM", "true")  # Always use mock in tests
    monkeypatch.setenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..test")
    monkeypatch.setenv("OCI_COHERE_MODEL_OCID", "ocid1.generativeaimodel.oc1..test")
    # Clear cache so Settings reloads with test env
    from handlers._shared.config import get_settings

    get_settings.cache_clear()
    yield


# ============================================================
# AWS fixtures (using moto)
# ============================================================


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mock AWS credentials so moto doesn't complain."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def dynamodb(aws_credentials):
    """Create a mocked DynamoDB with the QuejasTable."""
    from moto import mock_aws
    from handlers._shared.config import get_settings

    with mock_aws():
        # Get the resolved table name (matches what the client will use)
        table_name = get_settings().dynamodb_table_resolved

        # Create the table
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        table = ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "gsi1pk", "AttributeType": "S"},
                {"AttributeName": "gsi1sk", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1-StatusByDate",
                    "KeySchema": [
                        {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield ddb


@pytest.fixture
def s3(aws_credentials):
    """Create a mocked S3 with the FilesBucket."""
    from moto import mock_aws

    with mock_aws():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="sentinel-files-test")
        yield s3_client


@pytest.fixture
def sqs(aws_credentials):
    """Create a mocked SQS with the AnalysisQueue."""
    from moto import mock_aws

    with mock_aws():
        sqs_client = boto3.client("sqs", region_name="us-east-1")
        queue = sqs_client.create_queue(QueueName="sentinel-analysis-test")
        yield sqs_client


@pytest.fixture
def dynamo_client(dynamodb):
    """Get the dynamo_client singleton (with mocked AWS)."""
    import handlers._shared.dynamo_client as dc_module

    # Reset the singleton
    dc_module._client = None
    return dc_module.get_dynamo_client()


# ============================================================
# API event fixtures
# ============================================================


@pytest.fixture
def api_event():
    """Factory for API Gateway proxy events."""

    def _make(
        method: str = "GET",
        path: str = "/",
        body: dict | str | None = None,
        headers: dict | None = None,
        path_params: dict | None = None,
        query_params: dict | None = None,
    ):
        if isinstance(body, dict):
            import json

            body = json.dumps(body)
        return {
            "httpMethod": method,
            "path": path,
            "resource": path,
            "body": body,
            "headers": {
                "Content-Type": "application/json",
                "X-Tenant-ID": "test-tenant",
                "X-Correlation-ID": "test-correlation-123",
                **(headers or {}),
            },
            "pathParameters": path_params,
            "queryStringParameters": query_params,
            "requestContext": {
                "requestId": "test-request-id",
                "stage": "test",
            },
        }

    return _make


# ============================================================
# Sample data fixtures
# ============================================================


@pytest.fixture
def sample_queja():
    """Sample valid queja data."""
    return {
        "titulo": "Problema con el sistema de matriculas",
        "descripcion": "El sistema no me dejo inscribir las materias del proximo semestre, mostro error 500",
        "categoriaDeclarada": "ADMINISTRATIVA",
        "anonima": False,
        "sede": "Sede Norte",
        "facultad": "Ingenieria",
        "contactoEmail": "estudiante@utec.edu.pe",
    }


@pytest.fixture
def sample_chat_request():
    """Sample valid chat request."""
    return {
        "question": "Cuanto tiempo tengo para que se resuelva una queja critica?",
        "context": "TODOS",
    }
