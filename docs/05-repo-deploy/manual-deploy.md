# Manual de Deploy - Paso a Paso

> Guia completa para desplegar Sentinel AcademIA en AWS Academy + Oracle OCI + Vercel.
> Tiempo estimado: 2-3 horas la primera vez.

---

## Indice
1. [Prerequisitos](#1-prerequisitos)
2. [Setup de AWS Academy](#2-setup-de-aws-academy)
3. [Setup de Oracle OCI](#3-setup-de-oracle-oci)
4. [Deploy del Backend](#4-deploy-del-backend)
5. [Deploy del Frontend](#5-deploy-del-frontend)
6. [Verificacion Post-Deploy](#6-verificacion-post-deploy)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisitos

Antes de empezar, asegurate de tener:

- [ ] Cuenta de AWS Academy activa (con LabRole disponible)
- [ ] Creditos de Oracle Cloud Academy (o cuenta trial)
- [ ] Node.js 20+ instalado
- [ ] Python 3.x (para OCI CLI)
- [ ] Git configurado
- [ ] AWS CLI v2
- [ ] SAM CLI

```bash
# Verificar versiones
node --version    # >= v20
npm --version     # >= 9
git --version
aws --version
sam --version     # >= 1.100
```

---

## 2. Setup de AWS Academy

### 2.1 Obtener credenciales temporales

AWS Academy usa credenciales temporales que caducan cada 3-4 horas.

1. Ingresa a tu laboratorio de AWS Academy
2. Click en "AWS Details" (esquina superior derecha)
3. Click en "Show" en AWS CLI credentials
4. Copia los 3 valores:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN`

### 2.2 Configurar AWS CLI

```bash
aws configure

# Ingresa:
# AWS Access Key ID: <tu_access_key>
# AWS Secret Access Key: <tu_secret_key>
# Default region name: us-east-1
# Default output format: json
```

**Importante**: pega el `AWS_SESSION_TOKEN` como variable de entorno:

```bash
export AWS_SESSION_TOKEN="<tu_session_token>"
```

### 2.3 Verificar acceso

```bash
# Verificar identidad
aws sts get-caller-identity
# Debe mostrar tu usuario y el rol asumido

# Verificar que LabRole existe
aws iam get-role --role-name LabRole

# Verificar region
aws configure get region
# Debe ser us-east-1
```

### 2.4 Crear bucket para SAM artifacts

```bash
# Crear bucket unico para los artifacts de SAM
BUCKET_NAME="sentinel-sam-artifacts-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME --region us-east-1
echo "Bucket creado: $BUCKET_NAME"
# Guardar este nombre para usarlo despues
```

---

## 3. Setup de Oracle OCI

### 3.1 Instalar OCI CLI

```bash
# macOS / Linux
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Responder:
# - Install directory: ~/lib/oracle-cli (default)
# - Add to PATH: yes
# - OCI RC file: no (no por ahora)
# - Tab completion: yes
```

```bash
# Verificar instalacion
oci --version
```

### 3.2 Configurar OCI CLI

```bash
oci setup config
```

Te pedira:
- **User OCID**: lo obtienes en OCI Console → Profile → User Settings
- **Tenancy OCID**: OCI Console → Administration → Tenancy Details
- **Region**: ej. `us-chicago-1`
- **Generate a new API key**: Yes
- **Path for the key**: default `~/.oci/api_key.pem`
- **Fingerprint**: se genera automaticamente, guardalo

### 3.3 Subir la API key publica a OCI

```bash
# Mostrar el fingerprint y la key publica
cat ~/.oci/api_key.pem

# Copiar TODO el contenido
# Ir a OCI Console → Profile → User Settings → API Keys
# Click "Add API Key" → "Paste Public Key"
# Pegar el contenido → Save
```

### 3.4 Crear un compartimento

```bash
# Crear compartimento para el proyecto
oci iam compartment create \
  --compartment-id <tu_tenancy_ocid> \
  --name "SentinelAcademia" \
  --description "Compartment for Sentinel AcademIA project"

# Guardar el OCID del compartimento resultante
```

### 3.5 Probar OCI Generative AI

```bash
# Verificar que puedes listar modelos disponibles
oci generative-ai-inference model list \
  --compartment-id <tu_compartment_ocid> \
  --query 'data[*].display-name' \
  --output table
```

Deberias ver modelos como `cohere.command-r`, `cohere.command-r-plus`, `meta.llama-3.1-70b-instruct`.

### 3.6 Probar una llamada

```bash
# Test rapido
oci generative-ai-inference generate-text \
  --compartment-id <tu_compartment_ocid> \
  --serving-mode '{
    "modelId": "cohere.command-r",
    "servingType": "ON_DEMAND"
  }' \
  --inference-request '{
    "prompt": "Di hola en espanol",
    "maxTokens": 50
  }'
```

### 3.7 Crear Vault (opcional pero recomendado)

```bash
# Crear vault
oci kms vault create \
  --compartment-id <tu_compartment_ocid> \
  --display-name "SentinelVault" \
  --vault-type DEFAULT

# Anotar el OCID del vault
```

---

## 4. Deploy del Backend

### 4.1 Instalar dependencias

```bash
# En la raiz del proyecto
cd sentinel-academia
npm install
cd web && npm install && cd ..
```

### 4.2 Configurar variables de entorno del backend

Crear `src/.env` (NO commitear):

```bash
# OCI
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxxxx
OCI_REGION=us-chicago-1
OCI_CONFIG_FILE=/home/tu-usuario/.oci/config
OCI_CONFIG_PROFILE=DEFAULT

# AWS
AWS_REGION=us-east-1
DYNAMODB_TABLE=quejas
S3_BUCKET=sentinel-quejas-adjuntos
```

### 4.3 Crear el template.yaml (si no lo tienes)

El proyecto ya incluye `src/infra/template.yaml`. Revisa que las propiedades sean correctas.

### 4.4 Crear bucket S3 para adjuntos

```bash
aws s3 mb s3://sentinel-quejas-adjuntos --region us-east-1
```

### 4.5 Build del backend

```bash
cd src/infra
sam build
```

### 4.6 Deploy guiado (primera vez)

```bash
sam deploy --guided
```

Responde:
- **Stack Name**: `sentinel-academia-dev`
- **AWS Region**: `us-east-1`
- **Confirm changes before deploy**: y
- **Allow SAM CLI IAM role creation**: y
- **Save arguments to configuration file**: y
- **SAM configuration file**: `samconfig.toml` (default)
- **S3 bucket**: el bucket que creaste en el paso 2.4
- **Capabilities**: CAPABILITY_IAM
- **Environment**: dev
- **OciCompartmentId**: tu OCID del compartimento

### 4.7 Outputs del deploy

Al terminar, SAM muestra los outputs:

```
Outputs
--------
Key                 ApiUrl
Description         API Gateway endpoint URL
Value               https://abc123.execute-api.us-east-1.amazonaws.com

Key                 QuejasTableName
Value               quejas
```

**Guarda el `ApiUrl`**, lo necesitaras para el frontend.

### 4.8 Smoke test del backend

```bash
# Probar endpoint de quejas
API_URL="<tu_api_url_aqui>"

curl -X POST "$API_URL/quejas" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Test desde curl",
    "descripcion": "Esto es una prueba de smoke test del backend deployado",
    "categoriaDeclarada": "OTRA"
  }'

# Debe responder 202 Accepted con un quejaId
```

### 4.9 Verificar logs

```bash
# Ver logs de las Lambdas
sam logs --stack-name sentinel-academia-dev --tail

# O en CloudWatch Console:
# https://us-east-1.console.aws.amazon.com/cloudwatch/home#logsV2:log-groups
```

---

## 5. Deploy del Frontend

### 5.1 Opcion A: Vercel via GitHub (recomendado)

1. **Subir el repo a GitHub** (si no lo has hecho):

```bash
git init
git add .
git commit -m "feat: initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/sentinel-academia.git
git push -u origin main
```

2. **Conectar a Vercel**:
   - Ir a https://vercel.com/new
   - Importar el repo
   - Configurar:
     - **Framework Preset**: Vite
     - **Root Directory**: `web`
     - **Build Command**: `npm run build`
     - **Output Directory**: `dist`
     - **Install Command**: `npm install`
3. **Variables de entorno**:
   - `VITE_API_URL` = `https://abc123.execute-api.us-east-1.amazonaws.com`
4. **Deploy**

### 5.2 Opcion B: Vercel CLI

```bash
# Instalar
npm install -g vercel

# Login
vercel login

# Deploy
cd web
vercel --prod

# Te pedira configurar el proyecto, seguir las instrucciones
```

### 5.3 Verificacion

1. Abrir la URL publica (ej. `https://sentinel-academia.vercel.app`)
2. Llenar el form de queja
3. Verificar que llega al backend (revisar logs de Lambda)
4. Revisar que no hay errores en consola del navegador

---

## 6. Verificacion Post-Deploy

### Checklist completo

```bash
# 1. Backend responde
curl -X POST $API_URL/quejas \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Test post-deploy","descripcion":"Prueba final despues del deploy completo","categoriaDeclarada":"OTRA"}'

# 2. Frontend accesible
curl -I https://sentinel-academia.vercel.app

# 3. Logs de CloudWatch
aws logs tail /aws/lambda/sentinel-academia-dev-createQuejaFunction --since 10m

# 4. DynamoDB tiene items
aws dynamodb scan --table-name quejas --max-items 5

# 5. OCI GenAI responde
oci generative-ai-inference generate-text \
  --compartment-id $OCI_COMPARTMENT_ID \
  --serving-mode '{"modelId":"cohere.command-r","servingType":"ON_DEMAND"}' \
  --inference-request '{"prompt":"Test","maxTokens":10}'
```

### Verificar que el flujo end-to-end funciona

1. Abrir el frontend desplegado
2. Llenar form con queja "CRITICA" (mencion salud mental o acoso)
3. Ver confirmacion con ID
4. Esperar 30s
5. Ir al dashboard, buscar la queja por ID
6. Verificar que el analisis LLM esta
7. Verificar que la criticidad es CRITICA
8. Verificar en SNS que llego la alerta

---

## 7. Troubleshooting

### "LabRole does not exist"

AWS Academy crea LabRole, pero a veces no lo hace visible. Soluciones:

```bash
# Ver todos los roles
aws iam list-roles --query 'Roles[?contains(RoleName, `Lab`)].RoleName'

# Si no esta, intentar desde la consola de AWS:
# IAM → Roles → Create role → AWS service → Lambda
# Name: LabRole
# Attach: AWSLambdaBasicExecutionRole, AWSLambdaVPCAccessExecutionRole
# (no es lo ideal pero funciona para Academy)
```

### "OCI: 404 Not Found" al llamar GenAI

Verificar:
1. El compartment OCID es correcto
2. La region tiene Generative AI disponible (no todas)
3. El compartment tiene las policies necesarias

```bash
# Verificar regiones con GenAI
oci iam region-subscription list --tenancy-id <tenancy_ocid>
# Buscar: us-chicago-1, eu-frankfurt-1, etc.
```

### "CORS error" en el frontend

Si el backend no responde CORS, agregar en SAM:

```yaml
HttpApi:
  Type: AWS::ApiGatewayV2::Api
  Properties:
    CorsConfiguration:
      AllowOrigins:
        - "*"
      AllowMethods:
        - "*"
      AllowHeaders:
        - "*"
```

Y en cada funcion:

```yaml
Events:
  Api:
    Type: HttpApi
    Properties:
      ApiId: !Ref HttpApi
      # ... otros props
```

### "Lambda timeout"

Si las Lambdas fallan por timeout al llamar a OCI:

```yaml
# En template.yaml
Globals:
  Function:
    Timeout: 60  # Subir de 30 a 60
```

### "Costos excesivos"

Verificar en AWS Console:
- Cost Explorer
- Bills

Configurar budget:

```bash
aws budgets create-budget \
  --account-id <tu_account_id> \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

---

## Comandos utiles del dia a dia

```bash
# Ver logs de una Lambda especifica
sam logs -n CreateQuejaFunction --tail

# Re-deploy rapido
sam build && sam deploy

# Rollback al deploy anterior
sam deploy --no-disable-rollback
# Y en la consola de CloudFormation, click "Actions" → "Continue rollback"

# Eliminar todo (para empezar de cero)
sam delete --stack-name sentinel-academia-dev

# Ver outputs del stack
aws cloudformation describe-stacks \
  --stack-name sentinel-academia-dev \
  --query 'Stacks[0].Outputs'
```

---

## Costos esperados (referencia)

| Concepto | Hackathon (4 dias, ~100 quejas) | Produccion (mensual) |
|---|---|---|
| AWS Lambda | $0.00 | $0.01 |
| AWS API Gateway | $0.00 | $0.05 |
| AWS DynamoDB | $0.05 | $2.50 |
| AWS SQS/SNS/EB | $0.00 | $0.05 |
| AWS S3 | $0.00 | $0.30 |
| AWS CloudWatch + X-Ray | $0.10 | $0.50 |
| OCI GenAI (Cohere R) | $0.50 | $25.00 |
| OCI GenAI (Llama fallback) | $0.10 | $2.00 |
| OCI Document AI | $0.00 | $5.00 |
| Vercel | $0.00 | $0.00 |
| **TOTAL** | **~$0.75** | **~$35.00/mes** |

Ver [`costos.md`](costos.md) para desglose detallado.

---

## Cuando termines

1. Guarda las URLs publicas (frontend + API)
2. Anota las credenciales de OCI (las necesitaras en el video)
3. Graba el video demo
4. Comparte el repo

**Exito!**
