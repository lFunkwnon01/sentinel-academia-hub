"""Tests for tenant_config_service: per-tenant config loading and routing."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from services.tenant_config_service import (
    DEFAULT_TENANT_CONFIG,
    get_recipients,
    get_tenant_config,
    should_notify,
)


@pytest.fixture
def utec_config():
    return {
        "name": "UTEC",
        "emails": {
            "BIENESTAR": "bienestar@utec.edu.ec",
            "DIRECCION": "direccion@utec.edu.ec",
            "SEGURIDAD": "seguridad@utec.edu.ec",
            "DEFAULT": "sentinel@utec.edu.ec",
        },
        "threshold": 6,
    }


class TestGetTenantConfig:
    def test_loads_from_s3(self, utec_config, s3):
        """When config exists in S3, return it."""
        s3.put_object(
            Bucket="sentinel-files-test",
            Key="tenants/demo-utec/config.json",
            Body=json.dumps(utec_config),
        )
        with patch("services.tenant_config_service.get_settings") as m:
            m.return_value.files_bucket_resolved = "sentinel-files-test"
            config = get_tenant_config("demo-utec")
        assert config["name"] == "UTEC"
        assert config["emails"]["BIENESTAR"] == "bienestar@utec.edu.ec"

    def test_returns_defaults_when_missing(self, s3):
        """When config doesn't exist, return defaults."""
        with patch("services.tenant_config_service.get_settings") as m:
            m.return_value.files_bucket_resolved = "sentinel-files-test"
            config = get_tenant_config("unknown-tenant")
        assert config == DEFAULT_TENANT_CONFIG


class TestShouldNotify:
    def test_below_threshold_no_notify(self):
        """Prioridad below threshold = no notification."""
        analysis = {"prioridad": 3, "requiereNotificacionInmediata": False}
        assert should_notify("demo-utec", analysis) is False

    def test_above_threshold_notifies(self):
        """Prioridad >= threshold = notify."""
        analysis = {"prioridad": 7, "requiereNotificacionInmediata": False}
        assert should_notify("demo-utec", analysis) is True

    def test_immediate_notification_always(self):
        """requiereNotificacionInmediata = True, even low prioridad."""
        analysis = {"prioridad": 1, "requiereNotificacionInmediata": True}
        assert should_notify("demo-utec", analysis) is True


class TestGetRecipients:
    def test_acoso_routes_to_bienestar_seguridad(self):
        config = {
            "emails": {
                "BIENESTAR": "b@test.edu",
                "DIRECCION": "d@test.edu",
                "SEGURIDAD": "s@test.edu",
                "DEFAULT": "def@test.edu",
            }
        }
        with patch("services.tenant_config_service.get_tenant_config", return_value=config):
            recipients = get_recipients("demo-utec", "ACOSO")
        assert "b@test.edu" in recipients
        assert "s@test.edu" in recipients
        assert "d@test.edu" not in recipients  # ACOSO goes to bienestar+seguridad, not direccion

    def test_infraestructura_routes_to_direccion(self):
        config = {
            "emails": {
                "BIENESTAR": "b@test.edu",
                "DIRECCION": "d@test.edu",
                "DEFAULT": "def@test.edu",
            }
        }
        with patch("services.tenant_config_service.get_tenant_config", return_value=config):
            recipients = get_recipients("demo-utec", "INFRAESTRUCTURA")
        assert "d@test.edu" in recipients
        assert "b@test.edu" not in recipients
