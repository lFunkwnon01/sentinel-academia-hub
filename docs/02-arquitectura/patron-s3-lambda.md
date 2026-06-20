# Patron S3 + Lambda para Upload de Archivos

> Guia completa para implementar el flujo de upload de archivos adjuntos a las quejas.
> Dos patrones: Presigned URL (recomendado) y Directo (simple).

---

## Indice
1. [Vision general](#vision-general)
2. [Patron A: Presigned URL (RECOMENDADO)](#patron-a-presigned-url-recomendado)
3. [Patron B: Upload Directo (alternativo)](#patron-b-upload-directo-alternativo)
4. [Codigo completo de las Lambdas](#codigo-completo-de-las-lambdas)
5. [SAM Template (template.yaml)](#sam-template-templateyaml)
6. [CORS y permisos](#cors-y-permisos)
7. [Flujo end-to-end](#flujo-end-to-end)

---

## Vision general

En Sentinel AcademIA, los usuarios pueden adjuntar archivos a sus quejas (PDFs, imagenes). Necesitamos:

1. Almacenar los archivos de forma segura y escalable (S3)
2. Procesarlos despues con OCI Document Understanding (para extraer texto)
3. No saturar las Lambdas con archivos grandes
4. Tener URLs temporales (no permanentes) para acceder a los archivos

---

## Patron A: Presigned URL (RECOMENDADO)

### Flujo visual

```
[Frontend Vue]              [API Gateway]                [Lambda getUploadUrl]            [S3]
    |                              |                              |                        |
    | 1. POST /api/quejas (sin archivos)                            |                        |
    |   { titulo, descripcion, ...}                                  |                        |
    |----------------------------->|                              |                        |
    |                              | createQueja (sincronico)     |                        |
    |                              | - valida input               |                        |
    |                              | - crea registro en DynamoDB  |                        |
    |                              | - devuelve 202 con quejaId   |                        |
    | <----------------------------|                              |                        |
    | { quejaId, status: EN_COLA }|                              |                        |
    |                              |                              |                        |
    | 2. Por cada archivo a subir: |                              |                        |
    |   POST /api/uploads/presigned |                             |                        |
    |   { quejaId, filename, type }|                              |                        |
    |----------------------------->|                              |                        |
    |                              | getUploadUrl                 |                        |
    |                              | (verifica queja existe)      |                        |
    |                              | (genera presigned URL)──────>|
    |                              |                              | 3. s3.getSignedUrl(...)|
    | <----------------------------|                              | (expira en 5 min)     |
    | { uploadUrl, key, fields }   |                              |                        |
    |                              |                              |                        |
    | 4. PUT archivo (DIRECTO)     |                              |                        |
    |   Content-Type: image/jpeg   |                              |                        |
    |   Body: <binary>             |                              |                        |
    |---------------------------------------------------------------------------->|
    |                              |                              |                        |
    |                              |                              | 5. S3 Event ──────> Lambda fileProcessor
    |                              |                              |                (SQS Event Source Mapping)
    |                              |                              |                - GetObject del archivo
    |                              |                              |                - Llama a OCI Document AI
    |                              |                              |                - Guarda texto extraido en DynamoDB
    |                              |                              |                - Marca "texto extraido" en queja
    |                              |                              |                        |
    | 6. POST /api/quejas/:id/finalize (opcional)                 |                        |
    |   cuando todos los archivos subieron                        |                        |
    |----------------------------->|                              |                        |
    |                              | finalizeQueja                |                        |
    |                              | - encola para analisis LLM  |                        |
```

### Codigo: Lambda getUploadUrl

```typescript
// src/handlers/getUploadUrl.ts
import { APIGatewayProxyHandlerV2 } from 'aws-lambda';
import { z } from 'zod';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { docClient, TABLE_NAME } from './_shared/dynamoClient';
import { GetCommand } from '@aws-sdk/lib-dynamodb';
import { logger } from './_shared/logger';
import { ok, badRequest, notFound, serverError } from './_shared/httpResponse';
import { withErrorHandling } from './_shared/errors';

const s3 = new S3Client({ region: process.env.AWS_REGION });
const BUCKET = process.env.S3_BUCKET!;
const URL_EXPIRATION = 300; // 5 minutos

const InputSchema = z.object({
  quejaId: z.string().uuid(),
  filename: z.string().min(1).max(255),
  contentType: z.string().regex(/^(image|application)\/(jpeg|jpg|png|pdf|webp)$/),
});

export const handler: APIGatewayProxyHandlerV2 = withErrorHandling(async (event) => {
  const body = JSON.parse(event.body ?? '{}');
  const parsed = InputSchema.safeParse(body);
  if (!parsed.success) {
    return badRequest('Invalid input', parsed.error.flatten(), getCorrelationId(event));
  }
  const { quejaId, filename, contentType } = parsed.data;

  // Verificar que la queja existe
  const queja = await docClient.send(new GetCommand({
    TableName: TABLE_NAME,
    Key: { pk: `QUEJA#${quejaId}`, sk: 'META' },
  }));
  if (!queja.Item) {
    return notFound('Queja no encontrada', getCorrelationId(event));
  }

  // Generar key unica
  const extension = filename.split('.').pop();
  const key = `quejas/${quejaId}/${crypto.randomUUID()}.${extension}`;

  // Generar presigned URL
  const command = new PutObjectCommand({
    Bucket: BUCKET,
    Key: key,
    ContentType: contentType,
    Metadata: {
      quejaId,
      originalFilename: filename,
      uploadedAt: new Date().toISOString(),
    },
  });
  const uploadUrl = await getSignedUrl(s3, command, { expiresIn: URL_EXPIRATION });

  logger.info('Presigned URL generada', { quejaId, key, contentType });

  return ok({
    uploadUrl,
    key,
    expiresIn: URL_EXPIRATION,
    headers: {
      'Content-Type': contentType,
    },
  }, getCorrelationId(event));
});
```

### Codigo: Lambda fileProcessor (triggered by S3)

```typescript
// src/handlers/fileProcessor.ts
import { S3Event, SQSBatchResponse } from 'aws-lambda';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { Readable } from 'stream';
import { ociDocAi } from '../services/ociDocAi';
import { docClient, TABLE_NAME } from './_shared/dynamoClient';
import { UpdateCommand } from '@aws-sdk/lib-dynamodb';
import { logger } from './_shared/logger';

const s3 = new S3Client({ region: process.env.AWS_REGION });

export const handler = async (event: S3Event): Promise<SQSBatchResponse> => {
  const failures: { itemIdentifier: string }[] = [];

  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));
    const quejaId = key.split('/')[1]; // quejas/{quejaId}/{uuid}.pdf

    try {
      logger.info('Procesando archivo', { quejaId, key });

      // 1. Descargar de S3
      const obj = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
      const stream = obj.Body as Readable;
      const chunks: Buffer[] = [];
      for await (const chunk of stream) {
        chunks.push(chunk as Buffer);
      }
      const buffer = Buffer.concat(chunks);

      // 2. Extraer texto con OCI Document AI
      const contentType = obj.ContentType || 'application/octet-stream';
      const textoExtraido = await ociDocAi.extractText(buffer, contentType);

      logger.info('Texto extraido', { quejaId, key, length: textoExtraido.length });

      // 3. Guardar en DynamoDB
      await docClient.send(new UpdateCommand({
        TableName: TABLE_NAME,
        Key: { pk: `QUEJA#${quejaId}`, sk: 'ATTACHMENT#' + key },
        UpdateExpression: 'SET textoExtraido = :t, processedAt = :p, status = :s',
        ExpressionAttributeValues: {
          ':t': textoExtraido,
          ':p': new Date().toISOString(),
          ':s': 'TEXTO_EXTRAIDO',
        },
      }));

      // 4. Agregar el texto al acumulado de la queja
      await docClient.send(new UpdateCommand({
        TableName: TABLE_NAME,
        Key: { pk: `QUEJA#${quejaId}`, sk: 'META' },
        UpdateExpression: 'SET textoArchivos = list_append(if_not_exists(textoArchivos, :empty), :t)',
        ExpressionAttributeValues: {
          ':t': [textoExtraido],
          ':empty': [],
        },
      }));
    } catch (err) {
      logger.error('Error procesando archivo', {
        quejaId,
        key,
        error: String(err),
      });
      failures.push({ itemIdentifier: record.s3.object.key });
    }
  }

  return { batchItemFailures: failures };
};
```

---

## Patron B: Upload Directo (alternativo)

### Flujo

```
[Frontend]              [API Gateway]              [Lambda createQueja]              [S3]
    |                          |                            |                         |
    | 1. POST /api/quejas (multipart/form-data)            |                         |
    |   - titulo              |                            |                         |
    |   - descripcion         |                            |                         |
    |   - archivo1 (binary)   |                            |                         |
    |   - archivo2 (binary)   |                            |                         |
    |------------------------->|                            |                         |
    |                          | createQueja                |                         |
    |                          | - valida input             |                         |
    |                          | - parsea multipart         |                         |
    |                          | - sube cada archivo a S3 ────────────────────────>|
    |                          | - crea registro en DDB     |                         |
    |                          | - encola para analisis     |                         |
    |                          | - responde 202             |                         |
    | <------------------------|                            |                         |
    |                          |                            |                         |
