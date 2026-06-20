"""Shared utilities for all Lambda handlers in Sentinel AcademIA."""

from handlers._shared.config import Settings, get_settings
from handlers._shared.logger import get_logger
from handlers._shared.errors import (
    AppError,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    error_handler,
)
from handlers._shared.http_response import (
    HttpResponse,
    build_response,
    build_error_response,
)
from handlers._shared.correlation_id import (
    get_correlation_id,
    with_correlation_id,
)
from handlers._shared.dynamo_client import DynamoClient, get_dynamo_client
from handlers._shared.schemas import (
    QuejaBase,
    QuejaCreate,
    QuejaResponse,
    QuejaStatus,
)
from handlers._shared.auth import extract_tenant_id

__all__ = [
    "Settings",
    "get_settings",
    "get_logger",
    "AppError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "error_handler",
    "HttpResponse",
    "build_response",
    "build_error_response",
    "get_correlation_id",
    "with_correlation_id",
    "DynamoClient",
    "get_dynamo_client",
    "QuejaBase",
    "QuejaCreate",
    "QuejaResponse",
    "QuejaStatus",
    "extract_tenant_id",
]
