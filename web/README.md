# Sentinel AcademIA - Frontend

Frontend Vue 3 + TypeScript para la plataforma de quejas universitarias con IA.

## Stack

- **Vue 3** con Composition API
- **TypeScript** estricto
- **Vite** como build tool
- **Vue Router 4** para navegacion
- **Pinia** para estado global
- **CSS nativo** con custom properties (sin Tailwind)
- **Axios** para HTTP
- **Chart.js** + vue-chartjs para visualizaciones
- **marked** para renderizar markdown en el chat

## Requisitos

- Node.js 18+
- npm 9+ o pnpm

## Setup

```bash
# 1. Instalar dependencias
npm install

# 2. Configurar variables de entorno
cp .env.example .env.local
# Editar VITE_API_URL si es necesario

# 3. Iniciar dev server
npm run dev
# Abre http://localhost:5173
```

## Scripts

| Script | Descripcion |
|---|---|
| `npm run dev` | Inicia dev server con HMR |
| `npm run build` | Build de produccion (typecheck + bundle) |
| `npm run preview` | Preview del build localmente |
| `npm run typecheck` | Valida tipos TypeScript |
| `npm run lint` | Ejecuta ESLint |
| `npm run format` | Formatea con Prettier |
| `npm run test` | Ejecuta tests con Vitest |
| `npm run test:watch` | Tests en watch mode |
| `npm run test:coverage` | Tests con coverage |

## Estructura

```
web/
├── src/
│   ├── assets/styles/      # CSS con custom properties
│   ├── components/
│   │   ├── common/         # Componentes reutilizables
│   │   └── domain/         # Componentes de negocio
│   ├── composables/        # Logica reusable
│   ├── services/           # HTTP clients
│   ├── stores/             # Pinia stores
│   ├── views/              # Paginas (rutas)
│   ├── router/             # Vue Router config
│   ├── types/              # Tipos TypeScript
│   ├── App.vue             # Root component
│   └── main.ts             # Entry point
├── public/                 # Assets estaticos
├── index.html
└── vite.config.ts
```

## Mock con Prism

Para desarrollar sin backend:

```bash
# Terminal 1: Mock server (en raiz del proyecto)
npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010 --dynamic

# Terminal 2: Frontend
cd web && npm run dev
```

## Variables de entorno

| Variable | Descripcion | Default |
|---|---|---|
| `VITE_API_URL` | URL del backend | `http://localhost:4010` |
| `VITE_APP_NAME` | Nombre de la app | `Sentinel AcademIA` |
| `VITE_ENV` | Ambiente actual | `development` |

## Convenciones

- **Composition API** exclusivamente (`<script setup lang="ts">`)
- **Props tipadas** con TypeScript
- **Emits tipados** con tuplas
- **Services** para HTTP, NUNCA fetch directo
- **Composables** para logica reusable
- **Pinia** solo para estado global (auth, notifications)
- **CSS scoped** con custom properties

Ver `docs/04-frontend/arquitectura.md` y `docs/04-frontend/componentes.md` para detalles.

## Deploy

Ver `docs/04-frontend/arquitectura.md` seccion "Deploy a Vercel".

Resumen:
```bash
# Con Vercel CLI
npm install -g vercel
vercel --prod
```

O conectar el repo a Vercel para deploy automatico.

## Troubleshooting

### Puerto 5173 ocupado

```bash
npm run dev -- --port 3000
```

### Error de CORS

El mock de Prism incluye CORS por defecto. Si usas backend real, configura CORS en API Gateway.

### Build falla por tipos

```bash
npm run typecheck
# Corrige los errores antes de hacer build
```

## Documentacion relacionada

- `docs/04-frontend/arquitectura.md` - Arquitectura completa
- `docs/04-frontend/componentes.md` - Catalogo de componentes
- `docs/04-frontend/mock-flow.md` - Como usar el mock
- `api-mock/openapi.yaml` - Contrato de la API
