# Estimacion de Costos Detallada

> Costos reales del proyecto Sentinel AcademIA, desglosados por servicio y escenario.

---

## Resumen Ejecutivo

| Escenario | AWS | OCI | Vercel | **Total** |
|---|---|---|---|---|
| **Hackaton** (4 dias, 100-200 quejas) | < $0.50 | < $1.00 | $0.00 | **< $1.50** |
| **Piloto** (1 mes, 500 quejas) | ~$1.00 | ~$3.00 | $0.00 | **~$4.00** |
| **Produccion pequena** (mes, 5000 quejas) | ~$3.00 | ~$30.00 | $0.00 | **~$33.00** |
| **Produccion media** (mes, 50000 quejas) | ~$15.00 | ~$300.00 | $0.00 | **~$315.00** |

**vs. arquitectura equivalente con Claude Sonnet 4** (Bedrock):
- Produccion pequena: ~$330/mes (**10x m&aacute;s caro**)
- Produccion media: ~$3,300/mes

---

## Costos AWS (Region us-east-1)

### AWS Lambda

| Concepto | Free Tier | Costo unitario |
|---|---|---|
| Invocations | 1,000,000/mes | $0.20/1M |
| Compute (GB-second) | 400,000 GB-s/mes | $0.0000166667/GB-s |

**Calculo por escenario**:

| Escenario | Invocations | GB-s estimados | Costo |
|---|---|---|---|
| Hackaton | ~200 | ~20,000 | $0.00 |
| Piloto | ~3,000 | ~300,000 | $0.00 (free tier) |
| Produccion pequena | ~25,000 | ~2,500,000 | $0.005 + $0.04 = $0.045 |
| Produccion media | ~250,000 | ~25,000,000 | $0.05 + $0.42 = $0.47 |

### AWS API Gateway HTTP API

| Concepto | Free Tier | Costo unitario |
|---|---|---|
| Requests | 1,000,000/mes | $1.00/1M |

| Escenario | Requests | Costo |
|---|---|---|
| Hackaton | ~200 | $0.00 |
| Piloto | ~3,000 | $0.00 |
| Produccion pequena | ~25,000 | $0.025 |
| Produccion media | ~250,000 | $0.25 |

### AWS DynamoDB

PAY_PER_REQUEST:
| Concepto | Costo |
|---|---|
| Read request units | $0.25/million |
| Write request units | $1.25/million |
| Storage | $0.25/GB-mes |

| Escenario | Reads | Writes | Storage | Costo |
|---|---|---|---|---|
| Hackaton | ~10,000 | ~1,000 | 0.1 GB | $0.0025 + $0.00125 + $0.025 = $0.03 |
| Piloto | ~150,000 | ~15,000 | 0.5 GB | $0.04 + $0.02 + $0.125 = $0.18 |
| Produccion pequena | ~1.5M | ~150K | 2 GB | $0.375 + $0.19 + $0.50 = $1.06 |
| Produccion media | ~15M | ~1.5M | 20 GB | $3.75 + $1.88 + $5.00 = $10.63 |

### AWS SQS + SNS + EventBridge

| Servicio | Free Tier | Costo |
|---|---|---|
| SQS requests | 1,000,000/mes | $0.40/1M |
| SNS publishes | 1,000,000/mes | $0.50/1M |
| EventBridge events | - | $1.00/1M |

| Escenario | SQS | SNS | EventBridge | Costo |
|---|---|---|---|---|
| Hackaton | 100 | 5 | 50 | $0.00 |
| Piloto | 1,500 | 50 | 1,000 | $0.001 |
| Produccion pequena | 15,000 | 500 | 10,000 | $0.006 + $0.00025 + $0.01 = $0.02 |
| Produccion media | 150,000 | 5,000 | 100,000 | $0.06 + $0.0025 + $0.10 = $0.16 |

### AWS S3

| Concepto | Costo |
|---|---|
| Storage | $0.023/GB-mes (Standard) |
| GET requests | $0.0004/1K |
| PUT requests | $0.005/1K |

