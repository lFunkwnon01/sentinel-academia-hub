# Checklist de Resiliencia, Manejo de Limites y LLM

> Checklist de implementacion para el Criterio 3 de la rubrica.
> Ir marcando `[x]` conforme se implemente cada item.
> Documento completo: `resiliencia.pdf`

---

## Indice
1. [Timeouts](#1-timeouts)
2. [Circuit Breaker](#2-circuit-breaker)
3. [Fallback Chain LLM](#3-fallback-chain-llm)
4. [Rate Limiting](#4-rate-limiting)
5. [Retry con Exponential Backoff](#5-retry-con-exponential-backoff)
6. [Idempotencia](#6-idempotencia)
7. [Dead Letter Queues](#7-dead-letter-queues)
8. [Validacion Zod del LLM](#8-validacion-zod-del-llm)
9. [Logging Estructurado](#9-logging-estructurado)
10. [Observabilidad](#10-observabilidad)
11. [Costos y Monitoreo](#11-costos-y-monitoreo)
12. [Tests](#12-tests)
13. [Verificacion Final](#13-verificacion-final)

---

## 1. Timeouts

- [ ] Timeout configurado en `DynamoDBClient` (5s request, 2s connection)
- [ ] Timeout configurado en `S3Client` (10s request, 3s connection)
- [ ] Timeout configurado en `SQSClient` (10s)
- [ ] Timeout configurado en `EventBridgeClient` (5s)
- [ ] Timeout configurado en `SNSClient` (10s)
- [ ] Timeout configurado en `OCI GenAI` (30s via AbortController)
- [ ] Timeout configurado en `OCI Document AI` (60s via AbortController)
- [ ] Timeout configurado en `SES` (10s)
- [ ] Variables de entorno para timeouts externalizados
- [ ] Validacion de timeouts en tests (mockear latencia > timeout)

## 2. Circuit Breaker

- [ ] Paquete `opossum` instalado: `npm install opossum`
- [ ] Circuit breaker configurado para `cohere.command-r`
- [ ] Circuit breaker configurado para `meta.llama-3.1-70b-instruct`
- [ ] Circuit breaker configurado para `cohere.command-r-plus`
- [ ] Configuracion: `timeout: 30000`, `errorThresholdPercentage: 50`
- [ ] Configuracion: `resetTimeout: 30000`, `volumeThreshold: 5`
- [ ] Event listeners implementados (`open`, `halfOpen`, `close`, `reject`, `timeout`, `failure`)
- [ ] Metricas del circuit breaker expuestas a CloudWatch (custom metrics)
- [ ] CloudWatch Alarm cuando circuit breaker este abierto por >5 min
- [ ] Test del circuit breaker (simular fallos, verificar que abre)

## 3. Fallback Chain LLM

- [ ] Funcion `generateWithFallback()` implementada en `src/services/llmRouter.ts`
- [ ] Cadena: `cohere.command-r` -> `meta.llama-3.1-70b-instruct` -> `cohere.command-r-plus`
- [ ] Cada nivel envuelto en try/catch independiente
- [ ] Si todos fallan, retorna respuesta controlada (`safeDefaultResponse()`)
- [ ] Logging en cada intento: `modelo`, `latencyMs`, `inputTokens`, `outputTokens`
- [ ] Test: simular fallo del primer modelo, verificar que cae al segundo
- [ ] Test: simular fallo de todos, verificar respuesta controlada
- [ ] Test: verificar que modelos retornan JSON parseable

## 4. Rate Limiting

- [ ] Paquete `rate-limiter-flexible` instalado
- [ ] Rate limiter por `userId` (100 req/min)
- [ ] Rate limiter por `ip` (200 req/min)
- [ ] Implementado en handler `createQueja` (POST /api/quejas)
- [ ] Implementado en handler `chat` (POST /api/chat)
- [ ] Implementado en handler `listQuejas` (GET /api/quejas)
- [ ] Respuesta 429 con header `Retry-After`
- [ ] Codigo de error `RATE_LIMITED` en cuerpo de respuesta
- [ ] Test: enviar 101 requests rapidas, verificar 429 en la 101
- [ ] Test: verificar header Retry-After

## 5. Retry con Exponential Backoff

- [ ] Paquete `p-retry` instalado
- [ ] Funcion `callWithRetry()` con retries=3, minTimeout=1000, maxTimeout=10000
- [ ] Backoff exponencial con factor=2
- [ ] Jitter aleatorio (`randomize: true`)
- [ ] Listener `onFailedAttempt` para logging
- [ ] NO reintentar en errores 4xx
- [ ] NO reintentar despues de 3 intentos
- [ ] Test: simular fallo transitorio, verificar exito en retry 2
- [ ] Test: simular fallo permanente, verificar excepcion despues de 3

## 6. Idempotencia

- [ ] Funcion `computeIdempotencyKey()` con SHA-256 del input normalizado
- [ ] Check de idempotencia antes de procesar (GetCommand en `IDEMPOTENCY#...`)
- [ ] Si ya procesado, skip y ACK del mensaje
- [ ] Transaccion atomica en DynamoDB (PutItem ANALYSIS + PutItem IDEMPOTENCY)
- [ ] `ConditionExpression: attribute_not_exists(pk)` en el Put de IDEMPOTENCY
- [ ] TTL configurado en items de IDEMPOTENCY (7 dias)
- [ ] Test: enviar el mismo mensaje 2 veces, verificar 1 sola ejecucion
- [ ] Test: race condition con 2 mensajes simultaneos

## 7. Dead Letter Queues

- [ ] DLQ creada para `complaints-queue` (`complaints-dlq`)
- [ ] RedrivePolicy con `maxReceiveCount: 3`
- [ ] VisibilityTimeout = 6x el timeout de la Lambda
- [ ] ReportBatchItemFailures habilitado en consumer
- [ ] CloudWatch Alarm: `complaints-dlq-not-empty`
- [ ] Alarm suscrita a SNS topic de alertas
- [ ] Playbook para inspeccionar DLQ (documentado en README)
- [ ] Test: forzar 3 fallos del consumer, verificar mensaje en DLQ
- [ ] Test: replay de mensaje de DLQ (manual)

## 8. Validacion Zod del LLM

- [ ] Schema Zod estricto con `.strict()` para rechazar campos extra
- [ ] Todos los campos requeridos marcados con `min/max`
- [ ] Enums para `categoria`, `criticidad`, `sentimiento`
- [ ] Funcion `extractJson()` para limpiar output del LLM (markdown, texto extra)
- [ ] Funcion `analizarQueja()` con `safeParse()` y logging de errores
- [ ] Si la validacion falla, NO guardar el analisis
- [ ] Si la validacion falla, retry (max 3) o ir a DLQ
- [ ] Test: output con markdown embebido -> extrae correctamente
- [ ] Test: output con campo faltante -> rechaza
- [ ] Test: output con campo extra -> rechaza (strict)
- [ ] Test: output con tipo incorrecto -> rechaza

## 9. Logging Estructurado

- [ ] Logger con formato JSON obligatorio
- [ ] Campos: `timestamp`, `level`, `message`, `service`, `correlationId`
- [ ] Logger en `src/handlers/_shared/logger.ts`
- [ ] Correlation ID extraido de header `x-correlation-id` o generado
- [ ] Correlation ID en respuestas HTTP (header de salida)
- [ ] Correlation ID en mensajes SQS (MessageAttribute)
- [ ] Correlation ID en TODOS los logs de un request
- [ ] CERO `console.log` en el codigo (solo `logger`)
- [ ] NUNCA loggear secrets, PII, tokens
- [ ] Test: request genera logs con mismo correlationId

## 10. Observabilidad

- [ ] CloudWatch Logs configurado con retention de 14 dias
- [ ] X-Ray tracing activo en todas las Lambdas (`Tracing: Active` en SAM)
- [ ] Subsegments de X-Ray para llamadas a OCI y DynamoDB
- [ ] CloudWatch Metrics custom para:
  - [ ] `LlmTokensInput` (count, por modelo)
  - [ ] `LlmTokensOutput` (count, por modelo)
  - [ ] `LlmCost` (USD, por modelo)
  - [ ] `LlmLatency` (ms, por modelo)
  - [ ] `CircuitBreakerState` (0/1, por breaker)
  - [ ] `QuejasCreated` (count, por categoria/criticidad)
  - [ ] `DlqMessages` (count, por cola)
- [ ] CloudWatch Dashboard `sentinel-academia` creado
- [ ] SNS Topic `sentinel-alerts` con suscriptores (email/SMS)
- [ ] CloudWatch Alarms:
  - [ ] `lambda-errors-high` (>5 errores en 3 min)
  - [ ] `dlq-not-empty` (cualquier mensaje en DLQ)
  - [ ] `llm-cost-spike` (>$1/dia)
  - [ ] `api-latency-p95-high` (>3s p95)
- [ ] Langfuse integrado con tracing de LLM calls
- [ ] Langfuse: capturar prompt, output, tokens, latency, modelo
- [ ] Langfuse: `flushAsync()` en cada llamada
- [ ] CloudWatch Logs Insights queries documentadas en README

## 11. Costos y Monitoreo

- [ ] Estimacion de tokens consumidos (chars/4)
- [ ] Calculo de costo por llamada (input/output tokens * precio modelo)
- [ ] CloudWatch Metric `LlmCost` por modelo
- [ ] AWS Budget configurado ($5 USD/mes, alerta al 80%)
- [ ] Test: 100 quejas procesadas -> verificar metricas correctas
- [ ] Dashboard muestra costo acumulado vs budget
- [ ] Documentacion: `docs/05-repo-deploy/costos.md` con estimacion detallada

## 12. Tests

- [ ] Tests unitarios para `llmRouter.ts` (fallback chain, safe default)
- [ ] Tests unitarios para `rateLimiter.ts`
- [ ] Tests unitarios para `idempotency.ts` (hash, check)
- [ ] Tests unitarios para `analisis` (Zod parse, extract JSON)
- [ ] Tests con mocks de `ociGenai` (no llamadas reales)
- [ ] Tests con mocks de `dynamoClient` (no llamadas reales)
- [ ] Tests de integracion con LocalStack (SQS + DynamoDB)
- [ ] Coverage > 60% en logica de negocio
- [ ] Coverage > 80% en `llmRouter.ts`, `rateLimiter.ts`, `idempotency.ts`

## 13. Verificacion Final

- [ ] Todas las Lambdas pasan `npm run typecheck`
- [ ] Todas las Lambdas pasan `npm run lint`
- [ ] Todos los tests pasan `npm run test`
- [ ] `sam validate` sin errores
- [ ] `sam build` exitoso
- [ ] `sam deploy --guided` a dev exitoso
- [ ] Smoke test: POST /api/quejas -> 202 en <500ms
- [ ] Smoke test: consumer procesa en <30s
- [ ] Smoke test: criticidad=CRITICA -> alerta en <1min
- [ ] DLQ vacia despues de pruebas
- [ ] CloudWatch Dashboard muestra metricas
- [ ] Langfuse muestra traces
- [ ] Budget alert funciona (test: generar trafico para cruzar 80%)
- [ ] Documento `resiliencia.pdf` compila sin errores
- [ ] Checklist completo al 100%

---

## Metricas de Exito (SLA objetivo)

| Metrica | Objetivo |
|---|---|
| Tasa de exito en procesamiento | >= 99% |
| Tiempo de procesamiento (p95) | < 30s |
| Latencia del LLM (p95) | < 20s |
| Disponibilidad | >= 99.5% |
| Deteccion de caso critico | < 60s end-to-end |
| Falsos positivos (CRITICA) | < 10% |
| DLQ vacia | 100% del tiempo |
| Circuit breaker cerrado | >= 95% del tiempo |
| Costo por queja | < $0.001 USD |
| Budget alert | Funciona |

---

## Referencias

- PDF: [`resiliencia.pdf`](resiliencia.pdf) - Documento completo en LaTeX
- Diagrama: [`diagrams/flujo-resiliencia.png`](diagrams/flujo-resiliencia.png)
- Skills relevantes:
  - `oci-generative-ai/SKILL.md`
  - `event-driven-pattern/SKILL.md`
  - `unit-testing-patterns/SKILL.md`
  - `observability-stack/SKILL.md`
