# Changelog

Todos los cambios notables de este proyecto ser&aacute;n documentados en este archivo.

El formato est&aacute; basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.1.0] - 2025-XX-XX

### Added (a&ntilde;adido)
- **Backend serverless** en AWS Academy con 9 Lambdas especializadas
  - `createQueja` - Recepci&oacute;n de quejas (POST /api/quejas)
  - `getQueja` - Detalle de queja
  - `listQuejas` - Listado con filtros
  - `getAnalysis` - Resultado del an&aacute;lisis LLM
  - `getMetrics` - M&eacute;tricas para dashboard
  - `chat` - Chat con RAG
  - `processQueja` - Consumer de SQS (an&aacute;lisis async)
  - `notifyStudent` - Consumer de SNS
  - `updateDashboard` - Consumer de EventBridge
- **Multi-nube real**: AWS (orquestaci&oacute;n) + Oracle OCI (LLM)
- **LLM con fallback chain**:
  - Primary: Cohere Command R
  - Fallback: Meta Llama 3.1 70B Instruct
  - Terciario: Cohere Command R+
  - Degradado: respuesta controlada
- **Resiliencia**:
  - Circuit breaker con opossum
  - Rate limiting (token bucket) con rate-limiter-flexible
  - Retry con exponential backoff + jitter (p-retry)
  - Idempotencia con SHA-256 + DynamoDB conditional writes
  - Dead Letter Queues con alarmas CloudWatch
  - Timeouts en TODA llamada externa
  - Validaci&oacute;n Zod estricta del output del LLM
- **Observabilidad**:
  - Logging estructurado JSON con correlationId
  - X-Ray tracing distribuido
  - CloudWatch Metrics custom
  - Langfuse para tracing de LLM
  - CloudWatch Alarms + SNS para notificaciones
- **Frontend Vue 3**:
  - Home con hero, features y stack
  - Form de queja con validaci&oacute;n Zod
  - Dashboard con KPIs y gr&aacute;ficos
  - Chat IA con markdown y fuentes citables
  - Composables y services con TypeScript estricto
  - CSS nativo con custom properties (sin Tailwind)
  - Responsive mobile-first
  - Accesibilidad b&aacute;sica (WCAG AA)
- **Documentaci&oacute;n completa**:
  - Contexto del problema (LaTeX → PDF, 5 p&aacute;ginas)
  - Arquitectura (4 diagramas Mermaid C4 + justificaciones)
  - Resiliencia + LLM (LaTeX → PDF, 16+ p&aacute;ginas con c&oacute;digo)
  - Checklist de 100+ items de implementaci&oacute;n
  - Manual de deploy paso a paso
  - Estimaci&oacute;n de costos
  - OpenAPI spec completo (7 endpoints)
- **Infraestructura como c&oacute;digo**:
  - AWS SAM (template.yaml)
  - GitHub Actions CI pipeline
- **Configuraci&oacute;n opencode**:
  - 5 agents especializados
  - 7 reglas modulares
  - 16 skills con procedimientos
  - 4 MCPs integrados

### Security
- Validaci&oacute;n de TODA entrada con Zod
- Correlation ID obligatorio en headers
- CORS configurado en API Gateway
- Rate limiting para prevenir abuso
- Secrets en AWS Secrets Manager (no en c&oacute;digo)
- Anonimizaci&oacute;n de personas en el an&aacute;lisis LLM

### Notes
- Versi&oacute;n inicial del proyecto (hackat&oacute;n)
- Costo total estimado hackat&oacute;n: < $2 USD
- Costo estimado producci&oacute;n (5000 quejas/mes): ~$33 USD
- vs. arquitectura con Claude Sonnet 4: ~$200/mes (10x m&aacute;s caro)
