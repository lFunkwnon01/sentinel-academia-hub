# Checklist de Implementaci&oacute;n - Sentinel AcademIA

> Documento de seguimiento. Marca cada `[ ]` conforme lo completes.
> Formato: `[x]` = hecho, `[ ]` = pendiente, `[~]` = en progreso

---

## Progreso General

| Fase | Items | Completados | Progreso |
|---|---|---|---|
| **Fase 0: Setup** | 20 | 0/20 | 0% `[~]` |
| **Fase 1: Backend Core** | 25 | 0/25 | 0% |
| **Fase 2: Backend LLM** | 20 | 0/20 | 0% |
| **Fase 3: Frontend** | 15 | 0/15 | 0% |
| **Fase 4: Archivos + Email** | 10 | 0/10 | 0% |
| **Fase 5: RAG** (opcional) | 8 | 0/8 | 0% |
| **Fase 6: Testing** | 10 | 0/10 | 0% |
| **Fase 7: Deploy Final** | 8 | 0/8 | 0% |
| **TOTAL** | **116** | **0/116** | **0%** |

---

# FASE 0: Setup Inicial (1-2 horas)

> Objetivo: tener todas las herramientas instaladas y configuradas, poder conectarte a AWS Academy y Oracle OCI desde tu terminal.

## 0.1 Herramientas locales

- [x] **Python 3.14.3** instalado y verificado (`python3 --version`) — Python 3.14.3
- [x] **Node.js 20+** instalado y verificado (`node --version`) — v24.16.0
- [x] **AWS CLI v2** instalado y verificado (`aws --version`)
- [x] **SAM CLI** instalado y verificado (`sam --version`)
- [x] **OCI CLI** instalado y verificado (`oci --version`) — 3.87.0
- [x] **Git** configurado con tu nombre y email (`git --version`) — 2.54.0
- [x] **Tectonic** instalado (para compilar PDFs LaTeX si necesitas) — 0.16.9

**Verificaci&oacute;n**:
```bash
python3.12 --version   # Python 3.12.x
node --version        # v20.x o v22.x
aws --version         # aws-cli/2.x
sam --version         # SAM CLI, version 1.x
oci --version         # 2.x.x
git --version         # 2.x
```

## 0.2 AWS Academy

- [x] **Credenciales nuevas** obtenidas (AWS Details &rarr; Show)
- [x] **AWS CLI configurado** via variables de entorno (Account: 227165337884)
- [x] **Verificar identidad** con `aws sts get-caller-identity` — OK
- [x] **Verificar region** es `us-east-1` con `aws configure get region`
- [x] **Bucket S3 para SAM** creado (`sentinel-sam-artifacts-1781951709`)

**Verificaci&oacute;n**:
```bash
aws sts get-caller-identity
# Debe mostrar tu Account ID y Arn

aws s3 mb s3://sentinel-sam-artifacts-$(date +%s) --region us-east-1
# Guardar el nombre del bucket
```

## 0.3 Oracle OCI

- [x] **API key generada** en OCI Console (User Settings &rarr; API Keys)
- [x] **OCI CLI configurado** en `~/.oci/config` (region: us-chicago-1)
- [x] **Compartment creado** con nombre "SentinelAcademia" (OCID validado)
- [x] **Probar Cohere Command R** con un comando de prueba — **"¡Hola!"** (Cohere v1)
- [x] **Probar Gemini como fallback** — **OK** (formato TextContent)
- [x] **LLM router con fallback** — Cohere primary, Gemini fallback (skill actualizado)

**Verificaci&oacute;n**:
```bash
oci iam region-subscription list

oci generative-ai-inference generate-text \
  --compartment-id $OCI_COMPARTMENT_ID \
  --serving-mode '{"modelId":"cohere.command-r","servingType":"ON_DEMAND"}' \
  --inference-request '{"prompt":"Di hola","maxTokens":20}'
```

## 0.4 Repo y dependencias

- [ ] **Repo clonado** o descargado
- [ ] **Frontend deps** instaladas (`cd web && npm install`)
- [ ] **Tectonic verificado** (opcional, para PDFs)

