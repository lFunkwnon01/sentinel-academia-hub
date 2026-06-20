"""LLM client wrapper for OCI Cohere (with mock fallback for Lambda).

For production:
- Use OCI_INSTANCE_PRINCIPAL auth in Lambda
- Or use a Lambda Layer with a slim oci build
- Or call OCI via API Gateway proxy

For hackathon demo:
- MockLLMClient returns rule-based analysis (no external dep)
- RealLLMClient calls OCI Cohere (for local use)

Toggle: MOCK_LLM env var (default: "true" in Lambda, "false" locally)
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any

from handlers._shared.config import get_settings
from handlers._shared.errors import AppError
from handlers._shared.logger import get_logger
from handlers._shared.schemas import Analisis, QuejaResponse

log = get_logger(__name__)


SYSTEM_PROMPT = """Eres un asistente especializado en analizar quejas universitarias.
Devuelve SOLO JSON v\u00e1lido con esta estructura:

{
  "categoria": "ACADEMICA" | "INFRAESTRUCTURA" | "ACOSO" | "ADMINISTRATIVA" | "SALUD" | "OTRA",
  "subcategoria": "string corto",
  "criticidad": "BAJA" | "MEDIA" | "ALTA" | "CRITICA",
  "criticidadJustificacion": "string (1-2 oraciones)",
  "sentimiento": "POSITIVO" | "NEUTRO" | "NEGATIVO" | "NEGATIVO_FUERTE",
  "entidades": [{"tipo": "string", "texto": "string"}],
  "temasClave": ["tema1", "tema2"],
  "accionSugerida": "string (1-2 oraciones)",
  "prioridad": 1-10,
  "requiereNotificacionInmediata": true | false,
  "confidence": 0.0-1.0
}

Criticidad:
- BAJA: problemas menores
- MEDIA: requieren atenci\u00f3n
- ALTA: afectan a varios
- CRITICA: requiere notificaci\u00f3n INMEDIATA (acoso, violencia)"""


class LLMError(AppError):
    """Error calling the LLM service."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="LLM_UNAVAILABLE",
            details=details,
        )


# ============================================================================
# Mock LLM (rule-based, no external dep)
# ============================================================================


class MockLLMClient:
    """Mock LLM that returns rule-based analysis.

    Uses keyword matching on the queja text to determine categoria, criticidad, etc.
    Production would use a real LLM (OCI Cohere or similar).
    """

    KEYWORD_MAP = {
        "ACOSO": (["acoso", "acoso", "ofensiv", "agresi", "violencia", "amenaza", "hostig"], "CRITICA", 10),
        "SALUD": (["suicid", "depres", "ansiedad", "salud mental", "p\u00e1nico"], "CRITICA", 9),
        "INFRAESTRUCTURA": (["aula", "edificio", "baño", "techo", "inund", "filtr", "electric", "dañado", "roto"], "MEDIA", 5),
        "ACADEMICA": (["profesor", "docente", "calificaci\u00f3n", "examen", "tarea", "clase", "matrícula acad"], "MEDIA", 6),
        "ADMINISTRATIVA": (["matr\u00edcula", "inscripci\u00f3n", "tr\u00e1mite", "sistema", "pago", "factur", "becas"], "MEDIA", 5),
    }

    def analyze_queja(self, queja: QuejaResponse) -> Analisis:
        """Rule-based analysis (mock)."""
        start = time.time()
        text = f"{queja.titulo} {queja.descripcion}".lower()

        # Detect categoria
        best_match = ("OTRA", [], "BAJA", 3)
        for cat, (keywords, crit, prio) in self.KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0 and (best_match[0] == "OTRA" or score > best_match[3]):
                best_match = (cat, keywords, crit, prio)

        categoria_str, _keywords, criticidad_str, prioridad = best_match

        # Detect sentimiento
        if any(w in text for w in ["terrible", "horrible", "inaceptable", "urgente", "peligro"]):
            sentimiento = "NEGATIVO_FUERTE"
        elif any(w in text for w in ["mal", "malo", "problema", "falla", "error", "no funciona"]):
            sentimiento = "NEGATIVO"
        elif any(w in text for w in ["gracias", "feliz", "contento", "bien"]):
            sentimiento = "POSITIVO"
        else:
            sentimiento = "NEUTRO"

        # Extract entidades (capitalized words)
        entidades = []
        for word in queja.descripcion.split():
            if word and word[0].isupper() and len(word) > 3 and word.isalpha():
                entidades.append({"tipo": "MENCION", "texto": word})
                if len(entidades) >= 5:
                    break

        # Temas clave
        temas = []
        for cat, (keywords, _, _) in self.KEYWORD_MAP.items():
            for kw in keywords[:2]:
                if kw in text:
                    temas.append(kw)
        temas = list(set(temas))[:5]

        # Accion sugerida
        if criticidad_str == "CRITICA":
            accion = "Notificar a BIENESTAR y SEGURIDAD inmediatamente. Escalar a direcci\u00f3n."
            requiere = True
        elif criticidad_str == "ALTA":
            accion = "Revisar con la autoridad competente. Programar reuni\u00f3n en 48h."
            requiere = True
        elif criticidad_str == "MEDIA":
            accion = "Asignar a comit\u00e9 acad\u00e9mico. Responder en 5 d\u00edas h\u00e1biles."
            requiere = False
        else:
            accion = "Archivo informativo. Responder confirmando recepci\u00f3n."
            requiere = False

        latency_ms = int((time.time() - start) * 1000)

        from handlers._shared.schemas import (
            Analisis,
            CategoriaEnum,
            CriticidadEnum,
            SentimientoEnum,
        )

        return Analisis(
            categoria=CategoriaEnum(categoria_str),
            subcategoria=categoria_str.lower() if categoria_str != "OTRA" else None,
            criticidad=CriticidadEnum(criticidad_str),
            criticidadJustificacion=(
                f"Detectadas palabras clave de {categoria_str}. Prioridad {prioridad}/10."
            ),
            sentimiento=SentimientoEnum(sentimiento),
            entidades=entidades,
            temasClave=temas,
            accionSugerida=accion,
            prioridad=prioridad,
            requiereNotificacionInmediata=requiere,
            modeloUsado="mock-rule-based-v1",
            tokensConsumidos=len(text.split()),
            latenciaMs=latency_ms,
            confidence=0.75,
            generatedAt=datetime.now(timezone.utc).isoformat(),
        )


