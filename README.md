# Sentinel AcademIA

> Plataforma de quejas universitarias con IA — Hackathon 2026

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)]()
[![AWS](https://img.shields.io/badge/AWS-Cloud-orange)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-50%2F50%20passing-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

Plataforma serverless para gesti&oacute;n de quejas universitarias con an&aacute;lisis autom&aacute;tico
mediante IA generativa (Cohere v&iacute;a OCI). Backend en AWS (Lambda + DynamoDB + SQS + S3)
+ chatbot RAG + frontend Vue 3.

---

## &Iacute;ndice

- [Arquitectura](#arquitectura)
- [Stack tecnol&oacute;gico](#stack-tecnol&oacute;gico)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Setup local](#setup-local)
- [Deploy en AWS](#deploy-en-aws)
- [Configuraci&oacute;n de OCI](#configuraci&oacute;n-de-oci)
- [Endpoints de la API](#endpoints-de-la-api)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)
- [Tutorials paso a paso](#tutorials-paso-a-paso)

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND (Vue 3)                       │
│              S3 static website hosting (HTTP)                │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────┐
│                    API GATEWAY (REST)                        │
│   /health  /api/quejas  /api/quejas/{id}  /api/chat         │
└──────────┬──────────┬──────────┬──────────┬─────────────────┘
           │          │          │          │
     ┌─────▼──┐  ┌────▼───┐ ┌────▼────┐ ┌──▼──────┐
     │create  │  │get/list│ │upload-  │ │ chat   │
     │ queja  │  │ queja  │ │   url   │ │ (RAG)  │
     └────┬───┘  └───┬────┘ └────┬────┘ └──┬──────┘
          │          │           │         │
          ▼          ▼           ▼         ▼
    ┌─────────────────────────────────────┐
    │         DYNAMODB (single-table)       │
    │    PK: TENANT#{tid}#QUEJA#{qid}     │
    │    GSI: StatusByDate                 │
    └─────────────────────────────────────┘
                    ▲
                    │ update
    ┌───────────────┴───────────────────────┐
    │     SQS (AnalysisQueue + DLQ)         │
    └───────────────┬───────────────────────┘
                    │ trigger
    ┌───────────────▼───────────────────────┐
    │  analyze_queja Lambda (SQS consumer) │
    │  1. Get queja from DynamoDB           │
    │  2. Call LLM (Cohere/Mock)           │
    │  3. Update status to ANALIZADA        │
    └───────────────────────────────────────┘
                    │
    ┌───────────────▼───────────────────────┐
    │  S3 Bucket (FilesBucket)              │
    │  evidence files via presigned URLs    │
    │  S3 event -> file_processor Lambda    │
    └───────────────────────────────────────┘
                    ▲
                    │ presigned URL
    ┌───────────────▼───────────────────────┐
    │  upload_url Lambda (POST endpoint)    │
    │  Returns presigned PUT URL (15min)    │
    └───────────────────────────────────────┘

    ┌───────────────────────────────────────┐
    │  OCI (Oracle Cloud)                   │
    │  - Object Storage (reglamento.txt)   │
    │  - Generative AI (Cohere Command)    │
    │  - Knowledge base for RAG            │
    └───────────────────────────────────────┘
```

---

## Stack tecnol&oacute;gico

### Backend (Python 3.12)
- **AWS Lambda** — 7 funciones serverless
- **API Gateway REST** — endpoints HTTP
- **DynamoDB** — single-table multi-tenant
- **SQS + DLQ** — cola as&iacute;ncrona para an&aacute;lisis
- **S3** — evidencia + frontend
- **Python 3.12** (Lambda runtime) + 3.14.3 (local con OCI)

### LLM (Oracle Cloud Infrastructure)
- **OCI Object Storage** — knowledge base
- **OCI Python SDK 2.179.0** — interacci&oacute;n
- **OCI Generative AI** (Cohere Command) — para producci&oacute;n
- **MockLLMClient** — para demo (no requiere oci package)
- **Reglamento.txt** — knowledge base del RAG

### Frontend (Vue 3)
- **Vue 3.4.21** + **TypeScript** estricto
- **Pinia** + **Vue Router 4**
- **Axios** + **Chart.js**
- **Vite** build tool
- **S3 static website hosting** (sin CloudFront)

### DevOps
- **AWS SAM** — Infrastructure as Code
- **moto 5.2.2** — mock de servicios AWS en tests
- **pytest 9.1.1** — 50 tests en 2.5 segundos
- **Tectonic** — compilador LaTeX

---

## Estructura del proyecto

```
sentinel-academia/
├── infra/
│   ├── template.yaml              # SAM template (IaC)
│   ├── samconfig.toml             # Configuracion de sam deploy
│   └── .aws-sam-new/              # Build artifacts (gitignored)
│
├── src/
│   ├── handlers/                  # 1 archivo = 1 Lambda
│   │   ├── _shared/               # 8 modulos compartidos
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # Pydantic settings
│   │   │   ├── logger.py          # powertools logger
│   │   │   ├── errors.py          # AppError + error_handler
│   │   │   ├── http_response.py   # HttpResponse + CORS
│   │   │   ├── correlation_id.py  # x-correlation-id middleware
│   │   │   ├── dynamo_client.py   # Multi-tenant wrapper
│   │   │   ├── schemas.py         # Pydantic models (OpenAPI-aligned)
│   │   │   └── auth.py            # extract_tenant_id
│   │   ├── __init__.py
│   │   ├── health_check.py        # GET /health
│   │   ├── create_queja.py        # POST /api/quejas
│   │   ├── get_queja.py           # GET /api/quejas/{id}
│   │   ├── list_quejas.py         # GET /api/quejas
│   │   ├── analyze_queja.py       # SQS consumer (LLM analysis)
│   │   ├── upload_url.py          # POST /api/quejas/{id}/upload-url
│   │   ├── file_processor.py      # S3 event consumer
│   │   └── chat.py                # POST /api/chat (RAG)
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── llm_client.py          # OCI Cohere + Mock LLM
│   │   ├── knowledge_service.py    # RAG retrieval
│   │   └── file_service.py        # S3 presigned URLs
│   │
│   ├── tests/                     # pytest + moto
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_shared.py
│   │   │   ├── test_dynamo_client.py
│   │   │   └── test_knowledge_service.py
│   │   └── integration/
│   │       └── test_handlers.py
│   │
│   └── requirements.txt           # Runtime deps
│
├── web/                           # Frontend Vue 3
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/
│   │   ├── stores/
│   │   ├── services/              # apiClient, quejaService, chatService
│   │   ├── composables/
│   │   ├── components/
│   │   ├── views/                 # Home, Queja, Chat, Dashboard
│   │   └── types/
│   ├── .env.production            # VITE_API_URL
│   ├── package.json
│   └── dist/                      # Build artifacts
│
├── knowledge/                     # RAG knowledge base
│   └── reglamento.txt
│
├── docs/                          # Documentation
│   ├── 00-tutorial-llm/           # Tutorial Fase 0 (OCI setup)
│   ├── 01-tutorial-fase1/         # Tutorial Fase 1 (Backend Core)
│   ├── 02-tutorial-fase2/         # Tutorial Fase 2 (LLM)
│   ├── 03-tutorial-fase3/         # Tutorial Fase 3 (Frontend)
│   ├── 04-tutorial-fase4/         # Tutorial Fase 4 (Files)
│   ├── 05-tutorial-fase5/         # Tutorial Fase 5 (RAG)
│   ├── 06-tutorial-fase6/         # Tutorial Fase 6 (Testing)
│   └── 07-tutorial-fase7/         # Tutorial Fase 7 (Deploy)
│
├── .opencode/                     # opencode config
│   ├── agents/
│   ├── rules/                     # 10 reglas
│   └── skills/                    # 16 skills
│
├── api-mock/
│   └── openapi.yaml               # API spec
│
├── pyproject.toml                 # Project config (Python)
├── package.json                   # Root scripts
├── README.md                      # Este archivo
├── LICENSE                        # MIT
└── CHANGELOG.md
```

---

## Setup local

### Requisitos previos

| Herramienta | Versi&oacute;n | Check |
|---|---|---|
| Python | 3.12+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| AWS CLI | 2.x | `aws --version` |
| SAM CLI | 1.162+ | `sam --version` |
| mise | 2026+ | `mise --version` |
| Tectonic | 0.16+ | `tectonic --version` |

### 1. Clonar el repositorio

```bash
git clone https://github.com/your-org/sentinel-academia.git
cd sentinel-academia
```

### 2. Instalar Python 3.12 (si no lo tienes)

```bash
mise use --global python@3.12
python3.12 --version
```

### 3. Instalar dependencias Python (para tests)

```bash
pip install pydantic pydantic-settings email-validator boto3 \
  aws-lambda-powertools[tracer,logger,metrics] orjson \
  pytest pytest-cov pytest-mock 'moto[dynamodb,s3,sqs]' \
  boto3-stubs[dynamodb,s3,sqs]
```

### 4. Instalar dependencias Node (para frontend)

```bash
cd web
npm install
```

### 5. Configurar credenciales AWS Academy

```bash
export AWS_ACCESS_KEY_ID="ASIAT..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="IQoJb3JpZ2luX2Vj..."
export AWS_DEFAULT_REGION="us-east-1"
export AWS_REGION="us-east-1"

# Verificar
aws sts get-caller-identity
```

> **Nota AWS Academy**: las credenciales expiran cada 3-4 horas. Para refrescarlas:
> 1. AWS Academy → End Lab → Start Lab
> 2. Esperar 1-2 minutos
> 3. Click "AWS Details" → "Show"
> 4. Copiar las 3 credenciales nuevas

### 6. Configurar OCI (Oracle Cloud)

El archivo `~/.oci/config` debe tener:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=33:c3:5e:8d:b7:d6:...
tenancy=ocid1.tenancy.oc1..aaaa...
compartment-id=ocid1.compartment.oc1..aaaa...
region=us-chicago-1
key_file=/home/youruser/.oci/private_key.pem
```

Y `private_key.pem` con permisos `chmod 600`.

### 7. Verificar la instalaci&oacute;n

```bash
# AWS
aws sts get-caller-identity

# OCI
~/lib/oracle-cli/bin/python3 -c "
import oci
print('OCI OK:', oci.config.from_file('~/.oci/config', 'DEFAULT')['user'])
"
```

---

## Deploy en AWS

### 1. Build del backend

```bash
cd infra
sam build --build-dir .aws-sam-new
```

### 2. Primer deploy (guided)

```bash
sam deploy --guided \
  --template-file .aws-sam-new/template.yaml \
  --stack-name sentinel-academia-dev \
  --s3-bucket YOUR-SAM-ARTIFACTS-BUCKET \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

Esto te preguntar&aacute;:
- Stack name: `sentinel-academia-dev`
- Parameter Stage: `dev`
- Parameter LogLevel: `INFO`
- Parameter AllowedOrigins: `*`
- Parameter LambdaRoleArn: `arn:aws:iam::ACCOUNT:role/LabRole`

### 3. Deploys subsecuentes (no-interactive)

```bash
sam deploy \
  --stack-name sentinel-academia-dev \
  --template-file .aws-sam-new/template.yaml \
  --s3-bucket YOUR-SAM-ARTIFACTS-BUCKET \
  --capabilities CAPABILITY_IAM \
  --no-disable-rollback \
  --no-confirm-changeset
```

### 4. Configurar notificaci&oacute;n S3 (post-deploy)

Por la circular dependency, esto se hace manual:

```bash
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name sentinel-academia-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`FilesBucketName`].OutputValue' \
  --output text)

LAMBDA_ARN=$(aws lambda get-function \
  --function-name sentinel-file-processor-dev \
  --query 'Configuration.FunctionArn' --output text)

aws s3api put-bucket-notification-configuration \
  --bucket "$BUCKET" \
  --notification-configuration "{
    \"LambdaFunctionConfigurations\": [{
      \"Id\": \"FileProcessorTrigger\",
      \"LambdaFunctionArn\": \"$LAMBDA_ARN\",
      \"Events\": [\"s3:ObjectCreated:*\"],
      \"Filter\": {
        \"Key\": {
          \"FilterRules\": [{\"Name\": \"prefix\", \"Value\": \"tenants/\"}]
        }
      }
    }]
  }"
```

### 5. Build y deploy del frontend

```bash
cd web

# .env.production
cat > .env.production << EOF
VITE_API_URL=https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev
VITE_TENANT_ID=demo-utpl
EOF

# Build
npx vite build

# Crear bucket S3
BUCKET="sentinel-frontend-dev-$(aws sts get-caller-identity --query Account --output text)"
aws s3 mb "s3://$BUCKET" --region us-east-1

# Static website + public access
aws s3 website "s3://$BUCKET/" --index-document index.html --error-document index.html
aws s3api delete-public-access-block --bucket "$BUCKET"

# Bucket policy
cat > /tmp/policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::$BUCKET/*"
  }]
}
EOF
aws s3api put-bucket-policy --bucket "$BUCKET" --policy file:///tmp/policy.json

# Upload
aws s3 sync dist/ "s3://$BUCKET/" --delete
```

Tu frontend estar&aacute; en `http://$BUCKET.s3-website-us-east-1.amazonaws.com/`

---

## Configuraci&oacute;n de OCI

### 1. Crear Object Storage bucket

```python
import oci
from oci.config import from_file

config = from_file("~/.oci/config", "DEFAULT")
object_storage = oci.object_storage.ObjectStorageClient(config)

# Get namespace (no es el OCID!)
namespace = "ax59x2so1pxw"  # <-- importante
compartment_id = config["compartment-id"]

object_storage.create_bucket(
    namespace,
    "sentinel-knowledge",
    oci.object_storage.models.CreateBucketDetails(
        name="sentinel-knowledge",
        compartment_id=compartment_id,
        public_access_type="NoPublicAccess",
        storage_tier="Standard",
    ),
)
```

### 2. Subir el reglamento

```bash
# Subir knowledge/reglamento.txt al bucket
oci os object put \
  --bucket-name sentinel-knowledge \
  --name reglamento.txt \
  --file knowledge/reglamento.txt
```

### 3. (Opcional) Crear OCI Generative AI Agent para RAG production

Esto es para producci&oacute;n. El demo usa `MockLLMClient` (rule-based).

1. Ir a la Consola de OCI
2. Analytics & AI → Generative AI Agents
3. Create Agent
4. Data source: Object Storage bucket `sentinel-knowledge`
5. Model: Cohere Command R
6. Enable citations
7. Wait for indexing (5-10 min)
8. Get the Agent Endpoint OCID

---

## Endpoints de la API

| M&eacute;todo | Path | Descripci&oacute;n | Auth |
|---|---|---|---|
| GET | `/health` | Health check | No |
| POST | `/api/quejas` | Crear queja (async 202) | S&iacute; (tenant) |
| GET | `/api/quejas` | Listar quejas del tenant | S&iacute; (tenant) |
| GET | `/api/quejas/{id}` | Obtener queja con analysis | S&iacute; (tenant) |
| POST | `/api/quejas/{id}/upload-url` | Pedir presigned URL para upload | S&iacute; (tenant) |
| POST | `/api/chat` | Hacer pregunta al RAG | S&iacute; (tenant) |

Todos los endpoints requieren `X-Tenant-ID: <tenant>` excepto `/health`.

### Ejemplo: crear queja

```bash
curl -X POST https://YOUR-API.execute-api.us-east-1.amazonaws.com/dev/api/quejas \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo-utpl" \
  -H "X-Correlation-ID: my-test-001" \
  -d '{
    "titulo": "Problema con el aula",
    "descripcion": "El aula 205 tiene el techo con filtraciones",
    "categoriaDeclarada": "INFRAESTRUCTURA",
    "anonima": false
  }'
```

**Response 202**:
```json
{
  "quejaId": "uuid-here",
  "status": "PENDIENTE",
  "correlationId": "my-test-001",
  "createdAt": "2026-06-20T...",
  "estimatedAnalysisTime": 30
}
```

### Ejemplo: hacer chat (RAG)

```bash
curl -X POST https://YOUR-API.execute-api.us-east-1.amazonaws.com/dev/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo-utpl" \
  -d '{
    "question": "Cuales son las categorias de quejas?"
  }'
```

**Response 200**:
```json
{
  "answer": "Basado en el reglamento, las categorias son...",
  "sources": [
    {
      "id": "reglamento-cap1",
      "title": "Capitulo 1: Disposiciones generales",
      "content": "Articulo 1. ...",
      "score": 0.5
    }
  ],
  "modeloUsado": "cohere.command-latest",
  "tokensUsados": 146
}
```

---

## Tests

### Correr todos los tests

```bash
cd /home/lFunknown/sentinel-academia
export PYTHONPATH=src:$PYTHONPATH
python3 -m pytest src/tests/ -v
```

### Resultado esperado

```
src/tests/unit/test_shared.py ..................     [ 36%]
src/tests/unit/test_dynamo_client.py .........     [ 54%]
src/tests/unit/test_knowledge_service.py ...... [ 74%]
src/tests/integration/test_handlers.py ........... [100%]
============================== 50 passed in 2.09s ==============================
```

### Con coverage

```bash
python3 -m pytest src/tests/ --cov=src --cov-report=term-missing
```

### Tests espec&iacute;ficos

```bash
# Solo unit tests
python3 -m pytest src/tests/unit/

# Solo integration tests
python3 -m pytest src/tests/integration/

# Un test en particular
python3 -m pytest src/tests/integration/test_handlers.py::TestChat
```

---

## Troubleshooting

### Error: "NoCredentialsError"

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
aws sts get-caller-identity  # verificar
```

### Error: "Runtime.ImportModuleError: No module named 'src'"

Los imports deben ser `from handlers._shared` (sin `src.`).

### Error: "Float types are not supported. Use Decimal types instead."

Usar el helper `_to_dynamo()` que convierte floats a Decimal.

### Error: "LabRole not authorized to create IAM roles"

AWS Academy no permite `iam:CreateRole`. Usar `LabRole` pre-existente:
```yaml
Properties:
  Role: arn:aws:iam::ACCOUNT:role/LabRole
```

### Error: "Circular dependency between resources"

Quitar el S3 event del template y configurar la notificaci&oacute;n manual post-deploy.

### Error: "KeyError: 'filename' in LogRecord"

`filename` es palabra reservada de stdlib logging. Usar `file_name`.

---

## Stack final desplegado

| Recurso | ARN/ID |
|---|---|
| API Gateway | `om3eiczjr9` |
| Lambda `sentinel-health-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-health-dev` |
| Lambda `sentinel-create-queja-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-create-queja-dev` |
| Lambda `sentinel-get-queja-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-get-queja-dev` |
| Lambda `sentinel-list-quejas-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-list-quejas-dev` |
| Lambda `sentinel-analyze-queja-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-analyze-queja-dev` |
| Lambda `sentinel-upload-url-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-upload-url-dev` |
| Lambda `sentinel-file-processor-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-file-processor-dev` |
| Lambda `sentinel-chat-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-chat-dev` |
| Lambda `sentinel-dashboard-dev` | `arn:aws:lambda:us-east-1:ACCT:function:sentinel-dashboard-dev` |
| Lambda `sentinel-notify-email-dev` | SNS consumer para emails |
| DynamoDB `sentinel-quejas-dev` | Tabla single-table multi-tenant |
| SQS `sentinel-analysis-dev` | Cola principal con DLQ |
| SQS `sentinel-analysis-dlq-dev` | Dead Letter Queue (14 d&iacute;as) |
| SNS `sentinel-alertas-dev` | Topic para alertas cr&iacute;ticas |
| S3 `sentinel-files-dev-227165337884` | Bucket para evidencia + tenant configs |
| S3 `sentinel-frontend-dev-227165337884` | Frontend Vue 3 |
| OCI `sentinel-knowledge` | Knowledge base del RAG |

---

## Flujo de notificaciones (event-driven)

```
[POST /api/quejas] → SQS → [analyze_queja Lambda]
                              ↓ Mock LLM (prioridad 1-10)
                              ↓
                          prioridad >= tenant.threshold (default 6)?
                              ↓ S&Iacute;
                          [SNS Topic: sentinel-alertas]
                              ↓
                          [notifyByEmail Lambda]
                              ↓ Lee tenant config de S3
                              ↓
                          [Email a bienestar@utec.edu.ec, etc.]
```

### Tenant configs (per-tenant routing)

Subir configs como JSON a `s3://sentinel-files-dev/tenants/{tenantId}/config.json`:

```json
{
  "name": "Universidad T&eacute;cnica Estatal de Cuenca",
  "emails": {
    "BIENESTAR": "bienestar@utec.edu.ec",
    "DIRECCION": "direccion@utec.edu.ec",
    "SEGURIDAD": "seguridad@utec.edu.ec",
    "DEFAULT": "sentinel@utec.edu.ec"
  },
  "threshold": 6
}
```

**Routing por categor&iacute;a** (en `tenant_config_service.py:get_recipients`):
- `ACOSO`, `SALUD` &rarr; BIENESTAR + SEGURIDAD + DEFAULT
- `INFRAESTRUCTURA`, `ADMINISTRATIVA` &rarr; DIRECCION + DEFAULT
- Otras &rarr; DEFAULT

Para activar env&iacute;o real con SES, descomentar la secci&oacute;n marcada en `notify_by_email.py` y verificar dominio/emails en SES.

---

## Licencia

MIT — ver [LICENSE](LICENSE)

---

## Cr&eacute;ditos

- **AWS Academy** — por las credenciales y el sandbox
- **Oracle Cloud** — por el servicio de Generative AI
- **Cohere** — por el modelo de LLM
- **Vue.js / Pinia** — por el framework
- **pytest / moto** — por las herramientas de testing

---

## Tutorials paso a paso

Cada fase tiene un tutorial LaTeX + PDF detallado:

| Fase | Contenido | PDF |
|---|---|---|
| 0 | OCI setup (Cohere v1) | `docs/00-tutorial-llm/` |
| 1 | Backend Core (Lambda + DynamoDB) | `docs/01-tutorial-fase1/` |
| 2 | LLM integration (SQS + mock) | `docs/02-tutorial-fase2/` |
| 3 | Frontend deploy (S3 + Vite) | `docs/03-tutorial-fase3/` |
| 4 | File uploads (presigned URLs) | `docs/04-tutorial-fase4/` |
| 5 | RAG con OCI (Object Storage) | `docs/05-tutorial-fase5/` |
| 6 | Testing (pytest + moto) | `docs/06-tutorial-fase6/` |
| 7 | Deploy final (este README) | `docs/07-tutorial-fase7/` |

Para compilar cualquiera:
```bash
cd docs/0X-tutorial-faseX/
tectonic tutorial-faseX.tex
```

---

&Uacute;ltima actualizaci&oacute;n: junio 2026