```

### Limitaciones

- **API Gateway** limita requests a **10 MB** por body
- **Lambda** tiene maximo de **10 GB** de memoria (limite practico ~1 GB)
- Para archivos grandes, este patron NO funciona

### Codigo simplificado

```typescript
// src/handlers/createQuejaWithFiles.ts
import { APIGatewayProxyHandlerV2 } from 'aws-lambda';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { docClient, TABLE_NAME } from './_shared/dynamoClient';
import { PutCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';
import { logger } from './_shared/logger';
import { accepted, badRequest, serverError } from './_shared/httpResponse';
import { withErrorHandling } from './_shared/errors';
import { randomUUID, createHash } from 'crypto';

const s3 = new S3Client({ region: process.env.AWS_REGION });
const sqs = new SQSClient({ region: process.env.AWS_REGION });
const BUCKET = process.env.S3_BUCKET!;
const QUEUE_URL = process.env.PROCESS_QUEUE_URL!;

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];

export const handler: APIGatewayProxyHandlerV2 = withErrorHandling(async (event) => {
  // API Gateway con binary media type o base64
  const contentType = event.headers['content-type'] || '';
  
  if (!contentType.startsWith('multipart/form-data')) {
    return badRequest('Expected multipart/form-data', null, getCorrelationId(event));
  }

  // Parsear multipart (simplificado - en produccion usar aws-multipart-parser)
  const parts = parseMultipart(event.body || '', event.isBase64Encoded);
  const metadata = parts.find(p => p.name === 'metadata');
  const files = parts.filter(p => p.name === 'archivos');

  if (!metadata) {
    return badRequest('Missing metadata', null, getCorrelationId(event));
  }

  // Validar archivos
  for (const file of files) {
    if (file.data.length > MAX_FILE_SIZE) {
      return badRequest(`File ${file.filename} exceeds 5MB`, null, getCorrelationId(event));
    }
    if (!ALLOWED_TYPES.includes(file.contentType)) {
      return badRequest(`File type ${file.contentType} not allowed`, null, getCorrelationId(event));
    }
  }

  const quejaId = randomUUID();
  const uploadedKeys: string[] = [];

  // Subir cada archivo a S3
  for (const file of files) {
    const key = `quejas/${quejaId}/${randomUUID()}-${file.filename}`;
    await s3.send(new PutObjectCommand({
      Bucket: BUCKET,
      Key: key,
      Body: file.data,
      ContentType: file.contentType,
      Metadata: { quejaId, originalFilename: file.filename },
    }));
    uploadedKeys.push(key);
  }

  // Guardar queja en DynamoDB
  const meta = JSON.parse(metadata.data.toString());
  await docClient.send(new PutCommand({
    TableName: TABLE_NAME,
    Item: {
      pk: `QUEJA#${quejaId}`,
      sk: 'META',
      quejaId,
      ...meta,
      adjuntos: uploadedKeys,
      status: 'EN_COLA',
      createdAt: new Date().toISOString(),
      ttl: Math.floor(Date.now() / 1000) + (90 * 24 * 60 * 60),
    },
  }));

  // Encolar para procesamiento async
  const idempotencyKey = createHash('sha256').update(JSON.stringify({ quejaId, ...meta })).digest('hex');
  await sqs.send(new SendMessageCommand({
    QueueUrl: QUEUE_URL,
    MessageBody: JSON.stringify({
      eventType: 'queja.creada',
      payload: { quejaId, input: meta, adjuntos: uploadedKeys },
      metadata: { correlationId: getCorrelationId(event), idempotencyKey },
    }),
  }));

  logger.info('Queja creada con archivos', { quejaId, files: uploadedKeys.length });

  return accepted({
    quejaId,
    status: 'EN_COLA',
    adjuntos: uploadedKeys,
  }, getCorrelationId(event));
});
```

---

## SAM Template (template.yaml)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: nodejs20.x
    MemorySize: 512
    Timeout: 30
    Tracing: Active
    Environment:
      Variables:
        DYNAMODB_TABLE: !Ref QuejasTable
        S3_BUCKET: !Ref AdjuntosBucket
        SES_FROM_EMAIL: !Ref SesFromEmail
        LOG_LEVEL: INFO

Resources:
  # ============================================
  # S3 Bucket para adjuntos
  # ============================================
  AdjuntosBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'sentinel-quejas-adjuntos-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldVersions
            Status: Enabled
            NoncurrentVersionExpirationInDays: 30
          - Id: ExpireIncompleteUploads
            Status: Enabled
            AbortIncompleteMultipartUpload:
              DaysAfterInitiation: 1
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      CorsConfiguration:
        CorsRules:
          - AllowedHeaders: ['*']
            AllowedMethods: [GET, PUT, POST]
            AllowedOrigins:
              - 'https://sentinel-academia.vercel.app'
              - 'http://localhost:5173'
            MaxAge: 3000

  # ============================================
  # SQS Queue para archivos subidos
  # ============================================
  FileProcessingQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: file-processing-queue
      VisibilityTimeout: 300
      MessageRetentionPeriod: 1209600
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt FileProcessingDLQ.Arn
        maxReceiveCount: 3

  FileProcessingDLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: file-processing-dlq
      MessageRetentionPeriod: 1209600

  # ============================================
  # S3 Event Notification -> SQS
  # ============================================
  BucketNotificationRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: AllowSQSPublish
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - sqs:SendMessage
                Resource: !GetAtt FileProcessingQueue.Arn

  BucketNotification:
    Type: AWS::S3::Bucket
    DependsOn: BucketNotificationPolicy
    Properties:
      Bucket: !Ref AdjuntosBucket
      NotificationConfiguration:
        QueueConfigurations:
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt FileProcessingQueue.Arn

  BucketNotificationPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref AdjuntosBucket
      PolicyDocument:
        Statement:
          - Sid: AllowS3ToSendMessageToSQS
            Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action: sqs:SendMessage
            Resource: !GetAtt FileProcessingQueue.Arn

  # ============================================
  # Lambda: getUploadUrl (presigned URL)
  # ============================================
  GetUploadUrlFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/
      Handler: getUploadUrl.handler
      Description: Genera presigned URL para upload a S3
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /uploads/presigned
            Method: POST
      Policies:
        - S3WritePolicy:
            BucketName: !Ref AdjuntosBucket
        - DynamoDBReadPolicy:
            TableName: !Ref QuejasTable

  # ============================================
  # Lambda: fileProcessor (consumer de SQS)
  # ============================================
  FileProcessorFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/
      Handler: fileProcessor.handler
      Description: Procesa archivos subidos (extrae texto con OCI Document AI)
      MemorySize: 1024
      Timeout: 120
      Events:
        SQS:
          Type: SQS
          Properties:
            Queue: !GetAtt FileProcessingQueue.Arn
            BatchSize: 5
      Policies:
        - S3ReadPolicy:
            BucketName: !Ref AdjuntosBucket
        - DynamoDBCrudPolicy:
            TableName: !Ref QuejasTable

  # ============================================
  # Lambda: notifyByEmail (consumer de SNS)
  # ============================================
  NotifyByEmailFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/
      Handler: notifyByEmail.handler
      Description: Envia emails via SES cuando se detecta caso critico
      MemorySize: 256
      Timeout: 30
      Events:
        SNS:
          Type: SNS
          Properties:
            Topic: !Ref CriticalAlertsTopic
      Policies:
        - SESFullAccess

  # ============================================
  # SNS Topic para alertas criticas
  # ============================================
  CriticalAlertsTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: critical-alerts
      Subscription:
        - Endpoint: bienestar@universidad.edu
          Protocol: email
        - Endpoint: director@universidad.edu
          Protocol: email

  # ============================================
  # SES Email Identity (verificar dominio)
  # ============================================
  SesFromEmail:
    Type: AWS::SES::EmailIdentity
    Properties:
      EmailIdentity: alerts@sentinel-academia.com
```

