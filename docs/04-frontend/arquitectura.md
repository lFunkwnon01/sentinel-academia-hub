# Arquitectura del Frontend - Sentinel AcademIA

> Criterio 4: Frontend y Experiencia de Usuario
> Documento complementario al codigo en `web/`

---

## Indice

1. [Stack Tecnologico](#stack-tecnologico)
2. [Decisiones de Arquitectura](#decisiones-de-arquitectura)
3. [Estructura de Carpetas](#estructura-de-carpetas)
4. [Sistema de Diseno](#sistema-de-diseno)
5. [Patrones de Componentes](#patrones-de-componentes)
6. [Composables y Services](#composables-y-services)
7. [Estado Global (Pinia)](#estado-global-pinia)
8. [Routing y Navegacion](#routing-y-navegacion)
9. [Accesibilidad](#accesibilidad)
10. [Performance](#performance)
11. [Mock con Prism](#mock-con-prism)
12. [Deploy a Vercel](#deploy-a-vercel)

---

## Stack Tecnologico

| Capa | Tecnologia | Version | Justificacion |
|---|---|---|---|
| Framework | Vue 3 | ^3.4 | Composition API, mejor DX que React para nuestro caso |
| Lenguaje | TypeScript | ^5.4 | Type safety end-to-end |
| Build tool | Vite | ^5.2 | Rapido, HMR excelente, build optimizado |
| Router | Vue Router | ^4.3 | Estandar oficial de Vue |
| Estado global | Pinia | ^2.1 | Estandar oficial, reemplaza Vuex |
| HTTP client | Axios | ^1.6 | Interceptors, manejo de errores |
| Validacion | Zod | ^3.22 | Mismo schema que backend |
| Markdown | marked | ^12 | Para renderizar respuestas del chat |
| Charts | Chart.js + vue-chartjs | ^4 | Dashboard con metricas |
| Iconos | Heroicons (inline SVG) | - | Sin dependencia externa |
| Estilos | CSS nativo + custom properties | - | Sin Tailwind por requisito del proyecto |
| Tests | Vitest + @vue/test-utils | ^1.4 | Rapido, mismo API que Jest |
| Lint | ESLint + Prettier | - | Estandar de la industria |
| Deploy | Vercel | - | Free tier, CDN global, previews por PR |

**PROHIBIDO en este proyecto**:
- Tailwind, Bootstrap, Material UI, cualquier framework CSS
- Options API (usar siempre Composition API)
- Fetch directo en componentes (usar services)
- TypeScript laxo (cero `any`)

---

## Decisiones de Arquitectura

### AD-FE-001: SPA en Vercel (no SSR)

**Contexto**: Necesitamos una UI interactiva con dashboard tiempo real y chat.

**Decision**: Vue 3 SPA (Single Page Application) deployado en Vercel.

**Consecuencias**:
- (+) Build simple y rapido
- (+) Hosting gratuito con CDN global
- (+) Previews automaticos por PR
- (-) SEO limitado (no relevante: app tras autenticacion)
- (-) TTFB depende de bundle size (mitigado con code splitting)

### AD-FE-002: Composition API exclusivamente

**Contexto**: Vue 3 soporta Options API y Composition API.

**Decision**: Solo Composition API con `<script setup lang="ts">`.

**Consecuencias**:
- (+) Mejor tree-shaking
- (+) Reutilizacion via composables
- (+) Mejor TypeScript inference
- (-) Requiere disciplina del equipo (no caer en Options API)

### AD-FE-003: Estado local vs global

**Contexto**: No todo estado necesita Pinia.

**Decision**:
- **Local (ref, reactive)**: estado de UI de UN componente (loading, error, form values)
- **Composable compartido**: logica reusable (useQuejas, useChat)
- **Pinia (global)**: solo lo que cruza multiples vistas:
  - `auth` (usuario actual, token)
  - `notifications` (toasts globales)

**Consecuencias**:
- (+) Stores pequenos y enfocados
- (+) Performance (no re-renders innecesarios)
- (-) Requiere criterio del equipo

### AD-FE-004: CSS nativo con design tokens

**Contexto**: Tailwind fue prohibido por el equipo.

**Decision**: CSS con custom properties en `:root` (variables.css).

**Consecuencias**:
- (+) Sin dependencias
- (+) Theming facil (cambiar variables en runtime)
- (+) Codigo legible (no clases utility)
- (-) Mas verbose que utility-first

### AD-FE-005: Code splitting por ruta

**Contexto**: Bundle inicial debe ser pequeno.

**Decision**: Lazy load de cada vista en el router.

**Consecuencias**:
- (+) Bundle inicial ~50KB (no 500KB)
- (+) TTFB < 1s
- (-) Carga perezosa al cambiar de ruta (aceptable)

### AD-FE-006: Mock-first con Prism

**Contexto**: Necesitamos desarrollar el frontend antes de que el backend este listo.

**Decision**: Usar Stoplight Prism como mock server local basado en OpenAPI spec.

**Consecuencias**:
- (+) Frontend y backend se desarrollan en paralelo
- (+) Tests E2E pueden correr contra el mock
- (+) Demo del frontend sin deployar backend
- (-) Mock puede divergir del backend real (mitigado con OpenAPI sincronizado)

---

## Estructura de Carpetas

```
web/
├── public/
│   ├── favicon.svg
│   └── robots.txt
├── src/
│   ├── assets/
│   │   ├── icons/                    # SVG icons inline
│   │   └── styles/
│   │       ├── variables.css         # Design tokens (colores, spacing, etc.)
│   │       └── main.css              # Reset + base styles
│   ├── components/
│   │   ├── common/                   # Componentes reutilizables
│   │   │   ├── AppButton.vue
│   │   │   ├── AppInput.vue
│   │   │   ├── AppTextarea.vue
│   │   │   ├── AppSelect.vue
│   │   │   ├── AppCard.vue
│   │   │   ├── AppModal.vue
│   │   │   ├── AppSpinner.vue
│   │   │   ├── AppToast.vue
│   │   │   ├── AppBadge.vue
│   │   │   └── AppEmpty.vue
│   │   └── domain/                   # Componentes de negocio
│   │       ├── QuejaForm.vue
│   │       ├── QuejaCard.vue
│   │       ├── QuejaList.vue
│   │       ├── AnalysisBadge.vue
│   │       ├── CriticidadIndicator.vue
│   │       ├── DashboardChart.vue
│   │       ├── DashboardMetricCard.vue
│   │       ├── ChatMessage.vue
│   │       └── ChatInput.vue
│   ├── views/
│   │   ├── HomeView.vue              # Landing publica
│   │   ├── QuejaView.vue             # Form de queja
│   │   ├── DashboardView.vue        # Dashboard autoridades
│   │   ├── ChatView.vue              # Chat con RAG
│   │   └── NotFoundView.vue          # 404
│   ├── composables/
│   │   ├── useQuejas.ts              # Logica de quejas
│   │   ├── useChat.ts                # Logica de chat
│   │   ├── useToast.ts               # Wrapper del store notifications
│   │   └── useCorrelationId.ts       # Generar/obtener correlationId
│   ├── services/
│   │   ├── apiClient.ts              # Axios configurado
│   │   ├── quejaService.ts           # CRUD de quejas
│   │   ├── chatService.ts            # Chat con RAG
│   │   └── dashboardService.ts       # Metricas
│   ├── stores/
│   │   ├── auth.ts                   # Pinia: usuario actual
│   │   └── notifications.ts          # Pinia: toasts
│   ├── router/
│   │   └── index.ts                  # Rutas lazy-loaded
│   ├── types/
│   │   ├── api.ts                    # Tipos del OpenAPI
│   │   ├── domain.ts                 # Tipos del dominio
│   │   └── index.ts
│   ├── App.vue
│   └── main.ts
├── tests/
│   ├── setup.ts
│   └── components/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── .env.example
├── .gitignore
└── README.md
```

---

## Sistema de Diseno

### Design Tokens (variables.css)

```css
:root {
  /* Colores primarios */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-light: #dbeafe;
  --color-secondary: #64748b;

  /* Colores semanticos */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-info: #3b82f6;

  /* Criticidad (dominio) */
  --color-crit-low: #10b981;
  --color-crit-medium: #f59e0b;
  --color-crit-high: #f97316;
  --color-crit-critical: #dc2626;

  /* Colores de fondo */
  --color-bg: #ffffff;
  --color-bg-elevated: #f8fafc;
  --color-bg-muted: #f1f5f9;

  /* Texto */
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-text-inverse: #ffffff;

  /* Bordes */
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;

  /* Espaciado (escala 0.25rem) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* Tipografia */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  /* Pesos */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* Radios */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;

  /* Sombras */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);

  /* Transiciones */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);

  /* Z-index */
  --z-dropdown: 100;
  --z-modal: 200;
  --z-toast: 300;
  --z-tooltip: 400;
}

/* Modo oscuro (futuro) */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0f172a;
    --color-bg-elevated: #1e293b;
    --color-text: #f1f5f9;
    /* ... */
  }
}
```

### Tipografia

```css
body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg);
}

h1 { font-size: var(--text-4xl); font-weight: var(--font-bold); }
h2 { font-size: var(--text-3xl); font-weight: var(--font-semibold); }
h3 { font-size: var(--text-2xl); font-weight: var(--font-semibold); }
h4 { font-size: var(--text-xl); font-weight: var(--font-medium); }
```

---

## Patrones de Componentes

### 1. Componentes "common" (atoms/molecules)

Son reutilizables, sin logica de negocio. Ejemplos:
- `AppButton` con variants (`primary`, `secondary`, `danger`, `ghost`)
- `AppInput` con validacion visual
- `AppCard` con slot para header/body/footer
- `AppSpinner` para loading states
- `AppToast` para notificaciones

### 2. Componentes "domain" (organisms)

Conocen el dominio, usan los servicios. Ejemplos:
- `QuejaForm` - usa `quejaService.create()`
- `QuejaCard` - muestra una queja con su analisis
- `AnalysisBadge` - muestra criticidad con color
- `ChatMessage` - renderiza mensaje del chat con markdown

### 3. Composables (logica reusable)

Encapsulan estado + acciones, sin UI. Ejemplos:
- `useQuejas()` - CRUD de quejas con loading/error states
- `useChat()` - envio de mensajes, historial, streaming
- `useToast()` - wrapper del store de notifications

### 4. Services (HTTP)

Toda llamada HTTP va aqui. NUNCA fetch directo en componentes.

```typescript
// quejaService.ts
export const quejaService = {
  async create(input: CreateQuejaInput): Promise<QuejaAccepted> {
    const { data } = await apiClient.post<QuejaAccepted>('/api/quejas', input);
    return data;
  },
  async getById(id: string): Promise<Queja> {
    const { data } = await apiClient.get<Queja>(`/api/quejas/${id}`);
    return data;
  },
  async list(filters?: QuejaFilters): Promise<QuejaListResponse> {
    const { data } = await apiClient.get<QuejaListResponse>('/api/quejas', { params: filters });
    return data;
  },
  async getAnalysis(id: string): Promise<Analisis> {
    const { data } = await apiClient.get<Analisis>(`/api/quejas/${id}/analysis`);
    return data;
  },
};
```

---

## Composables y Services

### Composables como capa de abstraccion

Los componentes consumen composables, no services directamente:

```vue
<!-- QuejaView.vue -->
<script setup lang="ts">
import { useQuejas } from '@/composables/useQuejas';

const { crearQueja, loading, error } = useQuejas();

async function onSubmit(input: CreateQuejaInput) {
  try {
    const result = await crearQueja(input);
    // manejar exito
  } catch (e) {
    // error ya esta en el composable
  }
}
</script>
```

**Por que?**
- El componente no conoce el service (testeable con mock del composable)
- El composable encapsula loading/error (componente solo consume)
- Si cambia la implementacion del service, el componente no se entera

---

## Estado Global (Pinia)

### Stores minimos

Solo lo que cruza multiples vistas:

```typescript
// stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const isAuthenticated = computed(() => user.value !== null);

  function login(userData: User) { user.value = userData; }
  function logout() { user.value = null; }

  return { user, isAuthenticated, login, logout };
});

// stores/notifications.ts
export const useNotificationStore = defineStore('notifications', () => {
  const toasts = ref<Toast[]>([]);

  function show(toast: Omit<Toast, 'id'>) {
    const id = crypto.randomUUID();
    toasts.value.push({ id, ...toast });
    setTimeout(() => dismiss(id), toast.duration ?? 5000);
  }

  function dismiss(id: string) {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }

  return { toasts, show, dismiss };
});
```

### NO usar Pinia para

- Formularios (usar ref local)
- Estado de UI de un componente (modals, dropdowns)
- Listas de datos (usar composables)
- Estados de loading/error (en composables)

---

## Routing y Navegacion

### Lazy loading por ruta

```typescript
// router/index.ts
const routes = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  { path: '/queja', name: 'queja', component: () => import('@/views/QuejaView.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/chat', name: 'chat', component: () => import('@/views/ChatView.vue') },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue') },
];
```

### Guards de navegacion

```typescript
router.beforeEach((to, from, next) => {
  // Generar correlationId por sesion de navegacion
  if (!sessionStorage.getItem('correlationId')) {
    sessionStorage.setItem('correlationId', crypto.randomUUID());
  }
  next();
});
```

---

## Accesibilidad

### Patrones implementados

- **Labels** en todos los inputs (`<label for="...">`)
- **aria-*** attributes donde sean necesarios
- **Focus visible** con outline azul (`:focus-visible`)
- **Contraste** minimo 4.5:1 (cumple WCAG AA)
- **Roles ARIA** en componentes interactivos custom
- **Skip links** para saltar al contenido principal
- **Mensajes de error** anunciados con `aria-live="polite"`
- **Navegacion por teclado** funcional en todos los flujos
- **Reduced motion** respetado (`@media (prefers-reduced-motion: reduce)`)

### Componentes accesibles

```vue
<!-- AppButton.vue -->
<button
  :type="type"
  :disabled="disabled"
  :aria-busy="loading"
  :aria-label="ariaLabel ?? label"
  @click="onClick"
>
  <AppSpinner v-if="loading" aria-hidden="true" />
  <slot />
</button>
```

---

## Performance

### Tecnicas aplicadas

1. **Code splitting**: lazy load de vistas
2. **Tree shaking**: solo importes lo necesario
3. **Asset optimization**: imagenes con `loading="lazy"`, SVGs inline
4. **Debounce en busquedas**: 300ms
5. **Virtual scrolling** para listas largas (futuro)
6. **Memoization** de computeds costosos
7. **Bundle analyzer**: ver que ocupa mas espacio

### Bundle objetivo

- Inicial: < 200 KB (gzipped)
- Por ruta lazy: < 50 KB
- Total: < 500 KB

### Medir

```bash
# Build con visualizacion
npm run build -- --mode analyze

# Lighthouse
npx lighthouse https://sentinel-academia.vercel.app --view
```

**Metas Lighthouse**:
- Performance: > 80
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 80 (aunque no es critico)

---

## Mock con Prism

Ver `mock-flow.md` para instrucciones detalladas.

Resumen:
```bash
# Terminal 1: Mock server
npx @stoplight/prism-cli mock api-mock/openapi.yaml -p 4010 --dynamic

# Terminal 2: Frontend
cd web
npm run dev

# Acceder a http://localhost:5173
# El frontend apunta a VITE_API_URL=http://localhost:4010
```

---

## Deploy a Vercel

### Opcion 1: GitHub App (recomendado)

1. Conectar repo a Vercel
2. Configurar:
   - Framework: Vite
   - Root Directory: `web`
   - Build Command: `npm run build`
   - Output: `dist`
3. Variables de entorno:
   - `VITE_API_URL`: URL del API Gateway en AWS
4. Deploy automatico en cada push a `main`

### Opcion 2: CLI

```bash
cd web
vercel --prod
```

Ver `web/README.md` y skill `vercel-deploy/SKILL.md` para mas detalles.

---

## Checklist del Criterio 4

- [x] Frontend Vue 3 + TypeScript estricto
- [x] Form de queja funcional con validacion
- [x] Dashboard con metricas (graficos de Chart.js)
- [x] Chat con autoridades funcional (con RAG)
- [x] Estados: loading, error, empty, success
- [x] Responsive (mobile, tablet, desktop)
- [x] Accesibilidad: labels, aria-*, contraste, focus
- [x] Sin errores en consola
- [x] CSS con custom properties (sin Tailwind)
- [x] Composition API exclusivamente
- [x] Pinia solo para estado global
- [x] Code splitting por ruta
- [x] Mock con Prism funcional
- [x] Deployable en Vercel

---

## Referencias

- Codigo del frontend: `web/`
- OpenAPI spec: `api-mock/openapi.yaml`
- Mock flow: `mock-flow.md`
- Componentes: `componentes.md`
- Skills relevantes:
  - `vue3-architecture/SKILL.md`
  - `swagger-first/SKILL.md`
  - `frontend-streaming/SKILL.md`
  - `vercel-deploy/SKILL.md`
  - `unit-testing-patterns/SKILL.md`