**Definition of Done Fase 0**:
- Todos los comandos de verificaci&oacute;n pasan sin error
- `aws sts get-caller-identity` retorna tu identidad
- `oci generative-ai-inference` responde con un JSON

---

# FASE 1: Backend Core (3-4 horas)

> Objetivo: implementar las Lambdas b&aacute;sicas (CRUD) y desplegarlas en AWS. Sin LLM a&uacute;n.

## 1.1 Setup del proyecto Python

- [ ] **Estructura de carpetas** creada (`src/handlers/_shared/`, `src/services/`, `src/tests/`)
- [ ] **`requirements.txt`** con boto3, pydantic, aws-lambda-powertools, etc.
- [ ] **Entorno virtual** creado (`python3.12 -m venv .venv`)
- [ ] **Dependencias instaladas** (`pip install -r requirements.txt`)
- [ ] **`.env`** configurado con las variables de entorno

**Comando**:
```bash
cd src
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 1.2 Shared modules

- [ ] **`config.py`** con `Settings` de pydantic-settings
- [ ] **`logger.py`** con aws-lambda-powertools
- [ ] **`http_response.py`** con `ok()`, `accepted()`, `bad_request()`, `not_found()`, `server_error()`
- [ ] **`errors.py`** con `@with_error_handling` decorator
- [ ] **`schemas.py`** con `CreateQuejaInput`, `QuejaAccepted`, enums, etc.

**Verificaci&oacute;n**:
```bash
cd src
python3.12 -c "from handlers._shared.schemas import CreateQuejaInput; print('OK')"
```

## 1.3 Lambda createQueja (la m&aacute;s importante)

- [ ] **`handlers/create_queja.py`** implementado
- [ ] **Validaci&oacute;n Pydantic** de input
- [ ] **PutItem en DynamoDB** con multi-tenant (`pk = TENANT#...#QUEJA#...`)
- [ ] **SendMessage a SQS** con correlation ID
- [ ] **Test escrito** que valida el flujo completo

**Verificaci&oacute;n local**:
```bash
cd src
pytest tests/handlers/test_create_queja.py -v
```

## 1.4 Lambdas de lectura (read pattern)

- [ ] **`handlers/get_queja.py`** (GET /api/quejas/:id con GSI_ById)
- [ ] **`handlers/list_quejas.py`** (GET /api/quejas con GSI_ByTenant)
- [ ] **`handlers/get_analysis.py`** (GET /api/quejas/:id/analysis)
- [ ] **`handlers/get_metrics.py`** (GET /api/dashboard/metrics)

**Verificaci&oacute;n**:
```bash
pytest tests/handlers/test_get_queja.py tests/handlers/test_list_quejas.py -v
```

## 1.5 SAM template + primer deploy

- [ ] **`src/infra/template.yaml`** con las 4 Lambdas anteriores + tabla DynamoDB
- [ ] **`sam build`** exitoso
- [ ] **`sam deploy --guided`** primera vez (guardar `samconfig.toml`)
- [ ] **Smoke test** del API desplegado con `curl`
- [ ] **Ver outputs** del stack (`ApiUrl`, `TableName`)

**Verificaci&oacute;n**:
```bash
cd src/infra
sam build
sam deploy

# Test
API_URL=$(aws cloudformation describe-stacks --stack-name sentinel-academia-dev --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text)
curl -X POST $API_URL/quejas \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Test","descripcion":"Descripcion suficientemente larga","categoriaDeclarada":"OTRA"}'
# Debe responder 202 con quejaId
```

**Definition of Done Fase 1**:
- `sam deploy` exitoso
- `POST /api/quejas` responde 202
- `GET /api/quejas/:id` responde 200
- Item aparece en DynamoDB con `tenantId`

---

# FASE 2: Backend LLM (3-4 horas)

> Objetivo: integrar OCI Generative AI con circuit breaker y fallback. La queja se analiza autom&aacute;ticamente.

## 2.1 Cliente OCI

- [ ] **`services/oci_genai.py`** con clase `OCIGenAIClient`
- [ ] **M&eacute;todo `generate_text()`** implementado con Cohere Command R
- [ ] **M&eacute;todo `chat()`** implementado con historial
- [ ] **Tests con `responses`** que mockean HTTP a OCI

