"""SQS consumer: analyze_queja.

Triggered by SQS when a new queja is queued.
Flow:
1. Receive message from SQS (contains quejaId + tenantId)
2. Fetch queja from DynamoDB
3. Update status to PROCESANDO
4. Call LLM (Cohere) for analysis
5. Update status to ANALIZADA + store analysis
6. On failure: status to ERROR (retry handled by SQS)

Async pattern: createQueja sends a message; this Lambda processes it.
"""

from __future__ import annotations

import json
import os
from typing import Any

from handlers._shared.config import get_settings
from handlers._shared.correlation_id import clear_correlation_id, with_correlation_id
from handlers._shared.dynamo_client import (
    get_dynamo_client,
    now_iso,
    queja_pk,
    queja_sk,
)
from handlers._shared.errors import error_handler
from handlers._shared.http_response import HttpResponse  # for compatibility
from handlers._shared.logger import get_logger

import boto3

from handlers._shared.schemas import SQSCreateQuejaMessage
from services.llm_client import LLMError, get_llm_client
from services.tenant_config_service import get_recipients, get_tenant_config, should_notify

log = get_logger(__name__)


def _publish_notification(
    tenant_id: str,
    queja: dict,
    analysis,
    contexto_agregado: dict[str, Any] | None = None,
) -> None:
    """Publish queja notification to SNS (per-tenant routing).

    For INFRAESTRUCTURA, contexto_agregado contains the cluster summary.
    AI recommendations are generated via Cohere to help the recipient
    (rector/bienestar) decide how to respond.
    """
    settings = get_settings()
    topic_arn = getattr(settings, "alertas_topic_arn", None) or ""
    if not topic_arn:
        log.warning("SNS topic ARN not configured, skipping notification")
        return

    tenant_config = get_tenant_config(tenant_id)
    categoria = analysis.categoria.value
    recipients = get_recipients(tenant_id, categoria)

    # Generate AI recommendations for the recipient
    recomendaciones = _generate_recommendations(
        categoria=categoria,
        queja=queja,
        analysis=analysis,
        contexto_agregado=contexto_agregado,
    )

    # Subject
    if contexto_agregado:
        subject = f"[Sentinel] {contexto_agregado['count']} quejas similares: {queja.titulo[:40]}"
    else:
        subject = f"[Sentinel] {categoria} {analysis.criticidad.value}: {queja.titulo[:50]}"

    message = {
        "tenantId": tenant_id,
        "tenantName": tenant_config.get("name", tenant_id),
        "queja": {
            "quejaId": queja.quejaId,
            "tenantId": queja.tenantId,
            "titulo": queja.titulo,
            "descripcion": queja.descripcion,
            "categoriaDeclarada": queja.categoriaDeclarada.value,
            "cursoCodigo": getattr(queja, "cursoCodigo", None),
            "sede": getattr(queja, "sede", None),
            "facultad": getattr(queja, "facultad", None),
            "contactoEmail": getattr(queja, "contactoEmail", None),
        },
        "analysis": analysis.model_dump(mode="json"),
        "recipients": recipients,
        "recomendaciones_ia": recomendaciones,
    }
    if contexto_agregado:
        message["agregado"] = contexto_agregado

    sns = boto3.client("sns")
    try:
        # Render HTML and upload to S3 first (so we can include the link in the email)
        html_url = _upload_html_to_s3(
            subject=subject,
            queja=message["queja"],
            analysis=message["analysis"],
            tenant=tenant_config,
            agregado=contexto_agregado,
            recomendaciones_ia=recomendaciones,
            recipients=recipients,
        )
        # SNS email body: clean text with link to the beautiful HTML preview
        email_body = _render_simple_email_body(
            subject=subject,
            queja=message["queja"],
            analysis=message["analysis"],
            agregado=contexto_agregado,
            recomendaciones_ia=recomendaciones,
            html_url=html_url,
        )
        # Include the html_url in the JSON message for HTTP/SQS consumers
        message["html_url"] = html_url
        sns_message_payload = {
            "default": json.dumps(message, ensure_ascii=False),
            "email": email_body,
        }
        response = sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=json.dumps(sns_message_payload, ensure_ascii=False),
            MessageStructure="json",
        )
        log.info(
            "Notification published to SNS",
            extra={
                "message_id": response.get("MessageId"),
                "categoria": categoria,
                "prioridad": analysis.prioridad,
                "recipients": recipients,
                "is_aggregate": bool(contexto_agregado),
            },
        )
    except Exception as e:
        log.error("Failed to publish to SNS", extra={"error": str(e), "topic_arn": topic_arn})