| Escenario | Storage | GET | PUT | Costo |
|---|---|---|---|---|
| Hackaton | 0.1 GB | 50 | 10 | $0.00 |
| Piloto | 1 GB | 500 | 100 | $0.023 + $0.0002 + $0.0005 = $0.024 |
| Produccion pequena | 5 GB | 5,000 | 1,000 | $0.115 + $0.002 + $0.005 = $0.12 |
| Produccion media | 50 GB | 50,000 | 10,000 | $1.15 + $0.02 + $0.05 = $1.22 |

### AWS CloudWatch + X-Ray

| Concepto | Costo |
|---|---|
| Logs ingestion | $0.50/GB |
| Logs storage | $0.03/GB-mes |
| X-Ray traces | $5.00/1M |
| Metrics custom | $0.30/metric-mes |

| Escenario | Logs | Traces | Metrics | Costo |
|---|---|---|---|---|
| Hackaton | 0.5 GB | 200 | 5 | $0.25 + $0.001 + $0.125 = $0.38 |
| Piloto | 2 GB | 3,000 | 10 | $1.00 + $0.015 + $0.25 = $1.27 |
| Produccion pequena | 10 GB | 25,000 | 15 | $5.00 + $0.125 + $0.375 = $5.50 |
| Produccion media | 100 GB | 250,000 | 20 | $50 + $1.25 + $0.50 = $51.75 |

### Resumen AWS

| Escenario | Total AWS |
|---|---|
| Hackaton | $0.41 |
| Piloto | $1.47 |
| Produccion pequena | $6.74 |
| Produccion media | $64.42 |

---

## Costos Oracle OCI (Generative AI)

### Modelos disponibles y precios

| Modelo | Input $/1M tokens | Output $/1M tokens | Caso de uso |
|---|---|---|---|
| **cohere.command-r** | $0.50 | $1.50 | **Primary** |
| cohere.command-r-plus | $3.00 | $15.00 | Fallback terciario (raro) |
| meta.llama-3.1-70b-instruct | $0.72 | $0.72 | **Fallback 1** |
| meta.llama-3.3-70b-instruct | $0.72 | $0.72 | Alternativa |
| meta.llama-3.2-90b-vision | $0.72 | $0.72 | Vision/PDFs |

### Distribucion esperada

Asumiendo que el **80% de las quejas** se procesan con `cohere.command-r` (primary), **15% con Llama 3.1** (fallback), **4% con Command R+** (raro), y **1% con respuesta controlada** (degradado):

**Promedio por queja** (input ~500 tokens, output ~300 tokens):

| Modelo | Distribucion | Costo input | Costo output | Costo total |
|---|---|---|---|---|
| cohere.command-r | 80% | 500/1M * $0.50 = $0.00025 | 300/1M * $1.50 = $0.00045 | $0.0007 |
| llama-3.1-70b | 15% | 500/1M * $0.72 = $0.00036 | 300/1M * $0.72 = $0.00022 | $0.00058 |
| command-r-plus | 4% | 500/1M * $3 = $0.0015 | 300/1M * $15 = $0.0045 | $0.006 |
| Controlado | 1% | $0 | $0 | $0 |

**Promedio ponderado**: $0.0007 * 0.8 + $0.00058 * 0.15 + $0.006 * 0.04 = $0.00085 por queja

### Por escenario

| Escenario | Quejas | Costo OCI (LLM) | Costo OCI Doc AI (si se usa) | Total OCI |
|---|---|---|---|---|
| Hackaton | 200 | $0.17 | $0.00 (no se usa) | $0.17 |
| Piloto | 500 | $0.43 | $0.50 (5 PDFs) | $0.93 |
| Produccion pequena | 5,000 | $4.25 | $5.00 (50 PDFs) | $9.25 |
| Produccion media | 50,000 | $42.50 | $50.00 (500 PDFs) | $92.50 |

### OCI Vault (opcional)

Vault y secretos son **gratis** (incluidos en Always Free tier).

### OCI Compute, Networking

No usamos (todo es serverless con AWS Lambda). **Costo: $0**.

### Resumen OCI

