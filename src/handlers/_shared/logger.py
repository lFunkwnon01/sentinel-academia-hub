"""Structured logger using aws-lambda-powertools.

Rules:
- NEVER use print() - always logger
- Logger must include correlation_id automatically
- All log levels: DEBUG, INFO, WARNING, ERROR
"""

from __future__ import annotations

from aws_lambda_powertools import Logger

from handlers._shared.config import get_settings

# Module-level cached loggers (one per name)
_loggers: dict[str, Logger] = {}


def get_logger(name: str) -> Logger:
    """Get a powertools logger with project defaults.

    Usage:
        from handlers._shared.logger import get_logger
        log = get_logger(__name__)
        log.info("Processing queja", extra={"queja_id": "q123"})
    """
    if name in _loggers:
        return _loggers[name]

    settings = get_settings()
    logger = Logger(
        service=settings.app_name,
        level=settings.log_level,
        # Include correlation_id and tenant_id in every log if present
        owner="sentinel-academia",
    )
    _loggers[name] = logger
    return logger
