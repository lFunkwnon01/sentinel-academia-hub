"""Configuration management for Lambda handlers.

Reads environment variables set by SAM template.yaml.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment configuration injected via Lambda env vars."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    # --- AWS / Infra ---
    app_name: str = Field(default="sentinel-academia")
    stage: Literal["dev", "staging", "prod"] = Field(default="dev")
    region: str = Field(default="us-east-1")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # --- DynamoDB ---
    dynamodb_table: str = Field(default="sentinel-quejas-{stage}")

    # --- SQS ---
    analysis_queue_url: str | None = Field(
        default=None,
        description="URL de la SQS queue para analisis async",
    )

    # --- S3 ---
    files_bucket: str = Field(default="sentinel-files-{stage}")

    # --- SNS ---
    alertas_topic_arn: str | None = Field(
        default=None,
        description="ARN del SNS topic para alertas criticas",
    )

    # --- OCI / LLM ---
    oci_compartment_id: str | None = Field(
        default=None,
        description="OCI compartment OCID",
    )
    oci_cohere_model_ocid: str | None = Field(
        default=None,
        description="OCI Cohere model OCID (de la Consola)",
    )
    oci_user_ocid: str | None = Field(default=None)
    oci_tenancy_ocid: str | None = Field(default=None)
    oci_fingerprint: str | None = Field(default=None)
    oci_region: str = Field(default="us-chicago-1")
    oci_key_file: str = Field(default="/home/lFunknown/.oci/private_key.pem")

    # --- Frontend ---
    allowed_origins: str = Field(default="*")

    @property
    def dynamodb_table_resolved(self) -> str:
        return self.dynamodb_table.format(stage=self.stage)

    @property
    def files_bucket_resolved(self) -> str:
        return self.files_bucket.format(stage=self.stage)

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
