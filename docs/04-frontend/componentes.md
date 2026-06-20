# Catalogo de Componentes Vue - Sentinel AcademIA

> Inventario de todos los componentes del frontend con sus props, emits, slots y uso.

---

## Componentes Common (Reutilizables)

### AppButton

Boton con variants y estados.

**Props**:
| Prop | Tipo | Default | Descripcion |
|---|---|---|---|
| `variant` | `'primary' \| 'secondary' \| 'danger' \| 'ghost'` | `'primary'` | Estilo visual |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Tamano |
| `type` | `'button' \| 'submit' \| 'reset'` | `'button'` | Tipo HTML |
| `disabled` | `boolean` | `false` | Deshabilitado |
| `loading` | `boolean` | `false` | Estado de carga (muestra spinner) |
| `block` | `boolean` | `false` | Ancho completo |
| `ariaLabel` | `string` | - | Label para accesibilidad |

**Emits**: `click` (sin payload)

**Slots**: default (contenido del boton)

**Uso**:
```vue
<AppButton variant="primary" @click="onSubmit">Enviar queja</AppButton>
<AppButton variant="danger" :loading="submitting">Eliminar</AppButton>
```

---

### AppInput

Input de texto con label, validacion y mensaje de error.

**Props**:
| Prop | Tipo | Default | Descripcion |
|---|---|---|---|
| `modelValue` | `string` | `''` | Valor (v-model) |
| `label` | `string` | - | Label del campo |
| `type` | `string` | `'text'` | Tipo HTML |
| `placeholder` | `string` | - | Placeholder |
| `required` | `boolean` | `false` | Requerido |
| `disabled` | `boolean` | `false` | Deshabilitado |
| `error` | `string` | - | Mensaje de error |
| `hint` | `string` | - | Texto de ayuda |
| `maxlength` | `number` | - | Max caracteres |

**Emits**: `update:modelValue` (v-model)

**Uso**:
```vue
<AppInput v-model="titulo" label="Titulo" :maxlength="120" required />
```

---

### AppTextarea

Textarea con contador de caracteres.

**Props**: similar a `AppInput` + `rows: number`

**Uso**:
```vue
<AppTextarea
  v-model="descripcion"
  label="Descripcion"
  :rows="5"
  :maxlength="5000"
  required
/>
```

---

### AppSelect

Select con opciones.

**Props**:
| Prop | Tipo | Default | Descripcion |
|---|---|---|---|
| `modelValue` | `string` | `''` | Valor seleccionado |
| `options` | `Array<{value, label}>` | `[]` | Opciones |
| `label` | `string` | - | Label |
| `placeholder` | `string` | - | Placeholder |

**Uso**:
```vue
<AppSelect
  v-model="categoria"
  :options="[
    { value: 'ACADEMICA', label: 'Academica' },
    { value: 'INFRAESTRUCTURA', label: 'Infraestructura' },
    { value: 'ACOSO', label: 'Acoso' },
  ]"
  label="Categoria"
/>
```

---

### AppCard

Contenedor con header, body y footer opcionales.

**Slots**:
- `header`: titulo del card
- `default`: contenido
- `footer`: acciones

**Uso**:
```vue
<AppCard>
  <template #header>Queja #1234</template>
  <p>Descripcion de la queja...</p>
  <template #footer>
    <AppButton size="sm">Ver detalle</AppButton>
  </template>
</AppCard>
```

---

### AppSpinner

Indicador de carga.

**Props**:
| Prop | Tipo | Default | Descripcion |
|---|---|---|---|
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Tamano |
| `color` | `string` | `'var(--color-primary)'` | Color |

---

### AppToast

Notificacion flotante (exito/error/info).

**Props**:
| Prop | Tipo | Default | Descripcion |
|---|---|---|---|
| `message` | `string` | - | Mensaje |
| `type` | `'success' \| 'error' \| 'info' \| 'warning'` | `'info'` | Tipo |
| `duration` | `number` | `5000` | Duracion en ms |

**Uso**:
```vue
<AppToast :message="error" type="error" @close="error = ''" />
```

---

### AppBadge

Etiqueta pequena con color.

**Props**:
| Prop | Tipo | Default | Descripcion |
|---|---|---|---|
| `variant` | `'primary' \| 'success' \| 'warning' \| 'danger' \| 'neutral'` | `'neutral'` | Color |
| `size` | `'sm' \| 'md'` | `'sm'` | Tamano |

---

### AppEmpty

Estado vacio con icono, titulo y descripcion.

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `icon` | `string` | Nombre del icono |
| `title` | `string` | Titulo |
| `description` | `string` | Descripcion |

**Slots**: `action` (boton opcional)

---

## Componentes Domain (Negocio)

### QuejaForm

Formulario completo para crear una queja.

**Props**: ninguno (self-contained)

**Emits**: `submit: CreateQuejaInput`, `cancel`

**Uso**:
```vue
<QuejaForm @submit="onCreate" @cancel="goBack" />
```

**Caracteristicas**:
- Validacion local con Zod
- Contador de caracteres
- Select de categoria
- Checkbox de anonima
- Estados: idle, submitting, error
- Accesibilidad: labels, aria-describedby, focus management

---

### QuejaCard

Tarjeta que muestra una queja individual.

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `queja` | `Queja` | Datos de la queja |

**Emits**: `click` (id)

**Caracteristicas**:
- Muestra titulo, categoria, criticidad (badge)
- Preview del analisis si existe
- Indicador de archivos adjuntos
- Tiempo relativo ("hace 2 horas")

