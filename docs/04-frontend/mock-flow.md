# Mock Flow - Como probar el frontend sin backend

> Guia para correr el frontend de Sentinel AcademIA contra un mock del backend.
> Util durante desarrollo y demos.

---

## Que es Prism?

[Stoplight Prism](https://stoplight.io/open-source/prism) es un mock server que genera respuestas a partir de un OpenAPI spec. Simula el backend real para que puedas:

- Desarrollar el frontend sin esperar al backend
- Hacer demos sin deployar nada
- Hacer tests E2E reproducibles
- Documentar la API con ejemplos ejecutables

---

## Setup rapido (5 minutos)

### Prerequisitos

- Node.js 18+
- npm o pnpm
- El archivo `api-mock/openapi.yaml` (incluido en este repo)

### Paso 1: Instalar Prism

```bash
# Opcion A: Como dev dependency del proyecto
npm install -D @stoplight/prism-cli

# Opcion B: Ejecutar sin instalar (npx)
npx @stoplight/prism-cli --help
```

### Paso 2: Iniciar el mock server

```bash
# Desde la raiz del proyecto
npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010 --dynamic
```

**Argumentos**:
- `mock`: modo mock (vs `proxy` que redigiria a otro servidor)
- `api-mock/openapi.yaml`: ruta al spec
- `-p 4010`: puerto (puede ser cualquiera libre)
- `--dynamic`: genera datos aleatorios realistas (no solo "string")

**Output esperado**:
```
[Prism] Listening on http://127.0.0.1:4010
[Prism] Building example values...
```

### Paso 3: Configurar el frontend

En `web/.env.local` (crear si no existe):

```bash
VITE_API_URL=http://localhost:4010
```

### Paso 4: Iniciar el frontend

```bash
cd web
npm install
npm run dev
```

**Output esperado**:
```
  VITE v5.2.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Paso 5: Probar

1. Abre http://localhost:5173
2. Navega a `/queja` y llena el formulario
3. Mock responde con datos aleatorios
4. Revisa la consola del navegador: deberias ver `x-correlation-id` en cada request

---

## Probar los endpoints manualmente

### Con curl

```bash
# Health check
curl http://localhost:4010/api/quejas

# Crear queja
curl -X POST http://localhost:4010/api/quejas \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Problema con el profesor",
    "descripcion": "No ha asistido a clases en 2 semanas",
    "categoriaDeclarada": "ACADEMICA"
  }'

# Obtener queja
curl http://localhost:4010/api/quejas/12345

# Obtener analisis
curl http://localhost:4010/api/quejas/12345/analysis

# Dashboard
curl http://localhost:4010/api/dashboard/metrics

# Chat
curl -X POST http://localhost:4010/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Cual es el proceso para escalar una queja critica?"
  }'
```

### Con httpie (mas amigable)

```bash
http POST localhost:4010/api/quejas titulo="Test" descripcion="Descripcion de prueba" categoriaDeclarada="OTRA"
```

### Con VS Code REST Client

Crear `api-mock/test.http`:

```http
### Crear queja
POST http://localhost:4010/api/quejas
Content-Type: application/json

{
  "titulo": "Problema con profesor",
  "descripcion": "Descripcion suficientemente larga para validar",
  "categoriaDeclarada": "ACADEMICA"
}

### Listar quejas
GET http://localhost:4010/api/quejas?limit=5

### Dashboard
GET http://localhost:4010/api/dashboard/metrics

### Chat
POST http://localhost:4010/api/chat
Content-Type: application/json

{
  "question": "Cual es el proceso para escalar una queja?"
}
```

---

## Troubleshooting

### Error: "Port 4010 is already in use"

Otro proceso esta usando el puerto. Soluciones:

```bash
# Ver que proceso
lsof -i :4010    # Linux/Mac
netstat -ano | findstr :4010   # Windows

# Cambiar el puerto
npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4011 --dynamic
```

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

Prism deberia incluir CORS por defecto, pero si no:

```bash
# Agregar CORS via proxy en vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:4010',
        changeOrigin: true,
      },
    },
  },
});
```

### El mock no genera datos

`--dynamic` es clave. Sin el, Prism solo devuelve `string` generico.

### Quiero datos mas realistas

Puedes:
1. Agregar `examples` en el OpenAPI spec
2. Usar `--errors=false` para no simular errores
3. Usar un proxy a un mock service worker (MSW) en el frontend

### Quiero validar contra el spec

```bash
# Verifica que el spec sea valido
npx @redocly/cli lint api-mock/openapi.yaml

# Genera tipos TypeScript
npx openapi-typescript api-mock/openapi.yaml -o web/src/types/api.ts
```

---

## Comandos utiles

```bash
# Levantar mock + frontend en paralelo (con concurrently)
npx concurrently \
  "npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010 --dynamic" \
  "cd web && npm run dev"

# O usar npm-run-all
npm run mock:web   # Script combinado

# Solo el mock
npm run mock       # Si esta en package.json
```

### Agregar scripts al package.json raiz

```json
{
  "scripts": {
    "mock": "npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010 --dynamic",
    "web": "cd web && npm run dev",
    "dev:all": "concurrently \"npm run mock\" \"npm run web\""
  }
}
```

---

## Demo del flujo completo

### Script para grabar demo (5 minutos)

```bash
# 1. Iniciar mock
npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010 --dynamic &

# 2. Iniciar frontend
cd web && npm run dev

# 3. En el navegador:
#    a) Ir a http://localhost:5173
#    b) Llenar el form de queja con un caso "critico"
#    c) Ver la confirmacion con el ID
#    d) Ir al dashboard y ver la queja recien creada
#    e) Abrir el chat y preguntar: "Cual es el proceso para una queja critica?"
#    f) Ver la respuesta del asistente

# 4. Capturar pantalla
#    Usar herramienta de screen recording (OBS, Loom, etc.)
```

---

## Limitaciones del mock

Prism NO simula:
- WebSockets / SSE (chat en tiempo real)
- Streams
- Latencia variable
- Fallos intermitentes (a menos que uses `--errors`)

Para simular estos, considera:
- **MSW (Mock Service Worker)**: intercepta fetch en el navegador
- **json-server**: alternativa simple a Prism
- **Server custom en Node**: control total

---

## Proximos pasos

Cuando el backend este listo:
1. Cambiar `VITE_API_URL` al endpoint real de AWS API Gateway
2. Remover `--dynamic` (ya no hace falta mock)
3. Continuar usando el OpenAPI spec como contrato