---

## CORS y permisos

### CORS en S3

El bucket S3 debe permitir el origen del frontend:

```yaml
CorsConfiguration:
  CorsRules:
    - AllowedOrigins:
        - 'https://sentinel-academia.vercel.app'
        - 'http://localhost:5173'
      AllowedMethods: [PUT, POST]
      AllowedHeaders: ['*']
      ExposeHeaders: [ETag]
      MaxAge: 3000
```

### Permisos de la Lambda getUploadUrl

```yaml
Policies:
  - S3WritePolicy:
      BucketName: !Ref AdjuntosBucket
  - DynamoDBReadPolicy:
      TableName: !Ref QuejasTable
```

### Permisos del frontend

El frontend NO necesita credenciales de AWS para subir (usa la presigned URL directamente). Pero el navegador debe permitir CORS al bucket.

---

## Flujo end-to-end completo

### Paso 1: Usuario crea queja sin archivos
```bash
POST /api/quejas
{
  "titulo": "Problema con profesor",
  "descripcion": "..."
}
```
Respuesta: 202 `{ quejaId: "q-abc-123", status: "EN_COLA" }`

### Paso 2: Usuario pide URL para subir archivo
```bash
POST /api/uploads/presigned
{
  "quejaId": "q-abc-123",
  "filename": "evidencia.pdf",
  "contentType": "application/pdf"
}
```
Respuesta: 200 `{ uploadUrl: "https://s3...", key: "quejas/q-abc-123/xyz.pdf", expiresIn: 300 }`