**Verificaci&oacute;n**:
```bash
cd src
python3.12 -c "from services.oci_genai import OCIGenAIClient; print('OK')"
pytest tests/services/test_oci_genai.py -v
```

## 2.2 LLM Router con circuit breaker

- [ ] **`services/llm_router.py`** con `generate_with_fallback()`
- [ ] **Circuit breaker** con `opossum` por modelo (3 breakers)
- [ ] **Cadena**: cohere-r &rarr; llama-3.1 &rarr; command-r-plus &rarr; respuesta controlada
- [ ] **Logging** de cada intento (modelo, latencia, tokens, error)
- [ ] **Test de fallback** (Cohere falla &rarr; usa Llama)

**Verificaci&oacute;n**:
```bash
pytest tests/services/test_llm_router.py -v
# Test: Cohere falla -> Llama responde
```

## 2.3 Prompts estructurados

- [ ] **System prompt** para an&aacute;lisis de quejas (en `services/prompts.py`)
- [ ] **Validaci&oacute;n con Zod** del output (extraer JSON de markdown si es necesario)
- [ ] **Test con 3-5 quejas reales** que valide la consistencia del output

**Verificaci&oacute;n**:
```bash
cd src
python3.12 -c "
from services.structured_analysis import analizar_queja
result = analizar_queja('Un profesor no asistio a clases y nadie nos informa')
print(result.criticidad, result.categoria)
"
```

## 2.4 Lambda processQueja (consumer SQS)

- [ ] **`handlers/process_queja.py`** con BatchProcessor
- [ ] **Idempotencia** con SHA-256 del input
- [ ] **Llamada al LLM** con fallback
- [ ] **Guardar an&aacute;lisis** como item hijo (`sk = ANALYSIS#timestamp`)
- [ ] **Emitir evento** a EventBridge

**Verificaci&oacute;n**:
```bash
# Crear queja -> esperar 30s -> ver analisis en DynamoDB
aws dynamodb query --table-name quejas --key-condition-expression "begins_with(pk, :pk)" --expression-attribute-values '{":pk":{"S":"TENANT#universidad-ejemplo#QUEJA#"}}'
```

## 2.5 Lambda chat (RAG b&aacute;sico)

- [ ] **`handlers/chat.py`** implementado
- [ ] **Validaci&oacute;n** de input
- [ ] **Llamada al LLM** con contexto

**Verificaci&oacute;n**:
```bash
curl -X POST $API_URL/chat -H "Content-Type: application/json" \
  -d '{"question":"Cual es el proceso de queja?"}'
# Debe responder 200 con answer
```

**Definition of Done Fase 2**:
- Una queja creada se analiza autom&aacute;ticamente en &lt;60 segundos
- El item ANALYSIS aparece en DynamoDB
- Si OCI est&aacute; ca&iacute;do, el fallback a Llama funciona
- Logs estructurados visibles en CloudWatch

---

# FASE 3: Frontend Vue 3 (2-3 horas)

> Objetivo: frontend funcional desplegado en Vercel, conectado al backend.

## 3.1 Setup

- [ ] **`web/.env.local`** con `VITE_API_URL`
- [ ] **Mock de Prism corriendo** en `:4010`
- [ ] **`npm run dev`** levanta el frontend en `:5173`
- [ ] **Form de queja** funcional contra el mock

**Verificaci&oacute;n**:
```bash
cd web
npm run dev
# Abrir http://localhost:5173
# Llenar form, ver que llega al mock
```

## 3.2 Services y composables

- [ ] **`services/apiClient.ts`** con interceptors (correlationId, errores)
- [ ] **`services/quejaService.ts`** con todos los endpoints
- [ ] **`composables/useQuejas.ts`** con state management
- [ ] **`composables/useChat.ts`** con manejo de mensajes

**Verificaci&oacute;n**:
```bash
cd web
npx tsc --noEmit
# 0 errores
```

## 3.3 Vistas

- [ ] **HomeView** con hero y features
- [ ] **QuejaView** con form + success state
- [ ] **DashboardView** con KPIs y gr&aacute;ficos
- [ ] **ChatView** con chat interactivo
- [ ] **Responsive** mobile (probar en DevTools)

