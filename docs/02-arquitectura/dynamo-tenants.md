# Diseno de DynamoDB: Multi-Tenant + Single-Table

> Guia completa del modelo de datos de Sentinel AcademIA.
> Como la IA debe entenderlo para implementar el backend correctamente.

---

## Indice
1. [Por que multi-tenant desde el inicio](#1-por-que-multi-tenant-desde-el-inicio)
2. [Principios del diseno](#2-principios-del-diseno)
3. [Estructura de la tabla unica](#3-estructura-de-la-tabla-unica)
4. [Entidades y sus keys](#4-entidades-y-sus-keys)
5. [Access patterns](#5-access-patterns)
6. [Global Secondary Indexes (GSIs)](#6-global-secondary-indexes-gsis)
7. [Flujo end-to-end de una queja](#7-flujo-end-to-end-de-una-queja)
8. [Single-tenant vs Multi-tenant en codigo](#8-single-tenant-vs-multi-tenant-en-codigo)
9. [JSON Fixtures para tests](#9-json-fixtures-para-tests)
10. [Migracion futura](#10-migracion-futura)

---

## 1. Por que multi-tenant desde el inicio

Aunque la hackaton es para **UNA universidad**, el diseno multi-tenant es importante por:

1. **Costo cero adicional**: solo agregar `tenantId` a las keys
2. **Migracion futura trivial**: pasar a SaaS multi-universidad
3. **Aislamiento de tests**: tenants `test`, `dev`, `prod` separados
4. **Mejor practica de la industria**: SaaS multi-tenant es el estandar
5. **Demuestra competencia tecnica**: "disenamos pensando en escala"

### Que es un tenant

- **Tenant** = una institucion (universidad, colegio, empresa)
- En Sentinel AcademIA: cada universidad es un tenant
- Por ahora: 1 tenant activo (`universidad-ejemplo`)
- En el futuro: podrian ser 10, 100, 1000 universidades

### Que se comparte entre tenants

- Misma tabla DynamoDB
- Mismo bucket S3
- Mismo API Gateway
- Mismas Lambdas

### Que se aisla por tenant

- Data en DynamoDB (via `tenantId` en las keys)
- Archivos en S3 (prefijo del path: `tenants/{tenantId}/...`)
- Configuracion (tema, emails, branding)
- Reportes y dashboards

---

## 2. Principios del diseno

### Single-Table Design

- **Una sola tabla** DynamoDB para todo el dominio
- Cada item puede ser de **distinto tipo** (QUEJA, ANALYSIS, ATTACHMENT, etc.)
- Se diferencian por la **combinacion de partition key + sort key**
- **Reduce costos**: 1 tabla es mas barato que N tablas
- **Permite transacciones atomicas** entre entidades relacionadas

### Multi-tenant via Key Prefix

- TODA partition key comienza con `TENANT#{tenantId}#`
- Esto **aisla naturalmente** la data entre tenants
- Permite queries eficientes por tenant
- **NO requiere** policies de IAM complejas (todo esta en una tabla)

### Access Patterns First

Antes de disenar la tabla, definimos las queries que necesitamos:

1. "Obtener queja por ID" -> GSI por `quejaId`
2. "Listar quejas del tenant" -> GSI por `tenantId + createdAt`
3. "Buscar quejas criticas" -> GSI por `tenantId + criticidad`
4. "Verificar idempotencia" -> Key directa `IDEMPOTENCY#{hash}`
5. "Obtener config del tenant" -> Key directa `TENANT#{tenantId}`

### JSON Fixtures

Para cada entidad, tenemos fixtures JSON en `tests/fixtures/` que permiten tests realistas sin depender de la base real.

---

## 3. Estructura de la tabla unica

### CloudFormation / SAM

```yaml
QuejasTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: quejas
    BillingMode: PAY_PER_REQUEST  # Sin provisioned, ideal para cargas variables
    AttributeDefinitions:
      - { AttributeName: pk, AttributeType: S }
      - { AttributeName: sk, AttributeType: S }
      - { AttributeName: quejaId, AttributeType: S }
      - { AttributeName: tenantId, AttributeType: S }
      - { AttributeName: createdAt, AttributeType: S }
      - { AttributeName: criticidad, AttributeType: S }
    KeySchema:
      - { AttributeName: pk, KeyType: HASH }
      - { AttributeName: sk, KeyType: RANGE }
    GlobalSecondaryIndexes:
      - IndexName: GSI_ById
        KeySchema: [{ AttributeName: quejaId, KeyType: HASH }]
        Projection: { ProjectionType: ALL }
      - IndexName: GSI_ByTenant
        KeySchema:
          - { AttributeName: tenantId, KeyType: HASH }
          - { AttributeName: createdAt, KeyType: RANGE }
        Projection: { ProjectionType: ALL }
      - IndexName: GSI_ByTenantCriticidad
        KeySchema:
          - { AttributeName: tenantId, KeyType: HASH }
          - { AttributeName: criticidad, KeyType: RANGE }
        Projection: { ProjectionType: ALL }
    TimeToLiveSpecification:
      AttributeName: ttl
      Enabled: true
```

### Atributos

| Atributo | Tipo | Descripcion |
|---|---|---|
| `pk` | S | Partition Key: `TENANT#{tenantId}#QUEJA#{quejaId}` o `IDEMPOTENCY#{hash}` |
| `sk` | S | Sort Key: `META` o `ANALYSIS#{ts}` o `ATTACHMENT#{key}` |
| `tenantId` | S | Para GSI_ByTenant y GSI_ByTenantCriticidad |
| `quejaId` | S | Para GSI_ById |
| `createdAt` | S | ISO 8601, para ordenamiento |
| `criticidad` | S | Para filtrar por criticidad |
| `ttl` | N | UNIX timestamp para auto-expiracion |

---

## 4. Entidades y sus keys

### 4.1 QUEJA (item principal)

**Keys**:
- `pk`: `TENANT#{tenantId}#QUEJA#{quejaId}`
- `sk`: `META`

**Atributos**:
```json
{
  "pk": "TENANT#universidad-ejemplo#QUEJA#q-abc-123",
  "sk": "META",
  "tenantId": "universidad-ejemplo",
  "quejaId": "q-abc-123",
  "titulo": "Problema con profesor de calculo",
  "descripcion": "El profesor no asistio a clases en 2 semanas...",
  "categoriaDeclarada": "ACADEMICA",
  "status": "ANALIZADA",
  "userId": "u-user-123",
  "sede": "Sede Norte",
  "facultad": "Ingenieria",
  "anonima": false,
  "createdAt": "2025-01-15T10:30:00.000Z",
  "updatedAt": "2025-01-15T10:30:05.123Z",
  "ttl": 1736898600
}
```

**Como se crea**: en `createQueja` Lambda

### 4.2 ANALYSIS (hijo de QUEJA)

**Keys**:
- `pk`: `TENANT#{tenantId}#QUEJA#{quejaId}` (mismo que la queja)
- `sk`: `ANALYSIS#{timestamp}` (permite multiples analisis si se re-procesa)

**Atributos**:
```json
{
  "pk": "TENANT#universidad-ejemplo#QUEJA#q-abc-123",
  "sk": "ANALYSIS#2025-01-15T10:30:05.123Z",
  "tenantId": "universidad-ejemplo",
  "quejaId": "q-abc-123",
  "categoria": "ACADEMICA",
  "subcategoria": "INASISTENCIA_DOCENTE",
  "criticidad": "MEDIA",
  "criticidadJustificacion": "Problema recurrente que afecta a multiples estudiantes",
  "sentimiento": "NEGATIVO",
  "entidades": [
    {"tipo": "PERSONA", "texto": "profesor de calculo", "anonimizado": true}
  ],
  "temasClave": ["inasistencia", "calculo"],
  "accionSugerida": "Contactar direccion academica",
  "prioridad": 6,
  "requiereNotificacionInmediata": false,
  "modeloUsado": "cohere.command-r",
  "tokensConsumidos": 850,
  "latenciaMs": 2300
}
```

**Como se crea**: en `processQueja` Lambda (consumer SQS)

### 4.3 ATTACHMENT (hijo de QUEJA)

**Keys**:
- `pk`: `TENANT#{tenantId}#QUEJA#{quejaId}` (mismo que la queja)
- `sk`: `ATTACHMENT#{s3Key}` (permite multiples adjuntos)

**Atributos**:
```json
{
  "pk": "TENANT#universidad-ejemplo#QUEJA#q-abc-123",
  "sk": "ATTACHMENT#quejas/q-abc-123/abc-evidencia.pdf",
  "tenantId": "universidad-ejemplo",
  "quejaId": "q-abc-123",
  "s3Key": "tenants/universidad-ejemplo/quejas/q-abc-123/abc-evidencia.pdf",
  "filename": "evidencia.pdf",
  "contentType": "application/pdf",
  "size": 245678,
  "textoExtraido": "Contenido extraido por OCI Document AI...",
  "status": "TEXTO_EXTRAIDO",
  "createdAt": "2025-01-15T10:30:00.000Z"
}
```

**Como se crea**: en `fileProcessor` Lambda (consumer SQS de S3 events)

### 4.4 IDEMPOTENCY (separado, no bajo tenant)

**Keys**:
- `pk`: `IDEMPOTENCY#{hash}` (sin tenant prefix, es global)
- `sk`: `PROCESSED`

**Atributos**:
```json
{
  "pk": "IDEMPOTENCY#abc123def456",
  "sk": "PROCESSED",
  "quejaId": "q-abc-123",
  "tenantId": "universidad-ejemplo",
  "processedAt": "2025-01-15T10:30:05.000Z",
  "ttl": 1737071400
}
```

**Por que sin tenant**: el hash de idempotencia es globalmente unico (SHA-256 del input).

### 4.5 METRIC (agregacion por dia)

**Keys**:
- `pk`: `TENANT#{tenantId}#METRIC`
- `sk`: `DAILY#{date}#COUNT#{category}`

**Atributos**:
```json
{
  "pk": "TENANT#universidad-ejemplo#METRIC",
  "sk": "DAILY#2025-01-15#COUNT#ACADEMICA",
  "tenantId": "universidad-ejemplo",
  "date": "2025-01-15",
  "category": "ACADEMICA",
  "count": 15,
  "updatedAt": "2025-01-15T23:59:00.000Z"
}
```

**Como se actualiza**: en `updateDashboard` Lambda (consumer EventBridge)

### 4.6 TENANT CONFIG

**Keys**:
- `pk`: `TENANT#{tenantId}`
- `sk`: `CONFIG`

**Atributos**:
```json
{
  "pk": "TENANT#universidad-ejemplo",
  "sk": "CONFIG",
  "tenantId": "universidad-ejemplo",
  "name": "Universidad Ejemplo",
  "branding": {
    "primaryColor": "#2563eb",
    "logoUrl": "https://..."
  },
  "settings": {
    "bienestarEmail": "bienestar@universidad-ejemplo.edu",
    "directorEmail": "director@universidad-ejemplo.edu",
    "categoriasHabilitadas": ["ACADEMICA", "INFRAESTRUCTURA", "ACOSO"],
    "notificarSMS": true
  },
  "createdAt": "2025-01-01T00:00:00.000Z"
}
```

**Como se obtiene**: en cada Lambda que necesita config del tenant

---

## 5. Access patterns

| # | Access Pattern | Operacion | Keys/Index usadas |
|---|---|---|---|
| 1 | Crear queja | `PutItem` | pk=`TENANT#xxx#QUEJA#xxx`, sk=`META` |
| 2 | Obtener queja por ID | `Query` GSI_ById | Filter: tenantId=xxx |
| 3 | Listar quejas del tenant (recientes) | `Query` GSI_ByTenant | ScanIndexForward: false, Limit: 20 |
| 4 | Listar quejas por criticidad | `Query` GSI_ByTenantCriticidad | Key: tenantId+criticidad |
| 5 | Obtener queja + analisis + adjuntos | `Query` (mismo pk) | sk between META and ZZZ |
| 6 | Obtener solo META de queja | `GetItem` | pk + sk=META |
| 7 | Obtener solo ANALYSIS | `Query` (mismo pk) | sk begins_with ANALYSIS# |
| 8 | Obtener solo ATTACHMENTs | `Query` (mismo pk) | sk begins_with ATTACHMENT# |
| 9 | Verificar idempotencia | `GetItem` | pk=`IDEMPOTENCY#xxx`, sk=`PROCESSED` |
| 10 | Marcar idempotencia | `PutItem` con ConditionExpression | attribute_not_exists(pk) |
| 11 | Obtener config del tenant | `GetItem` | pk=`TENANT#xxx`, sk=`CONFIG` |
| 12 | Listar metricas del tenant | `Query` | pk=`TENANT#xxx#METRIC` |
| 13 | Incrementar metrica | `UpdateItem` ADD | atomic counter |

---

## 6. Global Secondary Indexes (GSIs)

### GSI_ById

- **Proposito**: Buscar queja por `quejaId` (sin saber el tenant)
- **Partition**: `quejaId`
- **Sort**: ninguno
- **Filter en codigo**: agregar `FilterExpression: tenantId = :tid` para aislar por tenant
- **Costo**: pagamos por cada read aunque no encontremos el item

### GSI_ByTenant

- **Proposito**: Listar quejas de un tenant ordenadas por fecha
- **Partition**: `tenantId`
- **Sort**: `createdAt`
- **Ventaja**: query eficiente por tenant + rango temporal
- **Uso**: `list_by_tenant()`, dashboard, paginacion

### GSI_ByTenantCriticidad

- **Proposito**: Listar quejas de un tenant por criticidad
- **Partition**: `tenantId`
- **Sort**: `criticidad`
- **Uso**: dashboard de autoridades, "mostrar todas las criticas"

---

## 7. Flujo end-to-end de una queja

```
[1] Usuario envia queja
    Frontend: POST /api/quejas
        |
        v
    Lambda: createQueja
        |
        +-- Validar input con Pydantic
        +-- Generar quejaId (uuid v4)
        +-- Determinar tenant_id (de JWT o settings)
        |
        +-- PutItem en DynamoDB
        |   pk = TENANT#universidad-ejemplo#QUEJA#q-123
        |   sk = META
        |   status = EN_COLA
        |
        +-- SendMessage a SQS
        |   MessageBody: { eventType: "queja.creada", payload: {...} }
        |
        +-- Return 202 Accepted { quejaId, status: "EN_COLA" }

[2] Consumer procesa la queja (async)
    SQS -> Lambda: processQueja
        |
        +-- Check idempotency (GetItem en IDEMPOTENCY#xxx)
        |   Si ya procesado: skip
        |
        +-- GetItem en DynamoDB (pk + sk=META)
        |
        +-- Si hay adjuntos:
        |   GetObject de S3 + OCI Document AI
        |   PutItem en ATTACHMENT#...
        |
        +-- Llamar OCI Generative AI
        |   Prompt: system + texto completo
        |   Validar output con Pydantic (AnalisisItem)
        |
        +-- PutItem en DynamoDB
        |   pk = TENANT#xxx#QUEJA#q-123 (mismo que la queja)
        |   sk = ANALYSIS#2025-01-15T10:30:05.123Z
        |
        +-- UpdateItem en DynamoDB
        |   pk + sk=META
        |   SET status = "ANALIZADA"
        |
        +-- TransactWrite: marcar idempotency
        |   PutItem: IDEMPOTENCY#xxx, sk=PROCESSED
        |
        +-- PutEvents a EventBridge
        |   source: "com.sentinel.queja"
        |   detail-type: "queja.analizada"
        |   detail: { quejaId, analysis }
        |
        +-- Return batchItemFailures: [] (todo OK)

[3] EventBridge enruta segun criticidad
    EventBridge -> 2 reglas:
        |
        +-- Si criticidad=CRITICA: SNS topic
        |   SNS -> Lambda: notifyByEmail
        |       |
        |       +-- SES.send_email a bienestar + director
        |
        +-- Siempre: SNS topic
            SNS -> Lambda: updateDashboard
                |
                +-- UpdateItem METRIC (atomic counter)

[4] Si el usuario consulta su queja
    Frontend: GET /api/quejas/q-123
        |
        v
    Lambda: getQueja
        |
        +-- Query GSI_ById (quejaId=q-123)
        |   Filter: tenantId=xxx
        |
        +-- Query mismo pk, sk begins_with ANALYSIS#
        |   (para incluir el ultimo analisis)
        |
        +-- Return queja + analisis
```

---

## 8. Single-tenant vs Multi-tenant en codigo

### Por ahora (hackaton): single-tenant

```python
# settings.py
class Settings(BaseSettings):
    default_tenant_id: str = "universidad-ejemplo"
    # ... otros

# Lambda
@logger.inject_lambda_context
def handler(event, context):
    tenant_id = settings.default_tenant_id  # Siempre el mismo
    # ... usar tenant_id
```

### En el futuro: multi-tenant real

```python
# auth.py
def extract_tenant_from_jwt(event: dict) -> str:
    """Extrae tenant_id del JWT del usuario."""
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    return claims["custom:tenant_id"]

# Lambda
@logger.inject_lambda_context
def handler(event, context):
    tenant_id = extract_tenant_from_jwt(event)  # Del usuario autenticado
    # ... usar tenant_id
```

**Lo importante**: el codigo de las Lambdas NO cambia entre single-tenant y multi-tenant real. Solo cambia como se obtiene el `tenant_id`.

---

## 9. JSON Fixtures para tests

Ver `tests/fixtures/` en la estructura del proyecto. Cada entidad tiene su fixture:

- `queja_valida.json` - Una queja completa
- `analysis_valido.json` - Output del LLM esperado
- `attachment_valido.json` - Archivo adjunto
- `tenant_config.json` - Config del tenant
- `sqs_message.json` - Mensaje de SQS de ejemplo
- `s3_event.json` - Evento de S3 de ejemplo
- `multiple_quejas.json` - Lista de quejas para tests de listado

### Como se cargan

```python
# tests/conftest.py
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / f"{name}.json") as f:
        return json.load(f)

@pytest.fixture
def queja_valida() -> dict:
    return load_fixture("queja_valida")
```

### Como se usan en tests

```python
def test_queja_creation(dynamodb_table, queja_valida):
    # Cargar la queja desde el fixture
    body = CreateQuejaInput(
        titulo=queja_valida["titulo"],
        descripcion=queja_valida["descripcion"],
        categoria_declarada=CategoriaEnum(queja_valida["categoriaDeclarada"]),
    )
    # ... test code
```

---

## 10. Migracion futura

### Cuando se quiera pasar a multi-universidad

**Paso 1**: Agregar autenticacion con JWT
- Implementar `extract_tenant_from_jwt()` en `_shared/auth.py`
- Configurar API Gateway con Cognito User Pool o similar

**Paso 2**: Cambiar `settings.default_tenant_id` por lookup
```python
# Antes
tenant_id = settings.default_tenant_id

# Despues
tenant_id = extract_tenant_from_jwt(event)
```

**Paso 3**: Validar que el tenant existe y esta activo
```python
tenant = get_tenant_config(tenant_id)
if not tenant or not tenant.is_active:
    return forbidden("Tenant inactivo", correlation_id)
```

**Paso 4**: Implementar self-service de onboarding
- Endpoint POST /api/tenants (solo para admins)
- Provisiona el tenant en DynamoDB, S3, etc.
- Crea la primera queja y usuario admin

**NO se requiere migracion de datos** porque desde el inicio usamos `tenantId` en las keys.

---

## Resumen

- **1 tabla** DynamoDB con `pk` y `sk`
- **Multi-tenant** via `TENANT#{tenantId}#` prefix en partition keys
- **3 GSIs**: por `quejaId`, por `tenantId+createdAt`, por `tenantId+criticidad`
- **6 tipos de items**: QUEJA, ANALYSIS, ATTACHMENT, IDEMPOTENCY, METRIC, TENANT
- **Pydantic** para validar TODO item antes de usar
- **JSON fixtures** para tests realistas
- **Migracion a multi-tenant real** = solo cambiar como se obtiene el tenant_id
