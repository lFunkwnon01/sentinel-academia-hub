"""POST /api/chat - RAG-powered chat endpoint.

Flow:
1. Client sends question + optional context filter
2. Knowledge service does keyword search on reglamento
3. LLM (mock or real Cohere) generates answer with retrieved context
4. Response includes answer + sources (citations)

Aligned with api-mock/openapi.yaml ChatRequest/ChatResponse schemas.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from handlers._shared.auth import extract_tenant_id
from handlers._shared.correlation_id import clear_correlation_id, with_correlation_id
from handlers._shared.errors import error_handler, ValidationError
from handlers._shared.http_response import HttpResponse
from handlers._shared.logger import get_logger
from handlers._shared.schemas import ChatRequest, ChatResponse
from services.knowledge_service import build_context, search
from services.llm_client import get_llm_client

log = get_logger(__name__)


SYSTEM_PROMPT = """Eres un asistente virtual de la universidad Sentinel AcademIA.
Tu trabajo es responder preguntas de estudiantes y personal sobre el reglamento
de quejas universitarias, basándote SIEMPRE en el contexto proporcionado.

Reglas:
1. Responde en español, de forma clara y concisa.
2. Basa tus respuestas EXCLUSIVAMENTE en el contexto del reglamento.
3. Si el contexto no contiene la respuesta, dilo claramente.
4. Cita el artículo o capítulo relevante cuando sea posible.
5. Si la pregunta es sobre una situación personal, sugiere escalar la queja.
6. NO inventes información que no esté en el contexto."""


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        raise ValueError("Missing request body")
    if event.get("isBase64Encoded"):
        import base64

        body = base64.b64decode(body).decode("utf-8")
    if isinstance(body, str):
        return json.loads(body)
    return body


def _generate_answer_mock(question: str, context: str) -> str:
    """Mock LLM that generates natural, conversational Spanish responses.

    Uses intent detection + a knowledge base of common questions to produce
    answers that feel human, not robotic. Falls back to context citation when
    the question doesn't match a known intent.
    """
    q = question.lower().strip()

    # ---- Tiempo / plazos ----
    if any(k in q for k in ("cuanto tiempo", "cuánto tiempo", "plazo", "demora", "demora", "tarda", "cuando responden", "cuando me responden", "rapidez")):
        return (
            "El tiempo de respuesta depende de la criticidad que el sistema le asigne a tu queja:\n\n"
            "- **Quejas CRÍTICAS**: notificación inmediata (24 horas) — se escala a las autoridades.\n"
            "- **Quejas ALTAS**: hasta 3 días hábiles.\n"
            "- **Quejas MEDIAS**: hasta 5 días hábiles.\n"
            "- **Quejas BAJAS**: hasta 10 días hábiles.\n\n"
            "Si sientes que tu caso se está demorando más de lo debido, lo mejor es escalarlo desde tu panel. "
            "Cuando una queja se escala, el plazo de respuesta se reduce a 24 horas y la revisa un comité de 3 miembros."
        )

    # ---- Proceso para escalar ----
    if any(k in q for k in ("escalar", "escalamiento", "proceso de queja", "queja critica", "queja crítica", "como escalo", "como reporto", "reportar una queja")):
        return (
            "El proceso completo para escalar una queja crítica en Sentinel AcademIA es este:\n\n"
            "1. **La registras** desde el formulario de Reportar. Queda con estado *PENDIENTE*.\n"
            "2. **La IA la analiza**: detecta categoría (acoso, infraestructura, etc.) y le asigna una criticidad de BAJA a CRÍTICA.\n"
            "3. **Si es CRÍTICA**, se publica automáticamente en el topic SNS de tu universidad y se notifica a BIENESTAR, DIRECCIÓN y SEGURIDAD — cada universidad tiene su lista configurada.\n"
            "4. **Si quieres escalarla**, lo haces desde la vista de detalle de tu queja. Al escalar:\n"
            "   - Cambia a prioridad ALTA.\n"
            "   - Las autoridades tienen 24 horas para responderte.\n"
            "   - Un comité de 3 personas la revisa.\n"
            "5. **Puedes hacer seguimiento** en el Dashboard: métricas por categoría, criticidad, sede y facultad.\n\n"
            "¿Quieres que te explique cómo escalar desde la interfaz?"
        )

    # ---- Categorías ----
    if any(k in q for k in ("categoria", "categoría", "tipo de queja", "que tipos", "qué tipos", "clases de queja")):
        return (
            "Sentinel AcademIA maneja seis categorías de quejas:\n\n"
            "- **ACADÉMICA** — problemas con profesores, cursos, calificaciones.\n"
            "- **INFRAESTRUCTURA** — aulas, baños, electricidad, filtraciones.\n"
            "- **ACOSO** — hostigamiento, violencia, discriminación.\n"
            "- **ADMINISTRATIVA** — matrículas, trámites, procedimientos.\n"
            "- **SALUD** — salud mental, bienestar, apoyo psicológico.\n"
            "- **OTRA** — cualquier otro motivo que no encaje en las anteriores.\n\n"
            "Al reportar, tú eliges la categoría y el sistema la confirma o ajusta según el contenido. "
            "Para temas sensibles como ACOSO o SALUD, las notificaciones van directo a BIENESTAR + SEGURIDAD."
        )

    # ---- Sanciones / plagio ----
    if any(k in q for k in ("sancion", "sanción", "castigo", "plagio", "fraude", "expulsion", "expulsión", "suspension", "suspensión")):
        if not context:
            return (
                "No encontré artículos específicos del reglamento sobre eso. "
                "Lo que sí te puedo decir es que las sanciones en la universidad se aplican según la "
                "gravedad: BAJA (amonestación verbal), MEDIA (escrita), ALTA (suspensión 5-15 días) y "
                "CRÍTICA (suspensión de 30+ días o expulsión). ¿Quieres que te ayude a entender en qué "
                "categoría cae tu caso?"
            )
        # Extract the most relevant 1-2 sentences from context
        sentences = _split_sentences(context)
        relevant = [s for s in sentences if any(k in s.lower() for k in ("sancion", "castigo", "plagio", "fraude", "amonest", "suspens", "expuls"))]
        if relevant:
            excerpt = " ".join(relevant[:3])[:800]
            return (
                f"Según el reglamento, esto es lo que aplica:\n\n{excerpt}\n\n"
                f"¿Te queda alguna duda sobre el proceso disciplinario?"
            )
        return f"Según el reglamento:\n\n{context[:600]}\n\n¿Te puedo ayudar con algo más?"

    # ---- Queja anónima ----
    if any(k in q for k in ("anonima", "anónima", "identidad", "confidencial")):
        return (
            "Sí, puedes reportar de forma anónima. Solo tienes que marcar la casilla *Reportar de forma anónima* "
            "en el formulario y no te vamos a pedir ningún dato personal. Eso sí, ten en cuenta que sin contacto "
            "no podemos darte seguimiento: si quieres estar al tanto del estado de tu caso, déjanos un email "
            "opcional o usa un canal donde podamos responderte."
        )

    # ---- Cómo contacto / bienestar ----
    if any(k in q for k in ("contacto", "bienestar", "psicolog", "psicólog", "salud mental", "ayuda")):
        return (
            "Si necesitas apoyo personal (psicológico, emocional, víctima de acoso), la ruta es:\n\n"
            "1. Reporta la queja con categoría **ACOSO** o **SALUD** desde el formulario.\n"
            "2. El sistema detecta automáticamente que es sensible y notifica a BIENESTAR y SEGURIDAD de tu universidad.\n"
            "3. La universidad suele ofrecer hasta 8 sesiones gratis con psicólogo — el equipo de bienestar te contacta.\n\n"
            "Si es urgente, también puedes llamar a la línea de crisis 24/7 de tu universidad (revisa la intranet o el "
            "directorio de tu sede)."
        )

    # ---- Estado / seguimiento ----
    if any(k in q for k in ("estado", "seguimiento", "como se", "cómo se", "ver mi queja", "mi queja")):
        return (
            "Para ver el estado de tus quejas, tienes dos opciones:\n\n"
            "- **Dashboard institucional**: métricas agregadas (qué categorías tienen más casos, qué tan críticos, etc.).\n"
            "- **Detalle de queja**: cada queja tiene un ID con el que puedes consultar su estado actual, "
            "categoría detectada, criticidad y respuesta del comité si fue escalada.\n\n"
            "Si tu queja lleva más tiempo del plazo según su criticidad, te recomiendo escalarla."
        )

    # ---- Generic fallback: use context if available ----
    if not context:
        return (
            "No tengo una respuesta exacta para eso con la información que tengo a mano. "
            "Puedo ayudarte mejor si me das un poco más de contexto, o puedes contactar directamente a "
            "quejas@universidad.edu o al equipo de bienestar de tu sede."
        )

    # Extract sentences that contain keywords from the question
    keywords = [w for w in q.split() if len(w) > 4 and w not in ("como", "cuales", "donde", "cuando", "porque")]
    sentences = _split_sentences(context)
    relevant = [s for s in sentences if any(k in s.lower() for k in keywords)][:3]
    if relevant:
        excerpt = " ".join(relevant)
        return (
            f"Buena pregunta. Según el reglamento y la documentación disponible:\n\n{excerpt}\n\n"
            f"¿Quieres profundizar en algo específico?"
        )

    return (
        f"Encontré esto en el reglamento que podría servirte:\n\n{context[:500]}\n\n"
        f"Si no te queda claro, dime qué parte quieres que te explique mejor."
    )


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences for relevance extraction."""
    import re
    # Split on . ! ? followed by space/newline
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _generate_answer_with_llm(question: str, context: str) -> tuple[str, int, int]:
    """Generate an answer using the LLM (with context).

    Returns:
        Tuple of (answer_text, tokens_used, latency_ms)
    """
    use_mock = os.environ.get("MOCK_LLM", "true").lower() != "false"

    start = time.time()
    if use_mock:
        answer = _generate_answer_mock(question, context)
        tokens = len(question.split()) + len(context.split())
    else:
        # Real Cohere via direct HTTP (no oci SDK required, just stdlib + cryptography)
        from services.oci_http_client import OCIError, call_oci_cohere_chat
        from handlers._shared.config import get_settings

        settings = get_settings()
        # Use context to inform, but also rely on the assistant persona
        context_section = (
            f"Información relevante encontrada en el reglamento de la universidad:\n"
            f"<<<\n{context[:2500] if context else 'Sin contexto adicional del reglamento.'}\n>>>\n\n"
            if context
            else ""
        )
        user_prompt = (
            f"{context_section}"
            f"Pregunta del usuario: {question}\n\n"
            f"Responde de forma breve (3-5 oraciones), clara, en español, "
            f"y útil. Si el contexto del reglamento responde la pregunta, "
            f"úsalo. Si no, responde con tu conocimiento general sobre "
            f"universidades y sugiere contactar a bienestar@universidad.edu "
            f"para casos específicos."
        )
        preamble = (
            "Eres 'SentinelBot', el asistente virtual de Sentinel AcademIA — "
            "una plataforma universitaria para reportar y dar seguimiento a "
            "quejas. Tu trabajo es ayudar a estudiantes y personal con "
            "preguntas sobre el proceso de quejas, el reglamento, plazos, "
            "categorías y cómo escalar casos. Hablas en español, con tono "
            "amigable, claro y empático. Si el usuario describe una situación "
            "difícil (acoso, discriminación), responde con sensibilidad y "
            "sugiere buscar apoyo en bienestar. Tus respuestas son "
            "cortas (3-5 oraciones) a menos que pidan más detalle."
        )

        try:
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
                preamble=preamble,
                max_tokens=350,
                temperature=0.4,
            )
            payload = result["payload"]
            cr = payload.get("chatResponse", payload.get("chat_response", payload))
            answer = (cr.get("text") or "").strip()
            usage = cr.get("usage") or {}
            tokens = usage.get("totalTokens") or usage.get("total_tokens") or 0
            if not answer:
                log.warning("OCI Cohere returned empty text, falling back to mock")
                answer = _generate_answer_mock(question, context)
        except (OCIError, Exception) as e:  # noqa: BLE001
            log.error(f"OCI Cohere call failed, falling back to mock: {e}")
            answer = _generate_answer_mock(question, context)
            tokens = 0

    latency_ms = int((time.time() - start) * 1000)
    return answer, tokens, latency_ms


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """POST /api/chat"""
    with_correlation_id(event)
    try:
        tenant_id = extract_tenant_id(event)
        log.append_keys(tenant_id=tenant_id)

        # Parse + validate body
        body = _parse_body(event)
        try:
            req = ChatRequest.model_validate(body)
        except PydanticValidationError as e:
            raise ValidationError(
                message="Invalid chat request",
                details={"errors": str(e)},
            ) from e

        log.append_keys(question_length=len(req.question))

        # 1. Retrieve relevant context (RAG step 1)
        context = build_context(req.question, top_k=3, tenant_id=tenant_id)
        sources_raw = search(req.question, top_k=3, tenant_id=tenant_id)
        log.info(
            "RAG retrieval",
            extra={"sources_found": len(sources_raw), "context_len": len(context)},
        )

        # 2. Generate answer with context (RAG step 2)
        answer, tokens, latency = _generate_answer_with_llm(req.question, context)

        # 3. Build response
        from handlers._shared.schemas import ChatSource

        sources = [
            ChatSource(
                id=s["id"],
                title=s["title"],
                content=s["content"],
                score=min(1.0, s["score"] / 10.0),  # normalize to 0-1
                page=s.get("page"),
                source=s.get("source", s.get("title", "")),
            )
            for s in sources_raw
        ]

        response = ChatResponse(
            answer=answer,
            sources=sources,
            conversationId=req.conversationId,
            modeloUsado=(
                "mock-rule-based-v1"
                if not sources
                else "cohere.command-latest"
            ),
            tokensUsados=tokens,
            latenciaMs=latency,
        )

        log.info(
            "Chat response generated",
            extra={"answer_length": len(answer), "sources": len(sources)},
        )

        return HttpResponse.ok(response.model_dump(mode="json"))
    finally:
        clear_correlation_id()