**Verificaci&oacute;n**:
```bash
cd web
npm run build
# 0 errores
npm run preview
# Probar todas las rutas
```

## 3.4 Deploy a Vercel

- [ ] **Cuenta en Vercel** creada
- [ ] **Vercel CLI** instalado (`npm install -g vercel`)
- [ ] **Deploy** con `vercel --prod` o conectando el repo
- [ ] **URL p&uacute;blica** funcionando

**Verificaci&oacute;n**:
```bash
cd web
vercel --prod
# Output: Production: https://sentinel-academia-xxx.vercel.app
```

**Definition of Done Fase 3**:
- Frontend deployado y accesible p&uacute;blicamente
- Form de queja funciona end-to-end
- Dashboard muestra datos del backend real
- Chat responde con el LLM

---

# FASE 4: Archivos + Email (2 horas)

> Objetivo: uploads a S3, procesamiento de adjuntos, emails de alerta.

## 4.1 S3 bucket

- [ ] **Bucket S3** creado (`sentinel-quejas-adjuntos`)
- [ ] **CORS configurado** para el frontend
- [ ] **Lifecycle policy** para archivos antiguos

**Verificaci&oacute;n**:
```bash
aws s3 mb s3://sentinel-quejas-adjuntos --region us-east-1
aws s3api get-bucket-cors --bucket sentinel-quejas-adjuntos
```

## 4.2 Lambda getUploadUrl

- [ ] **`handlers/get_upload_url.py`** implementado
- [ ] **Presigned URL** generada con expiraci&oacute;n de 5 min
- [ ] **Test** que verifica que la URL funciona

**Verificaci&oacute;n**:
```bash
curl -X POST $API_URL/uploads/presigned \
  -H "Content-Type: application/json" \
  -d '{"quejaId":"q-test","filename":"test.pdf","contentType":"application/pdf"}'
# Responde con uploadUrl
```

## 4.3 Lambda fileProcessor

- [ ] **`handlers/file_processor.py`** (consumer SQS de S3 events)
- [ ] **OCI Document AI** extrae texto del PDF/imagen
- [ ] **Guardar texto** en item ATTACHMENT

**Verificaci&oacute;n**:
```bash
# Subir archivo a S3 -> esperar 30s -> ver texto extraido
```

## 4.4 Lambda notifyByEmail (SES)

- [ ] **Email identity verificada** en SES (o usar sandbox)
- [ ] **`handlers/notify.py`** implementado
- [ ] **SNS topic** configurado con suscripci&oacute;n
- [ ] **Email se env&iacute;a** cuando criticidad=CRITICA

**Verificaci&oacute;n**:
```bash
# Crear queja con keywords de acoso
# Esperar 30s
# Verificar email recibido en bienestar@...
```

**Definition of Done Fase 4**:
- Upload de PDF funciona end-to-end
- Texto extraido aparece en DynamoDB
- Email llega cuando hay caso cr&iacute;tico

---

# FASE 5: RAG (Opcional, 2-3 horas)

> Objetivo: el chat pueda responder preguntas sobre el reglamento universitario usando RAG.

## 5.1 Ingesta de documentos

- [ ] **Documento del reglamento** subido a S3
- [ ] **Chunking** (500 chars, overlap 50)
- [ ] **Embeddings** con Cohere `embed-multilingual-v3.0`

## 5.2 Vector store

- [ ] **Tabla `rag_chunks`** en DynamoDB
- [ ] **Guardar chunks + embeddings** con metadata

## 5.3 Retrieval + chat

- [ ] **B&uacute;squeda por similitud** (cosine similarity)
- [ ] **Top-K chunks** en el prompt del LLM
- [ ] **Citaciones** en la respuesta

**Verificaci&oacute;n**:
```bash
curl -X POST $API_URL/chat -d '{"question":"Cual es el articulo 5 del reglamento?"}'
# Debe responder con citaciones
```

**Definition of Done Fase 5**:
- El chat responde preguntas sobre el reglamento
- Incluye citaciones de los art&iacute;culos relevantes

---

# FASE 6: Testing (1-2 horas)

> Objetivo: tests comprehensivos que garanticen calidad.

## 6.1 Unit tests