# ============================================================================
# Real LLM (OCI Cohere) - for local use only
# ============================================================================


class RealLLMClient:
    """Real LLM using OCI Cohere. Requires `oci` package and OCI config."""

    def __init__(self) -> None:
        import oci
        from oci.generative_ai_inference import GenerativeAiInferenceClient
        from oci.generative_ai_inference import models as inference_models

        settings = get_settings()
        self.compartment_id = settings.oci_compartment_id
        self.model_ocid = settings.oci_cohere_model_ocid
        self.region = settings.oci_region

        if not self.compartment_id:
            raise LLMError("OCI_COMPARTMENT_ID not configured")
        if not self.model_ocid:
            raise LLMError("OCI_COHERE_MODEL_OCID not configured")

        self.config = oci.config.from_file(settings.oci_key_file, "DEFAULT")
        if settings.oci_user_ocid:
            self.config["user"] = settings.oci_user_ocid
        if settings.oci_tenancy_ocid:
            self.config["tenancy"] = settings.oci_tenancy_ocid
        if settings.oci_fingerprint:
            self.config["fingerprint"] = settings.oci_fingerprint

        self._client = GenerativeAiInferenceClient(
            self.config,
            service_endpoint=f"https://inference.generativeai.{self.region}.oci.oraclecloud.com",
        )
        self._inference_models = inference_models

    def analyze_queja(self, queja: QuejaResponse) -> Analisis:
        import oci

        user_prompt = self._build_user_prompt(queja)
        start = time.time()

        try:
            chat_request = self._inference_models.CohereChatRequest(
                message=user_prompt,
                max_tokens=800,
                temperature=0.2,
                is_stream=False,
            )
            details = self._inference_models.ChatDetails(
                compartment_id=self.compartment_id,
                serving_mode=self._inference_models.OnDemandServingMode(
                    model_id=self.model_ocid
                ),
                chat_request=chat_request,
            )
            response = self._client.chat(details)
            latency_ms = int((time.time() - start) * 1000)
            text = response.data.chat_response.text
            tokens = response.data.chat_response.usage.total_tokens or 0
        except oci.exceptions.ServiceError as e:
            log.error("OCI Cohere call failed", extra={"error": str(e)})
            raise LLMError(
                f"OCI Cohere call failed: {e.message}",
                details={"status": e.status},
            ) from e

        analysis_dict = self._parse_json_response(text)
        analysis_dict.update(
            {
                "modeloUsado": "cohere.command-latest",
                "tokensConsumidos": tokens,
                "latenciaMs": latency_ms,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            }
        )
        return Analisis(**analysis_dict)

    def _build_user_prompt(self, queja: QuejaResponse) -> str:
        parts = [
            f"T\u00edtulo: {queja.titulo}",
            f"Descripci\u00f3n: {queja.descripcion}",
            f"Categor\u00eda declarada: {queja.categoriaDeclarada.value}",
        ]
        if queja.sede:
            parts.append(f"Sede: {queja.sede}")
        if queja.facultad:
            parts.append(f"Facultad: {queja.facultad}")
        parts.append("\nDevuelve SOLO el JSON.")
        return "\n".join(parts)

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object in response: {text[:200]}")
        return json.loads(text[start : end + 1])


# ============================================================================
# Factory
# ============================================================================

_client: MockLLMClient | RealLLMClient | None = None


