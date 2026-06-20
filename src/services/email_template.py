"""Shared HTML email template for Sentinel AcademIA notifications.

Used by:
- analyze_queja: renders inline HTML for SNS email subscriptions
- notify_by_email: renders + uploads to S3 for preview/archival
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


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


def render_plain_text(
    queja: dict[str, Any],
    analysis: dict[str, Any],
    tenant: dict[str, Any],
    agregado: dict[str, Any] | None,
    recomendaciones_ia: str,
    recipients: list[str],
) -> str:
    """Generate plain text version for multipart MIME."""
    parts = [
        f"=== SENTINEL ACADEMIA - {analysis.get('criticidad', 'NUEVA')} ===",
        f"Tenant: {tenant.get('name', '?')}",
        f"Categoria: {analysis.get('categoria', '')}",
        f"Prioridad: {analysis.get('prioridad', '')}/10",
        f"Queja ID: {queja.get('quejaId', '?')}",
    ]
    if queja.get("cursoCodigo"):
        parts.append(f"Curso: {queja['cursoCodigo']}")
    if queja.get("contactoEmail"):
        parts.append(f"Reportante: {queja['contactoEmail']}")
    parts.append("")
    parts.append(f"TITULO: {queja.get('titulo', '')}")
    parts.append("")
    parts.append("DESCRIPCION:")
    parts.append(queja.get("descripcion", ""))
    parts.append("")
    if agregado:
        parts.append(f"\n*** ALERTA AGREGADA: {agregado.get('count', 0)} QUEJAS SIMILARES ***")
        parts.append(f"Palabras clave: {', '.join(agregado.get('common_keywords', [])[:10])}")
        if agregado.get("top_sedes"):
            parts.append(f"Sedes: {', '.join(agregado['top_sedes'])}")
        parts.append("Titulos representativos:")
        for t in agregado.get("sample_titles", [])[:5]:
            parts.append(f"  - {t}")
    if recomendaciones_ia:
        parts.append("\nRECOMENDACIONES DE LA IA:")
        parts.append(recomendaciones_ia)
    parts.append(f"\n---")
    parts.append(f"Enviado a: {', '.join(recipients)}")
    parts.append("Sentinel AcademIA - Multi-nube AWS + OCI")
    return "\n".join(parts)


def build_multipart_email(
    html_body: str,
    plain_text: str,
) -> str:
    """Combine HTML and plain text into a multipart/alternative MIME message.

    This is the standard way to send HTML emails that work across all clients
    (Gmail, Outlook, mobile clients). Email clients that support HTML will
    render the HTML part; fallback clients will see the plain text.
    """
    import uuid as uuid_mod

    boundary = f"----=_NextPart_Sentinel_{uuid_mod.uuid4().hex[:12]}"
    return f"""\
--{boundary}
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

{plain_text}

--{boundary}
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: 7bit

{html_body}

--{boundary}--"""


def render_email_html(
    subject: str,
    queja: dict[str, Any],
    analysis: dict[str, Any],
    tenant: dict[str, Any],
    agregado: dict[str, Any] | None,
    recomendaciones_ia: str,
    recipients: list[str],
) -> str:
    """Render the email as HTML with a professional design (CSS inline)."""
    categoria = analysis.get("categoria", "")
    criticidad = analysis.get("criticidad", "")
    prioridad = analysis.get("prioridad", 0)

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

    aggregate_section = ""
    if agregado:
        count = agregado.get("count", 0)
        sample_titles = agregado.get("sample_titles", [])
        common_kw = agregado.get("common_keywords", [])[:8]
        aggregate_section = f'''
<div class="aggregate-list">
  <h4>&#128202; {count} quejas similares detectadas</h4>
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

    recommendations_html = ""
    if recomendaciones_ia:
        recommendations_html = f'''
<div class="recommendations">
  <h3>Recomendaciones de la IA <span class="ai-badge">COHERE</span></h3>
  <div class="content">{recomendaciones_ia}</div>
</div>
'''

    if queja.get("contactoEmail"):
        reportante_html = f'<dd><a href="mailto:{queja["contactoEmail"]}" style="color: #2563eb; text-decoration: none;">{queja["contactoEmail"]}</a></dd>'
    else:
        reportante_html = '<dd><em style="color: #6b7280;">Anonima</em></dd>'

    curso_html = ""
    if queja.get("cursoCodigo"):
        curso_html = f'<dt>Curso</dt><dd><strong>{queja["cursoCodigo"]}</strong></dd>'

    sede_facultad = ""
    if queja.get("sede") or queja.get("facultad"):
        sede_facultad = (
            f'<dt>Ubicacion</dt><dd>'
            + " / ".join(filter(None, [queja.get("sede"), queja.get("facultad")]))
            + '</dd>'
        )

    frontend_base = "https://sentinel-frontend-dev-227165337884.s3-website-us-east-1.amazonaws.com"

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
    <h1>&#128737; Sentinel AcademIA</h1>
    <p class="subtitle">Sistema de gestion de quejas universitarias</p>
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
      <h2 class="section-title">Informacion de la queja</h2>
      <dl class="detail-grid">
        <dt>Tenant</dt><dd>{tenant.get("name", "?")} ({queja.get("tenantId", "?")})</dd>
        <dt>Categoria</dt><dd><span class="badge badge-info">{categoria or queja.get("categoriaDeclarada", "")}</span></dd>
        <dt>Prioridad</dt><dd><strong>{prioridad}/10</strong></dd>
        <dt>Queja ID</dt><dd><code style="background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 12px;">{queja.get("quejaId", "?")}</code></dd>
        {curso_html}
        {sede_facultad}
        <dt>Reportante</dt>{reportante_html}
      </dl>
    </div>

    <div class="section">
      <h2 class="section-title">Titulo</h2>
      <p style="font-size: 18px; font-weight: 600; color: #111827; margin: 0;">
        {queja.get("titulo", "")}
      </p>
    </div>

    <div class="section">
      <h2 class="section-title">Descripcion</h2>
      <div class="description-box">{queja.get("descripcion", "")}</div>
    </div>

    {recommendations_html}

    <div class="actions">
      <a href="{frontend_base}/dashboard" class="btn btn-primary">Ver en Dashboard</a>
      <a href="{frontend_base}/queja/{queja.get("quejaId", "")}" class="btn btn-secondary">Ver queja completa</a>
    </div>

    <div class="divider"></div>

    <p style="font-size: 13px; color: #6b7280; margin: 0;">
      <strong>Accion requerida:</strong> Por favor revisa esta queja y toma las medidas correspondientes segun el protocolo de {tenant.get("name", "la universidad")}.
    </p>
  </div>

  <div class="footer">
    <p>
      Enviado a: {", ".join(recipients)}<br>
      <strong>Sentinel AcademIA</strong> &middot; Multi-nube AWS + OCI
    </p>
    <p class="timestamp">
      {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
    </p>
  </div>
</div>
</body>
</html>'''