- [ ] **Tests para cada Lambda** (happy path)
- [ ] **Tests de validaci&oacute;n** (input inv&aacute;lido)
- [ ] **Tests de idempotencia** en processQueja
- [ ] **Tests de fallback** del LLM router
- [ ] **Tests de presigned URL**

**Verificaci&oacute;n**:
```bash
cd src
pytest --cov=. --cov-report=term-missing
# Coverage > 70%
```

## 6.2 Integration tests

- [ ] **Test end-to-end** crear queja &rarr; esperar &rarr; ver an&aacute;lisis
- [ ] **Test de email** con SES mock
- [ ] **Test de upload** con S3 mock

## 6.3 Coverage y quality

- [ ] **Coverage** > 70% en l&oacute;gica de negocio
- [ ] **mypy strict** sin errores
- [ ] **ruff** sin warnings

**Verificaci&oacute;n**:
```bash
cd src
mypy . --strict
ruff check .
pytest --cov=. --cov-fail-under=70
```

**Definition of Done Fase 6**:
- `pytest` pasa con >70% coverage
- `mypy --strict` sin errores
- `ruff check` sin warnings

---

# FASE 7: Deploy Final (1 hora)

> Objetivo: deploy en producci&oacute;n, smoke tests, video demo.

## 7.1 Deploy AWS

- [ ] **`sam build && sam deploy`** en producci&oacute;n
- [ ] **Variables de entorno** configuradas
- [ ] **CloudWatch alarms** activas

**Verificaci&oacute;n**:
```bash
cd src/infra
sam build && sam deploy
```

## 7.2 Smoke tests end-to-end

- [ ] **POST /api/quejas** responde 202
- [ ] **An&aacute;lisis LLM** se completa en &lt;60s
- [ ] **Dashboard** muestra la queja
- [ ] **Chat** responde con informaci&oacute;n
- [ ] **Email de cr&iacute;tica** llega al destinatario

**Verificaci&oacute;n**:
```bash
# Ejecutar el script de smoke test completo
bash scripts/smoke-test-e2e.sh
```

## 7.3 Video demo

- [ ] **Video de 2-3 minutos** grabado (form de queja, dashboard, chat)
- [ ] **Subido a YouTube/Loom** (unlisted o public)
- [ ] **Link agregado** al README

**Definition of Done Fase 7**:
- Backend deployado y funcional
- Frontend deployado en Vercel
- Video demo listo
- Todos los criterios de la r&uacute;brica cumplidos

---

# Resumen de Comandos R&aacute;pidos

```bash
# Backend
cd src
source .venv/bin/activate
pytest                          # Tests
sam build && sam deploy          # Deploy
sam logs -n CreateQuejaFunction --tail   # Logs

# Frontend
cd web
npm run dev                     # Dev
npm run build                   # Build
vercel --prod                   # Deploy

# Documentacion
bash scripts/serve-docs.sh      # Redoc en :8080
npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010 --dynamic  # Mock
bash scripts/test-mock.sh       # Test mock
```

---

# Comandos de Verificaci&oacute;n por Fase

| Fase | Comando de verificaci&oacute;n |
|---|---|
| **0** | `aws sts get-caller-identity && oci --version` |
| **1** | `curl -X POST $API_URL/quejas -d '...'` debe responder 202 |
| **2** | Crear queja &rarr; esperar &rarr; `aws dynamodb query` muestra ANALYSIS |
| **3** | Abrir URL de Vercel y ver el form |
| **4** | Subir PDF &rarr; ver texto extraido en DynamoDB |
| **5** | Chat responde con citaciones |
| **6** | `pytest --cov` &gt; 70% |
| **7** | `bash scripts/smoke-test-e2e.sh` todo verde |

---

# &Aacute;rea de Notas

Usa este espacio para anotar decisiones, problemas encontrados, o cosas para revisar despu&eacute;s:

```




```

---

# Historial de Iteraciones

## Iteraci&oacute;n 1 - [FECHA]
**Completado**:
- [ ] 

**En progreso**:
- [ ] 

**Problemas encontrados**:
-

**Decisiones tomadas**:
-

**Pr&oacute;xima iteraci&oacute;n**:
-