def _render_simple_email_body(
    subject: str,
    queja: dict,
    analysis: dict,
    agregado: dict | None,
    recomendaciones_ia: str,
    html_url: str = "",
) -> str:
    """Render a clean, simple email body with a link to the HTML preview.

    SNS email protocol only sends text/plain, so embedding HTML in the body
    shows up as raw text. The right pattern is: short clean email with a link
    to the beautiful HTML page (hosted in S3).
    """
    lines = [
        f"Hola,",
        "",
        f"Se ha recibido una nueva alerta de Sentinel AcademIA.",
        "",
        f"DETALLE DE LA QUEJA",
        f"===================",
        f"Tipo: {analysis.get('categoria', '')} ({analysis.get('criticidad', '')})",
        f"Prioridad: {analysis.get('prioridad', '')}/10",
        f"Queja ID: {queja.get('quejaId', '')}",
        f"Titulo: {queja.get('titulo', '')}",
    ]
    if queja.get("cursoCodigo"):
        lines.append(f"Curso: {queja['cursoCodigo']}")
    if queja.get("contactoEmail"):
        lines.append(f"Reportante: {queja['contactoEmail']}")
    lines.append("")
    lines.append("Descripcion:")
    lines.append(queja.get("descripcion", "")[:500])
    lines.append("")
    if agregado:
        lines.append(f"*** ALERTA AGREGADA: {agregado.get('count', 0)} quejas similares ***")
        if agregado.get("common_keywords"):
            lines.append(f"Palabras clave: {', '.join(agregado['common_keywords'][:8])}")
    if recomendaciones_ia:
        lines.append("")
        lines.append("Recomendaciones de la IA (Cohere):")
        lines.append(recomendaciones_ia[:600])
    lines.append("")
    lines.append("---")
    lines.append("VER EMAIL COMPLETO CON DISENO:")
    if html_url:
        lines.append(html_url)
    else:
        lines.append("(link no disponible)")
    lines.append("")
    lines.append("---")
    lines.append("Sentinel AcademIA - Multi-nube AWS + OCI")
    return "\n".join(lines)


def _upload_html_to_s3(
    subject: str,
    queja: dict,
    analysis: dict,
    tenant: dict,
    agregado: dict | None,
    recomendaciones_ia: str,
    recipients: list[str],
) -> str:
    """Render HTML and upload to S3. Returns the public URL."""
    import uuid as uuid_mod
    from services.email_template import render_email_html

    settings = get_settings()
    s3_client = boto3.client("s3", region_name=settings.region)
    email_bucket = "sentinel-emails-dev-227165337884"

    analysis_dict = analysis if isinstance(analysis, dict) else analysis.model_dump(mode="json")
    html_content = render_email_html(
        subject=subject,
        queja=queja,
        analysis=analysis_dict,
        tenant=tenant,
        agregado=agregado,
        recomendaciones_ia=recomendaciones_ia,
        recipients=recipients,
    )

    email_id = uuid_mod.uuid4().hex[:12]
    s3_key = f"emails/{email_id}.html"
    try:
        s3_client.put_object(
            Bucket=email_bucket,
            Key=s3_key,
            Body=html_content.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
        )
        return f"https://{email_bucket}.s3.us-east-1.amazonaws.com/{s3_key}"
    except Exception as e:
        log.warning(f"Failed to upload HTML preview: {e}")
        return ""


