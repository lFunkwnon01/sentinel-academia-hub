"""Pydantic schemas for Quejas (complaints).

Aligned with api-mock/openapi.yaml spec.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class QuejaStatus(StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_COLA = "EN_COLA"
    PROCESANDO = "PROCESANDO"
    ANALIZADA = "ANALIZADA"
    NOTIFICADA = "NOTIFICADA"
    ERROR = "ERROR"


class CategoriaEnum(StrEnum):
    ACADEMICA = "ACADEMICA"
    INFRAESTRUCTURA = "INFRAESTRUCTURA"
    ACOSO = "ACOSO"
    ADMINISTRATIVA = "ADMINISTRATIVA"
    SALUD = "SALUD"
    OTRA = "OTRA"


class CriticidadEnum(StrEnum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class SentimientoEnum(StrEnum):
    POSITIVO = "POSITIVO"
    NEUTRO = "NEUTRO"
    NEGATIVO = "NEGATIVO"
    NEGATIVO_FUERTE = "NEGATIVO_FUERTE"


# --- Entidad detectada por LLM ---
class Entidad(BaseModel):
    tipo: str
    texto: str


# --- Resultado del analisis LLM (alineado con OpenAPI Analisis) ---
class Analisis(BaseModel):
    categoria: CategoriaEnum
    subcategoria: str | None = None
    criticidad: CriticidadEnum
    criticidadJustificacion: str | None = None
    sentimiento: SentimientoEnum
    entidades: list[Entidad] = Field(default_factory=list)
    temasClave: list[str] = Field(default_factory=list)
    accionSugerida: str
    prioridad: int = Field(ge=1, le=10)
    requiereNotificacionInmediata: bool = False
    modeloUsado: str = "cohere.command-latest"
    tokensConsumidos: int = 0
    latenciaMs: int = 0
    confidence: float = Field(ge=0, le=1, default=0.0)
    generatedAt: str


# --- DTOs ---


class QuejaBase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        frozen=False,
        use_enum_values=False,
    )

    titulo: Annotated[str, Field(min_length=5, max_length=120)]
    descripcion: Annotated[str, Field(min_length=20, max_length=5000)]
    categoriaDeclarada: CategoriaEnum = Field(default=CategoriaEnum.OTRA)
    adjuntos: list[str] = Field(default_factory=list, max_length=5)
    anonima: bool = Field(default=False)
    sede: str | None = Field(default=None, max_length=100)
    facultad: str | None = Field(default=None, max_length=100)
    contactoEmail: EmailStr | None = Field(default=None)
    contactoTelefono: str | None = Field(
        default=None, pattern=r"^\+?[0-9\s\-]{7,20}$"
    )
    cursoCodigo: str | None = Field(
        default=None, max_length=20,
        description="C\u00f3digo del curso (requerido si categoria=ACADEMICA)",
    )

    @field_validator("adjuntos")
    @classmethod
    def validate_s3_urls(cls, v: list[str]) -> list[str]:
        for url in v:
            if not url.startswith("https://") or ".s3." not in url:
                raise ValueError(f"Invalid S3 URL: {url}")
        return v

    @field_validator("cursoCodigo", "contactoEmail")
    @classmethod
    def validate_category_requirements(cls, v, info):
        """Enforce business rules: email required for sensitive categories,
        course code required for ACADEMICA."""
        # We don't have categoria here - validation done at handler level
        return v


class QuejaCreate(QuejaBase):
    pass


class QuejaAccepted(BaseModel):
    quejaId: str = Field(default_factory=lambda: str(uuid4()))
    status: QuejaStatus = QuejaStatus.PENDIENTE
    correlationId: str
    createdAt: str
    estimatedAnalysisTime: int = 30


class QuejaResponse(QuejaBase):
    quejaId: str = Field(default_factory=lambda: f"q-{uuid4().hex[:12]}")
    tenantId: str
    status: QuejaStatus = QuejaStatus.PENDIENTE
    userId: str | None = None
    createdAt: str
    updatedAt: str
    analysis: Analisis | None = None
    escalada: bool = False
    escalaAt: str | None = None

    @classmethod
    def from_dynamo(cls, item: dict[str, Any]) -> QuejaResponse:
        data = {k: v for k, v in item.items() if k not in {"pk", "sk"}}
        for field, enum_cls in (
            ("categoriaDeclarada", CategoriaEnum),
            ("status", QuejaStatus),
        ):
            if field in data and isinstance(data[field], str):
                data[field] = enum_cls(data[field])
        if data.get("analysis") and isinstance(data["analysis"], dict):
            data["analysis"] = Analisis(**data["analysis"])
        return cls(**data)


# --- SQS message format ---
class SQSCreateQuejaMessage(BaseModel):
    """SQS message body for analysis."""

    quejaId: str
    tenantId: str
    correlationId: str | None = None


# --- Chat (RAG) ---
class ChatRequest(BaseModel):
    """POST /api/chat - User question for the RAG-powered chatbot."""

    question: str = Field(min_length=5, max_length=1000, description="User question")
    context: str | None = Field(
        default="TODOS",
        description="Which knowledge base to search: REGLAMENTO, QUEJAS, TODOS",
    )
    conversationId: str | None = Field(
        default=None, description="Conversation ID for multi-turn (future)"
    )


class ChatSource(BaseModel):
    """Source document referenced in the answer."""

    id: str
    title: str
    content: str
    score: float = Field(ge=0, le=1)
    page: int | None = None
    source: str | None = None


class ChatResponse(BaseModel):
    """Response from /api/chat."""

    answer: str
    sources: list[ChatSource] = Field(default_factory=list)
    conversationId: str | None = None
    modeloUsado: str
    tokensUsados: int = 0
    latenciaMs: int = 0
