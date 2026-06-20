"""SNS consumer: notify_by_email.

Renders beautiful HTML emails and uploads them to S3 (publicly readable).
The SNS message includes a link to the HTML preview, simulating real email
delivery without requiring SES access (AWS Academy LabRole restriction).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from handlers._shared.config import get_settings
from handlers._shared.correlation_id import clear_correlation_id, with_correlation_id
from handlers._shared.errors import error_handler
from handlers._shared.logger import get_logger
from services.tenant_config_service import get_recipients, get_tenant_config

log = get_logger(__name__)


# ============================================================================
# HTML Email Templates (CSS inline for max compatibility)
# ============================================================================

EMAIL_BASE_CSS = """
body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f4f6f9; color: #1a1a1a; }
.container { max-width: 680px; margin: 0 auto; background: #ffffff; }
.header { padding: 32px 40px; background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); color: white; }
.header h1 { margin: 0; font-size: 22px; font-weight: 600; letter-spacing: -0.3px; }
.header .subtitle { margin: 6px 0 0; font-size: 13px; opacity: 0.85; }
.badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.badge-critical { background: #fee2e2; color: #991b1b; }
.badge-high { background: #fed7aa; color: #9a3412; }
.badge-medium { background: #fef3c7; color: #854d0e; }
.badge-low { background: #d1fae5; color: #065f46; }
.badge-info { background: #dbeafe; color: #1e40af; }
.body { padding: 32px 40px; }
.alert-banner { padding: 16px 20px; border-radius: 8px; margin-bottom: 24px; }
.alert-banner.critical { background: #fef2f2; border-left: 4px solid #dc2626; }
.alert-banner.aggregate { background: #fff7ed; border-left: 4px solid #ea580c; }
.alert-banner p { margin: 0; color: #1a1a1a; font-size: 14px; line-height: 1.5; }
.alert-banner strong { color: #991b1b; }
.section { margin-bottom: 28px; }
.section-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; margin: 0 0 10px; }
.detail-grid { display: grid; grid-template-columns: 140px 1fr; gap: 8px 16px; padding: 16px 20px; background: #f9fafb; border-radius: 8px; font-size: 14px; }
.detail-grid dt { color: #6b7280; font-weight: 500; margin: 0; }
.detail-grid dd { color: #111827; font-weight: 500; margin: 0; }
.description-box { padding: 18px 20px; background: #f9fafb; border-radius: 8px; border-left: 3px solid #2563eb; font-size: 14px; line-height: 1.6; color: #1f2937; white-space: pre-wrap; }
.aggregate-list { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }
.aggregate-list h4 { margin: 0 0 12px; font-size: 14px; color: #9a3412; }
.aggregate-list ul { margin: 0; padding-left: 20px; color: #7c2d12; font-size: 13px; }
.aggregate-list li { margin-bottom: 6px; }
.recommendations { padding: 20px 24px; background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-radius: 8px; margin-bottom: 24px; border-left: 4px solid #059669; }
.recommendations h3 { margin: 0 0 12px; font-size: 15px; color: #064e3b; display: flex; align-items: center; gap: 8px; }
.recommendations .ai-badge { background: #059669; color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 700; }
.recommendations .content { font-size: 14px; line-height: 1.7; color: #064e3b; white-space: pre-wrap; }
.actions { display: flex; gap: 12px; margin: 24px 0 8px; }
.btn { display: inline-block; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px; }
.btn-primary { background: #2563eb; color: white; }
.btn-secondary { background: #ffffff; color: #1e40af; border: 1.5px solid #1e40af; }
.footer { padding: 24px 40px; background: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center; }
.footer p { margin: 0; font-size: 12px; color: #6b7280; }
.footer .timestamp { margin-top: 4px; font-size: 11px; color: #9ca3af; }
.divider { height: 1px; background: #e5e7eb; margin: 24px 0; }
""".strip()


def render_email_html(
    subject: str,
    queja: dict,
    analysis: dict,
    tenant: dict,
    agregado: dict | None,
    recomendaciones_ia: str,
    recipients: list[str],
    email_url: str,
) -> str:
    """Render the email as HTML with a professional design."""
    categoria = analysis.get("categoria", "")
    criticidad = analysis.get("criticidad", "")
    prioridad = analysis.get("prioridad", 0)
    inmediata = analysis.get("requiereNotificacionInmediata", False)

    if criticidad == "CRITICA":
        banner_class = "critical"
        banner_label = "Queja CRITICA - Requiere atencion inmediata"
        badge_class = "badge-critical"
    elif criticidad == "ALTA":
        banner_class = "aggregate"
        banner_label = "Queja de prioridad ALTA"
        badge_class = "badge-high"
    elif criticidad == "MEDIA":
        banner_class = "aggregate"
        banner_label = "Queja de prioridad MEDIA"
        badge_class = "badge-medium"
    else:
        banner_class = "aggregate"
        banner_label = f"Queja {criticidad}"
        badge_class = "badge-low"

    # Aggregate-specific content
    aggregate_section = ""
    if agregado:
        count = agregado.get("count", 0)
        sample_titles = agregado.get("sample_titles", [])
        common_kw = agregado.get("common_keywords", [])[:8]
        aggregate_section = f'''
<div class="aggregate-list">
  <h4>📊 {count} quejas similares detectadas</h4>
  <p style="margin: 0 0 8px; font-size: 12px; color: #9a3412;">
    Palabras clave comunes: {", ".join(common_kw)}
  </p>
  <ul>
    {"".join(f"<li>{t}</li>" for t in sample_titles[:5])}
  </ul>
</div>
'''
        banner_class = "aggregate"
        banner_label = f"Alerta agregada: {count} quejas similares"

    # Recommendations section
    recommendations_html = ""
    if recomendaciones_ia:
        recommendations_html = f'''
<div class="recommendations">
  <h3>Recomendaciones de la IA <span class="ai-badge">COHERE</span></h3>
  <div class="content">{recomendaciones_ia}</div>
</div>
'''

    # Contact info
    reportante_html = ""
    if queja.get("contactoEmail"):
        reportante_html = f'<dd><a href="mailto:{queja["contactoEmail"]}" style="color: #2563eb; text-decoration: none;">{queja["contactoEmail"]}</a></dd>'
    else:
        reportante_html = '<dd><em style="color: #6b7280;">An&oacute;nima</em></dd>'

    curso_html = ""
    if queja.get("cursoCodigo"):
        curso_html = f'<dt>Curso</dt><dd><strong>{queja["cursoCodigo"]}</strong></dd>'

    sede_facultad = ""
    if queja.get("sede") or queja.get("facultad"):
        sede_facultad = (
            f'<dt>Ubicaci&oacute;n</dt><dd>'
            + " / ".join(filter(None, [queja.get("sede"), queja.get("facultad")]))
            + '</dd>'
        )

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>{EMAIL_BASE_CSS}</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🛡️ Sentinel AcademIA</h1>
    <p class="subtitle">Sistema de gesti&oacute;n de quejas universitarias</p>
  </div>

  <div class="body">
    <div class="alert-banner {banner_class}">
      <p>
        <span class="badge {badge_class}">{criticidad or "NUEVA"}</span>
        &nbsp;
        <strong>{banner_label}</strong>
      </p>
    </div>

    {aggregate_section}

    <div class="section">
      <h2 class="section-title">Informaci&oacute;n de la queja</h2>
      <dl class="detail-grid">
        <dt>Tenant</dt><dd>{tenant.get("name", "?")} ({queja.get("tenantId", "?")})</dd>
        <dt>Categor&iacute;a</dt><dd><span class="badge badge-info">{categoria or queja.get("categoriaDeclarada", "")}</span></dd>
        <dt>Prioridad</dt><dd><strong>{prioridad}/10</strong></dd>
        <dt>Queja ID</dt><dd><code style="background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 12px;">{queja.get("quejaId", "?")}</code></dd>
        {curso_html}
        {sede_facultad}
        <dt>Reportante</dt>{reportante_html}
      </dl>
    </div>

    <div class="section">
      <h2 class="section-title">T&iacute;tulo</h2>
      <p style="font-size: 18px; font-weight: 600; color: #111827; margin: 0;">
        {queja.get("titulo", "")}
      </p>
    </div>

    <div class="section">
      <h2 class="section-title">Descripci&oacute;n</h2>
      <div class="description-box">{queja.get("descripcion", "")}</div>
    </div>

    {recommendations_html}

    <div class="actions">
      <a href="https://sentinel-frontend-dev-227165337884.s3-website-us-east-1.amazonaws.com/dashboard" class="btn btn-primary">
        Ver en Dashboard
      </a>
      <a href="https://sentinel-frontend-dev-227165337884.s3-website-us-east-1.amazonaws.com/queja/{queja.get("quejaId", "")}" class="btn btn-secondary">
        Ver queja completa
      </a>
    </div>

    <div class="divider"></div>

    <p style="font-size: 13px; color: #6b7280; margin: 0;">
      <strong>Acci&oacute;n requerida:</strong> Por favor revisa esta queja y toma las medidas correspondientes seg&uacute;n el protocolo de {tenant.get("name", "la universidad")}.
      Si necesitas escalar este caso, responde a este email indicando la acci&oacute;n tomada.
    </p>
  </div>

  <div class="footer">
    <p>
      Enviado a: {", ".join(recipients)}<br>
      <strong>Sentinel AcademIA</strong> &middot; Multi-nube AWS + OCI
    </p>
    <p class="timestamp">
      {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")} &middot;
      <a href="{email_url}" style="color: #6b7280;">Ver este email en el navegador</a>
    </p>
  </div>
</div>
</body>
</html>'''


def render_plain_text(queja, analysis, tenant, agregado, recomendaciones_ia, recipients, email_url):
    """Plain text fallback for email clients that don't support HTML."""
    parts = [
        f"=== SENTINEL ACADEMIA - {analysis.get('criticidad', 'NUEVA')} ===",
        f"Tenant: {tenant.get('name', '?')}",
        f"Categoria: {analysis.get('categoria', '')}",
        f"Prioridad: {analysis.get('prioridad', '')}/10",
        f"Queja ID: {queja.get('quejaId', '?')}",
        "",
        f"TITULO: {queja.get('titulo', '')}",
        "",
        "DESCRIPCION:",
        queja.get("descripcion", ""),
        "",
    ]
    if queja.get("cursoCodigo"):
        parts.append(f"CURSO: {queja['cursoCodigo']}")
    if queja.get("contactoEmail"):
        parts.append(f"REPORTANTE: {queja['contactoEmail']}")
    if agregado:
        parts.append(f"\nQuejas similares: {agregado.get('count', 0)}")
        parts.append("Titulos: " + ", ".join(agregado.get("sample_titles", [])[:3]))
    if recomendaciones_ia:
        parts.append("\nRECOMENDACIONES DE LA IA:")
        parts.append(recomendaciones_ia)
    parts.append(f"\n---")
    parts.append(f"Ver email HTML: {email_url}")
    parts.append(f"\nEnviado a: {', '.join(recipients)}")
    return "\n".join(parts)


# ============================================================================
# Lambda Handler
# ============================================================================

@error_handler
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """SNS event handler: renders HTML email, uploads to S3, logs link."""
    with_correlation_id(event)
    try:
        records = event.get("Records", [])
        log.info(f"Processing {len(records)} SNS records")

        settings = get_settings()
        s3_client = boto3.client("s3", region_name=settings.region)
        # Email bucket is hardcoded to keep template simple
        email_bucket = f"sentinel-emails-dev-227165337884"
        # Use the REST endpoint (HTTPS) - bucket policy allows public read
        public_url_base = f"https://{email_bucket}.s3.us-east-1.amazonaws.com"

        for record in records:
            sns = record.get("Sns", {})
            message_str = sns.get("Message", "{}")
            sns_subject = sns.get("Subject", "Sentinel Notification")
            try:
                message = json.loads(message_str)
            except json.JSONDecodeError:
                log.warning("Invalid SNS message", extra={"message_preview": message_str[:200]})
                continue

            tenant_id = message.get("tenantId", "unknown")
            queja = message.get("queja", {})
            analysis = message.get("analysis", {})
            agregado = message.get("agregado")
            recomendaciones_ia = message.get("recomendaciones_ia", "")

            tenant_config = get_tenant_config(tenant_id)
            recipients = get_recipients(tenant_id, analysis.get("categoria", "OTRA"))

            # Render HTML
            email_id = uuid.uuid4().hex[:12]
            email_url = f"{public_url_base}/emails/{email_id}.html"
            html_content = render_email_html(
                sns_subject, queja, analysis, tenant_config,
                agregado, recomendaciones_ia, recipients, email_url,
            )
            plain_content = render_plain_text(
                queja, analysis, tenant_config,
                agregado, recomendaciones_ia, recipients, email_url,
            )

            # Upload to S3 (public-readable via bucket policy)
            s3_key = f"emails/{email_id}.html"
            try:
                s3_client.put_object(
                    Bucket=email_bucket,
                    Key=s3_key,
                    Body=html_content.encode("utf-8"),
                    ContentType="text/html; charset=utf-8",
                )
                log.info(f"Email HTML uploaded: {email_url}")
            except ClientError as e:
                log.error(f"Failed to upload email HTML: {e}")
                email_url = "(upload failed)"

            # Log
            log.info(
                "HTML EMAIL READY (preview link below)",
                extra={
                    "tenant_id": tenant_id,
                    "to": recipients,
                    "subject": sns_subject,
                    "email_url": email_url,
                    "is_aggregate": bool(agregado),
                    "prioridad": analysis.get("prioridad"),
                    "criticidad": analysis.get("criticidad"),
                },
            )

        return {"statusCode": 200, "body": "OK"}
    finally:
        clear_correlation_id()