def _generate_recommendations(
    categoria: str,
    queja: dict,
    analysis,
    contexto_agregado: dict[str, Any] | None,
) -> str:
    """Use Cohere to generate recommendations for the SNS recipient.

    Falls back to a simple template if the LLM is unavailable.
    """
    settings = get_settings()
    use_mock = os.environ.get("MOCK_LLM", "true").lower() != "false"

    # Build context
    if contexto_agregado:
        user_prompt = (
            f"Recibes un GRUPO de {contexto_agregado['count']} quejas similares "
            f"de la categor\u00eda {categoria} en {contexto_agregado.get('top_sedes', ['?'])[0]}.\n\n"
            f"Titulo representativo: {queja.titulo}\n"
            f"Descripcion: {queja.descripcion[:300]}\n"
            f"Palabras clave comunes: {', '.join(contexto_agregado['common_keywords'][:8])}\n"
            f"Prioridad del an\u00e1lisis IA: {analysis.prioridad}/10\n\n"
            f"Como autoridad universitaria, qu\u00e9 acci\u00f3n recomiendas? "
            f"Responde breve (3-4 oraciones) y accionable."
        )
    else:
        user_prompt = (
            f"Nuevo reporte individual ({categoria}, criticidad {analysis.criticidad.value}, "
            f"prioridad {analysis.prioridad}/10):\n\n"
            f"Titulo: {queja.titulo}\n"
            f"Descripcion: {queja.descripcion[:400]}\n"
        )
        if getattr(queja, "cursoCodigo", None):
            user_prompt += f"Curso: {queja.cursoCodigo}\n"
        user_prompt += (
            "\nComo autoridad (rector/bienestar), qu\u00e9 acci\u00f3n recomiendas? "
            "Responde breve (2-3 oraciones) y accionable."
        )

    preamble = (
        "Eres un asistente administrativo experto en gesti\u00f3n universitaria. "
        "Tu trabajo es dar recomendaciones CONCRETAS y ACCIONABLES a las "
        "autoridades sobre c\u00f3mo responder a quejas. Hablas en espa\u00f1ol, "
        "de forma directa y breve. Prioriza: 1) protecci\u00f3n de personas si "
        "es sensible, 2) plazos de respuesta, 3) acci\u00f3n concreta a tomar."
    )

    if use_mock:
        # Simple rule-based fallback
        if contexto_agregado:
            return (
                f"Patr\u00f3n detectado: {contexto_agregado['count']} quejas similares "
                f"sobre '{queja.titulo[:50]}'. Recomiendo: 1) Visita de inspecci\u00f3n "
                f"a {contexto_agregado.get('top_sedes', ['el \u00e1rea afectada'])[0]} esta semana. "
                f"2) Plan de mantenimiento correctivo con plazo de 30 d\u00edas. "
                f"3) Comunicado oficial a la comunidad universitaria."
            )
        if categoria == "ACOSO":
            return (
                "1) Contactar al reportante en m\u00e1ximo 24h (v\u00eda bienestar). "
                "2) Activar protocolo de acoso con comit\u00e9 de 3 miembros. "
                "3) Medidas de protecci\u00f3n inmediatas para la v\u00edctima."
            )
        if categoria == "ACADEMICA":
            return (
                f"1) Verificar el caso con el profesor del curso {getattr(queja, 'cursoCodigo', '?')}. "
                "2) Solicitar al docente explicaci\u00f3n formal y plazo de regularizaci\u00f3n. "
                "3) Si procede, escalar a decanatura para sanci\u00f3n o capacitaci\u00f3n."
            )
        if categoria == "SALUD":
            return (
                "1) Contactar v\u00eda Bienestar Estudiantil en 24h. "
                "2) Ofrecer apoyo psicol\u00f3gico (hasta 8 sesiones gratis). "
                "3) Si hay riesgo inmediato, activar l\u00ednea de crisis 24/7."
            )
        return (
            f"1) Revisar la queja con el \u00e1rea correspondiente. "
            f"2) Dar respuesta formal en plazo de {analysis.prioridad} d\u00edas. "
            f"3) Documentar la resoluci\u00f3n para referencia futura."
        )

    # Real LLM
    try:
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
            preamble=preamble,
            max_tokens=350,
            temperature=0.4,
        )
        cr = result["payload"].get("chatResponse", result["payload"].get("chat_response", result["payload"]))
        text = (cr.get("text") or "").strip()
        return text or _generate_recommendations(categoria, queja, analysis, contexto_agregado)
    except Exception as e:
        log.error(f"Cohere recommendations failed: {e}")
        return _generate_recommendations.__wrapped__(categoria, queja, analysis, contexto_agregado) if hasattr(_generate_recommendations, "__wrapped__") else ""


def _set_status(queja_id: str, tenant_id: str, status: str) -> None:
    """Update queja status in DynamoDB."""
    dynamo = get_dynamo_client()
    dynamo.update_item(
        pk=queja_pk(tenant_id, queja_id),
        sk=queja_sk(queja_id),
        updates={"status": status, "updatedAt": now_iso()},
    )