---

### QuejaList

Lista paginada de quejas con filtros.

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `quejas` | `QuejaListItem[]` | Lista |
| `loading` | `boolean` | Estado de carga |

**Emits**: `select: id`, `filter: QuejaFilters`

**Caracteristicas**:
- Filtros por categoria y criticidad
- Paginacion con "cargar mas"
- Empty state si no hay quejas
- Skeleton loaders

---

### AnalysisBadge

Badge que muestra el resultado del analisis LLM.

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `analysis` | `Analisis` | Resultado del analisis |

**Sub-componentes**: CriticidadIndicator, Badge

**Caracteristicas**:
- Color segun criticidad
- Icono segun categoria
- Tooltip con justificacion

---

### CriticidadIndicator

Indicador visual de criticidad (color + texto).

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `criticidad` | `'BAJA' \| 'MEDIA' \| 'ALTA' \| 'CRITICA'` | Nivel |
| `size` | `'sm' \| 'md' \| 'lg'` | Tamano |

**Colores**:
- `BAJA`: verde
- `MEDIA`: amarillo
- `ALTA`: naranja
- `CRITICA`: rojo

---

### DashboardChart

Grafico de Chart.js envuelto en Vue.

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `type` | `'line' \| 'bar' \| 'doughnut' \| 'pie'` | Tipo de grafico |
| `data` | `ChartData` | Datos |
| `options` | `ChartOptions` | Opciones |

**Uso**:
```vue
<DashboardChart type="doughnut" :data="distribucionCategorias" />
```

---

### DashboardMetricCard

Tarjeta con un KPI grande.

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `title` | `string` | Titulo del KPI |
| `value` | `number \| string` | Valor |
| `trend` | `number` | Variacion (opcional) |
| `icon` | `string` | Icono |
| `color` | `string` | Color del icono |

---

### ChatMessage

Mensaje individual del chat (user o assistant).

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `message` | `ChatMessage` | Mensaje con role, content, sources |

**Caracteristicas**:
- Avatar segun rol
- Markdown rendering (assistant)
- Citaciones colapsables
- Timestamp
- Indicador de "escribiendo..." cuando streaming

---

### ChatInput

Input para enviar mensajes al chat.

**Props**:
| Prop | Tipo | Descripcion |
|---|---|---|
| `disabled` | `boolean` | Deshabilitado |
| `placeholder` | `string` | Placeholder |

**Emits**: `send: string`

**Caracteristicas**:
- Textarea que crece con el contenido
- Enter para enviar, Shift+Enter para nueva linea
- Contador de caracteres
- Boton de enviar

---

## Composables

### useQuejas

Encapsula la logica de gestion de quejas.

**API**:
```typescript
const {
  quejas,              // Ref<QuejaListItem[]>
  quejaActual,         // Ref<Queja | null>
  loading,             // Ref<boolean>
  error,               // Ref<string | null>
  fetchQuejas,         // (filters?) => Promise<void>
  fetchQueja,          // (id) => Promise<void>
  crearQueja,          // (input) => Promise<QuejaAccepted>
  fetchAnalysis,       // (id) => Promise<Analisis>
  escalarQueja,        // (id, motivo) => Promise<Queja>
} = useQuejas();
```

### useChat

Encapsula la logica del chat.

**API**:
```typescript
const {
  messages,            // Ref<ChatMessageUI[]>
  loading,             // Ref<boolean>
  error,               // Ref<string | null>
  sendMessage,         // (text) => Promise<void>
  clearHistory,        // () => void
} = useChat();
```

### useToast

Wrapper del store de notifications.

**API**:
```typescript
const toast = useToast();
toast.success('Operacion exitosa');
toast.error('Algo salio mal');
toast.info('Informacion util');
toast.warning('Cuidado');
```

---

## Stores (Pinia)

### useAuthStore

```typescript
const auth = useAuthStore();
auth.user             // Ref<User | null>
auth.isAuthenticated  // ComputedRef<boolean>
auth.login(user)      // (User) => void
auth.logout()         // () => void
```

### useNotificationStore

```typescript
const notifications = useNotificationStore();
notifications.toasts          // Ref<Toast[]>
notifications.show(toast)    // (Toast) => void
notifications.dismiss(id)    // (id) => void
```

---

## Convenciones de naming

| Tipo | Convencion | Ejemplo |
|---|---|---|
| Componentes | PascalCase, prefijo `App` para comunes | `AppButton.vue`, `QuejaForm.vue` |
| Composables | camelCase, prefijo `use` | `useQuejas.ts`, `useChat.ts` |
| Services | camelCase, sufijo `Service` | `quejaService.ts` |
| Stores | camelCase, prefijo `use...Store` | `useAuthStore()` |
| Tipos | PascalCase | `CreateQuejaInput`, `Queja` |
| Props (componentes comunes) | nombre descriptivo | `variant`, `size`, `loading` |
| Events | pasado + nombre | `submit`, `click`, `select` |

---

## Anti-patrones (NO hacer)

- Componentes de mas de 200 lineas
- Logica de negocio en componentes (mover a composables)
- Estado local con Pinia (usar ref)
- Fetch directo en componentes (usar services)
- Inline styles (excepto dinamicos justificados)
- TypeScript `any`
- Sin props tipadas
- Sin emits tipados
- Sin accesibilidad basica (labels, aria, focus)