| Escenario | Total OCI |
|---|---|
| Hackaton | $0.17 |
| Piloto | $0.93 |
| Produccion pequena | $9.25 |
| Produccion media | $92.50 |

---

## Costos Vercel

| Plan | Costo | Limites |
|---|---|---|
| **Hobby (free)** | $0.00 | 100 GB bandwidth, builds ilimitados, 100 GB-Hrs serverless |
| Pro | $20/mes por usuario | Mas bandwidth, analytics, teams |

**Para la hackaton y produccion pequena**: **$0.00** con el plan Hobby.

---

## Costos de observabilidad adicionales

### Langfuse (cloud)

| Plan | Costo | Limites |
|---|---|---|
| **Hobby (free)** | $0.00 | 50K events/mes |
| Pro | $59/mes | 500K events/mes |

Para la hackaton, el plan **Hobby es suficiente**. Para produccion real, el plan Pro vale la inversion.

### Datadog / Better Stack / Sentry (opcional)

No incluidos en MVP. Si se agregan:
- Sentry: free tier (5K eventos/mes)
- Datadog: $15-30/mes
- Better Stack: $25/mes

---

## Comparacion con alternativas

### Nuestra implementacion (Cohere R + Llama)
- Produccion pequena: **~$35/mes**
- Produccion media: **~$315/mes**

### Alternativa 1: Claude Sonnet 4 (Bedrock)
- Claude Sonnet 4: $3 input / $15 output por 1M tokens
- 5000 quejas/mes, 800 tokens input + 300 output promedio:
  - 4M input + 1.5M output tokens
  - Costo: 4 * $3 + 1.5 * $15 = $12 + $22.5 = $34.5/mes solo de LLM
  - Total con AWS: ~$45-50/mes
- 50000 quejas/mes: ~$345-400/mes

### Alternativa 2: GPT-4o
- $2.50 input / $10 output por 1M tokens
- Similar a Claude
- Produccion pequena: ~$40/mes

### Alternativa 3: Gemini 1.5 Pro
- $1.25 input / $5 output por 1M tokens (hasta 128K context)
- Produccion pequena: ~$25/mes de LLM

**Conclusion**: nuestra eleccion de Cohere R es **5-10x mas barata** que las alternativas premium, con calidad suficiente para extraccion estructurada.

---

## Monitoreo de costos

### Configurar budget alert en AWS

```bash
# Crear budget con alerta al 80%
cat > budget.json << EOF
{
  "BudgetName": "SentinelAcademiaMonthly",
  "BudgetLimit": {
    "Amount": "10",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {
    "Service": [
      "Amazon API Gateway",
      "AWS Lambda",
      "Amazon DynamoDB",
      "Amazon Simple Queue Service",
      "Amazon Simple Storage Service",
      "Amazon CloudWatch"
    ]
  }
}
EOF

cat > notifications.json << EOF
[{
  "Notification": {
    "NotificationType": "ACTUAL",
    "ComparisonOperator": "GREATER_THAN",
    "Threshold": 80
  },
  "Subscribers": [{
    "SubscriptionType": "EMAIL",
    "Address": "tu-email@ejemplo.com"
  }]
}]
EOF

aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

### Monitorear OCI

```bash
# Ver uso de OCI
oci usage-api usage-summary request-summarized-usages \
  --compartment-id <tu_compartment> \
  --time-usage-started "$(date -u -d '1 month ago' '+%Y-%m-%dT%H:%M:%S.000Z')" \
  --time-usage-ended "$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')" \
  --granularity MONTHLY
```

---

## Conclusion

Para la hackaton, el costo total estimado es **< $1.50 USD** (hackaton completo de 4 dias, ~200 quejas de prueba).

Para produccion pequena (5000 quejas/mes, 1 universidad):
- **~$35 USD/mes**
- 5-10x mas barato que usar Claude o GPT-4o
- Cabe en cualquier presupuesto universitario

**Recomendacion**: usar Cohere Command R como primary (es nuestra decision correcta) y mantener Llama 3.1 como fallback (es 6x mas barato que Command R como terciario, y de calidad comparable).