def _process_one(record: dict[str, Any]) -> None:
    """Process a single SQS record."""
    body = record.get("body", "{}")
    msg = SQSCreateQuejaMessage.model_validate_json(body)
    log.append_keys(queja_id=msg.quejaId, tenant_id=msg.tenantId)

    log.info("Starting analysis")

    # 1. Fetch queja
    dynamo = get_dynamo_client()
    item = dynamo.get_queja(tenant_id=msg.tenantId, queja_id=msg.quejaId)
    from handlers._shared.schemas import QuejaResponse

    queja = QuejaResponse.from_dynamo(item)

    # 2. Update to PROCESANDO
    _set_status(msg.quejaId, msg.tenantId, "PROCESANDO")
    log.info("Status updated to PROCESANDO")

    # 3. Call LLM
    llm = get_llm_client()
    try:
        analysis = llm.analyze_queja(queja)
    except LLMError as e:
        log.error("LLM call failed", extra={"error": str(e)})
        _set_status(msg.quejaId, msg.tenantId, "ERROR")
        # Re-raise so SQS retries (and eventually DLQ)
        raise

    # 4. Update to ANALIZADA + store analysis
    analysis_json = analysis.model_dump(mode="json")
    dynamo.update_item(
        pk=queja_pk(msg.tenantId, msg.quejaId),
        sk=queja_sk(msg.quejaId),
        updates={
            "status": "ANALIZADA",
            "updatedAt": now_iso(),
            "analysis": analysis_json,
        },
    )
    log.info(
        "Analysis stored",
        extra={
            "categoria": analysis.categoria.value,
            "criticidad": analysis.criticidad.value,
            "prioridad": analysis.prioridad,
            "tokens": analysis.tokensConsumidos,
        },
    )

    # 5. Notification logic: per-category business rules
    categoria = queja.categoriaDeclarada.value
    notificar = False
    contexto_agregado: dict[str, Any] | None = None

    if categoria == "INFRAESTRUCTURA":
        # Wait for sample size (10) of similar complaints
        from services.complaint_aggregator import (
            should_trigger_aggregate_notification,
            summarize_cluster,
        )

        complaint_dict = {
            "titulo": queja.titulo,
            "descripcion": queja.descripcion,
            "categoriaDeclarada": categoria,
            "sede": queja.sede,
            "facultad": queja.facultad,
        }
        should_aggregate, similar = should_trigger_aggregate_notification(
            msg.tenantId, complaint_dict
        )
        if should_aggregate:
            # Aggregate this one + all similar ones
            cluster = [complaint_dict] + [
                {k: v for k, v in s.items() if k in ("titulo", "descripcion", "categoriaDeclarada", "sede", "facultad")}
                for s in similar
            ]
            contexto_agregado = summarize_cluster(cluster)
            contexto_agregado["queja_nueva"] = queja.quejaId
            notificar = True
            log.info(
                "INFRAESTRUCTURA threshold reached, aggregating",
                extra={"count": len(cluster), "tenant_id": msg.tenantId},
            )
        else:
            log.info(
                "INFRAESTRUCTURA below threshold, waiting for more",
                extra={"similar_count": len(similar), "tenant_id": msg.tenantId},
            )
    else:
        # ACADEMICA/ACOSO/ADMINISTRATIVA/SALUD: single queja triggers notification
        if should_notify(msg.tenantId, analysis_json):
            notificar = True

    if notificar:
        _publish_notification(
            msg.tenantId, queja, analysis,
            contexto_agregado=contexto_agregado,
        )


@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """SQS event handler for the analysis queue."""
    with_correlation_id(event)
    try:
        records = event.get("Records", [])
        log.info(f"Processing {len(records)} SQS records")

        failed: list[dict[str, Any]] = []
        for record in records:
            try:
                _process_one(record)
            except Exception as e:
                log.exception("Failed to process record")
                failed.append(
                    {"itemIdentifier": record.get("messageId"), "message": str(e)}
                )

        # If any failed, return batchItemFailures so SQS retries
        if failed:
            return {"batchItemFailures": failed}

        return {"statusCode": 200, "body": "OK"}
    finally:
        clear_correlation_id()