def get_llm_client() -> MockLLMClient | "HTTPRealLLMClient":
    """Get LLM client (mock by default, real via HTTP for Lambda).

    Toggle: MOCK_LLM env var
    - "true" (default in Lambda): MockLLMClient
    - "false": HTTPRealLLMClient (uses oci_http_client, no SDK needed)
    """
    global _client
    if _client is not None:
        return _client

    use_mock = os.environ.get("MOCK_LLM", "true").lower() != "false"
    if use_mock:
        log.info("Using MockLLMClient (rule-based)")
        _client = MockLLMClient()
    else:
        log.info("Using HTTPRealLLMClient (OCI Cohere via direct HTTP)")
        # Import here to avoid circular imports
        from services.oci_http_client import call_oci_cohere_chat
        from handlers._shared.config import get_settings

        class HTTPRealLLMClient:
            """Real LLM client using OCI Cohere via direct HTTP (no SDK)."""
            def __init__(self) -> None:
                self._settings = get_settings()

            def analyze_queja(self, queja):
                return _analyze_queja_http(queja, self._settings)

            def _call_cohere(self, message, preamble, max_tokens=800, temperature=0.2):
                s = self._settings
                result = call_oci_cohere_chat(
                    user_ocid=s.oci_user_ocid or "",
                    tenancy_ocid=s.oci_tenancy_ocid or "",
                    fingerprint=s.oci_fingerprint or "",
                    key_file=s.oci_key_file,
                    compartment_id=s.oci_compartment_id or "",
                    model_ocid=(
                        s.oci_cohere_model_ocid
                        or "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyalrfnqiqipm3xn4yy2r2fww32yidtopep6rg2uupd3i2a"
                    ),
                    region=s.oci_region,
                    message=message,
                    preamble=preamble,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                payload = result["payload"]
                cr = payload.get("chatResponse", payload.get("chat_response", payload))
                return (cr.get("text") or "", cr.get("usage") or {}, result["latency_ms"])

        _client = HTTPRealLLMClient()
    return _client


def _analyze_queja_http(queja, settings) -> "Analisis":
    """Analyze a queja using Cohere via HTTP and parse the structured JSON."""
    from handlers._shared.schemas import Analisis
    from datetime import datetime, timezone

    system_prompt = (
        "Eres un asistente que analiza quejas universitarias. "
        "Responde SOLO con un JSON v\u00e1lido con esta estructura:\n"
        '{"categoria": "ACADEMICA|INFRAESTRUCTURA|ACOSO|ADMINISTRATIVA|SALUD|OTRA",'
        '"subcategoria": "string",'
        '"criticidad": "BAJA|MEDIA|ALTA|CRITICA",'
        '"criticidadJustificacion": "string (1-2 oraciones)",'
        '"sentimiento": "POSITIVO|NEUTRO|NEGATIVO|NEGATIVO_FUERTE",'
        '"entidades": [{"tipo": "string", "texto": "string"}],'
        '"temasClave": ["tema1", "tema2"],'
        '"accionSugerida": "string (1-2 oraciones)",'
        '"prioridad": 1-10,'
        '"requiereNotificacionInmediata": true|false,'
        '"confidence": 0.0-1.0}'
    )
    user_prompt = (
        f"Titulo: {queja.titulo}\n"
        f"Descripcion: {queja.descripcion}\n"
        f"Categoria declarada: {queja.categoriaDeclarada.value}\n"
        f"\nDevuelve SOLO el JSON."
    )

    from services.oci_http_client import call_oci_cohere_chat

    result = call_oci_cohere_chat(
        user_ocid=settings.oci_user_ocid or "",
        tenancy_ocid=settings.oci_tenancy_ocid or "",
        fingerprint=settings.oci_fingerprint or "",
        key_file=settings.oci_key_file,
        compartment_id=settings.oci_compartment_id or "",
        model_ocid=(
            settings.oci_cohere_model_ocid
            or "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyalrfnqiqipm3xn4yy2r2fww32yidtopep6rg2uupd3i2a"
        ),
        region=settings.oci_region,
        message=user_prompt,
        preamble=system_prompt,
        max_tokens=600,
        temperature=0.2,
    )
    payload = result["payload"]
    cr = payload.get("chatResponse", payload.get("chat_response", payload))
    text = (cr.get("text") or "").strip()
    usage = cr.get("usage") or {}
    tokens = usage.get("totalTokens") or usage.get("total_tokens") or 0
    latency_ms = result["latency_ms"]

    # Parse JSON from the text
    text_clean = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text_clean = re.sub(r"\s*```$", "", text_clean)
    start = text_clean.find("{")
    end = text_clean.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON in Cohere response: {text[:200]}")
    analysis_dict = json.loads(text_clean[start : end + 1])
    analysis_dict.update({
        "modeloUsado": "cohere.command-latest",
        "tokensConsumidos": tokens,
        "latenciaMs": latency_ms,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    })
    return Analisis(**analysis_dict)
