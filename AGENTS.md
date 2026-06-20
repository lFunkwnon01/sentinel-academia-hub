# AGENTS.md

> Archivo de contexto para herramientas de AI (Cursor, Aider, opencode, etc.).
> opencode usa `opencode.json` como config principal; este archivo es para otras tools.

## Proyecto
**Sentinel AcademIA** - Plataforma de quejas universitarias con IA.
Hackaton: "Arquitectura basada en eventos e integracion con LLMs".

## Stack

### Backend (Python)
- **Lenguaje**: Python 3.12 (no TypeScript/Node.js)
- **Compute**: AWS Lambda (1 funcion = 1 endpoint)
- **Librerias**: aws-lambda-powertools, Pydantic v2, boto3, opossum
- **Storage**: DynamoDB (single-table, multi-tenant)
- **Colas**: SQS + SNS + EventBridge
- **Secrets**: Secrets Manager
- **IaC**: AWS SAM (template.yaml)
- **Multi-tenant**: tenantId en TODAS las partition keys

### Frontend (TypeScript)
- **Framework**: Vue 3 con Composition API
- **Lenguaje**: TypeScript estricto
- **Build**: Vite + Pinia + Vue Router 4
- **Estilos**: CSS nativo con custom properties (NO Tailwind)
- **Despliegue**: Vercel

### LLM
- **Proveedor**: Oracle OCI Generative AI
- **Primary**: Cohere Command R
- **Fallback 1**: Meta Llama 3.1 70B
- **Fallback 2**: Cohere Command R+
- **Embeddings**: Cohere embed-multilingual-v3.0

## Documentacion
- `docs/01-contexto/` - Criterio 1 (LaTeX → PDF)
- `docs/02-arquitectura/` - Criterio 2 (Mermaid + PNG + patrones)
  - `dynamo-tenants.md` - Diseno DB multi-tenant
  - `patron-s3-lambda.md` - Patron upload de archivos
- `docs/03-resiliencia-llm/` - Criterio 3 (LaTeX + checklist)
- `docs/04-frontend/` - Criterio 4 (Vue + Swagger mock)
- `docs/05-repo-deploy/` - Criterio 5 (checklist + manual + prompt Lucidchart)

## Reglas principales

### Backend (Python)
1. **Python 3.12 estricto** con type hints en TODO.
2. **Pydantic v2** para validacion runtime.
3. **aws-lambda-powertools** para logger, tracer, metrics.
4. **1 Lambda = 1 endpoint o 1 consumer**.
5. **Correlation ID** obligatorio en headers y logs.
6. **multi-tenant**: `tenantId` en TODA partition key de DynamoDB.
7. **NUNCA print()** - usar `logger`.
8. **Validar input SIEMPRE con Pydantic** antes de logica.
9. **Boto3 + boto3-stubs** para type hints.

### General
10. **Idioma**: Responder en espanol, codigo y configs en ingles.
11. **LLM con circuit breaker + fallback** (Cohere R -> Llama 3.1 -> Command R+).
12. **CSS nativo** con custom properties (NO Tailwind en frontend).
13. **Composition API** siempre (NO Options API).
14. **Pinia** solo para estado global.
15. **Documentar al momento**, no al final.
16. **Documentacion es contrato vivo**: leer docs antes de codear, actualizar despues.
17. **Trazabilidad total**: cada elemento en la doc tiene su contraparte en codigo.

## Estructura clave

```
src/
├── handlers/         # Backend: 1 Lambda por archivo (Python)
│   ├── _shared/      # Modulos compartidos
│   └── *.py          # 1 archivo = 1 handler
├── services/         # Logica de negocio
├── infra/            # template.yaml (SAM)
└── tests/            # pytest + moto + fixtures JSON

web/src/              # Frontend Vue 3
docs/                 # Documentacion por criterio
.opencode/            # Config de opencode (agents, skills, rules)
api-mock/             # OpenAPI spec
```

## Comandos frecuentes

```bash
# Backend (Python)
cd src
python -m pytest                    # Tests
python -m pytest --cov=src          # Con coverage
mypy src/                           # Type check
ruff check src/                     # Lint
ruff format src/                    # Format
sam build
sam deploy --guided

# Frontend
cd web && npm run dev
cd web && npm run build
cd web && npm run typecheck
cd web && npm run lint

# Documentacion
tectonic docs/01-contexto/contexto.tex
tectonic docs/03-resiliencia-llm/resiliencia.tex
bash scripts/regenerate-diagrams.sh

# Mock API
npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010

# Dev: mock + frontend en paralelo
npm run dev:all
```

## Prohibido
- **TypeScript/Node.js en backend** (usamos Python 3.12)
- **print()** en backend (usar `logger`)
- Type hints faltantes en Python
- Tailwind, Bootstrap, Material UI en frontend
- Bases de datos relacionales
- Cloudflare (no tenemos tarjeta configurada)
- Modelos LLM caros en el proyecto desplegado (Claude Opus, GPT-4, Gemini Pro)
- Multi-nube "fake"
- Commitear secrets o .env
- Tenant ID hardcodeado (debe venir de JWT o settings)
- Sin `tenantId` en las partition keys de DynamoDB

## Skills disponibles (16)

### Backend / Data
- `swagger-first` - API-first con OpenAPI
- `aws-lambda-pattern` - Plantillas Lambda Python
- `event-driven-pattern` - SQS, EventBridge, SNS (Python)
- `dynamodb-patterns` - Single-table, multi-tenant, JSON fixtures

### LLM / IA
- `oci-generative-ai` - OCI GenAI + fallback
- `rag-implementation` - RAG, embeddings, vector search

### Frontend
- `vue3-architecture` - Estructura Vue 3
- `frontend-streaming` - SSE, WebSocket
- `vercel-deploy` - Deploy a Vercel

### Calidad / DevOps
- `unit-testing-patterns` - pytest + moto + fixtures
- `github-actions` - CI/CD workflows
- `observability-stack` - CloudWatch, X-Ray, Langfuse
- `deploy-checklist` - Pre/post deploy

### Documentacion
- `mermaid-diagrams` - Diagramas C4
- `latex-document` - LaTeX → PDF
- `hackathon-deliverables` - Checklist rubrica

Para reglas detalladas, ver `.opencode/rules/*.md`.
Para skills, ver `.opencode/skills/*/SKILL.md`.
Para agents, ver `.opencode/agents/*.md`.