### Paso 3: Frontend sube directo a S3
```javascript
await fetch(uploadUrl, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/pdf' },
  body: fileBlob,
});
```

### Paso 4: S3 notifica a SQS
S3 dispara evento a SQS automaticamente.

### Paso 5: Lambda fileProcessor procesa
- Descarga el archivo de S3
- Llama a OCI Document Understanding
- Extrae el texto
- Guarda en DynamoDB

### Paso 6: Cuando todos los archivos estan listos
- El analisis LLM (processQueja) lee `textoArchivos` de DynamoDB
- Lo combina con la descripcion
- Genera el analisis completo

### Paso 7: Si el analisis es CRITICA
- EventBridge dispara a SNS
- Lambda notifyByEmail envia email via SES a bienestar y director

---

## Resumen: Que patron usar

| Criterio | Presigned URL | Directo |
|---|---|---|
| Archivos < 5MB | Si (recomendado) | OK |
| Archivos > 5MB | Si (obligatorio) | NO funciona |
| Archivos > 100MB | Si (usar multipart) | NO funciona |
| Complejidad de implementacion | Media | Baja |
| Velocidad de upload | Alta (directo) | Media (proxy) |
| Costo | Bajo (solo S3) | Alto (Lambda compute) |
| Seguridad | URLs temporales | Token-based |
| Produccion | ✅ Recomendado | Solo hackathon |
