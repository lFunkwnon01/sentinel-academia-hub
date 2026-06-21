<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { z } from 'zod';
import AppButton from '@/components/common/AppButton.vue';
import AppInput from '@/components/common/AppInput.vue';
import AppTextarea from '@/components/common/AppTextarea.vue';
import AppSelect from '@/components/common/AppSelect.vue';
import type { CreateQuejaInput, Categoria } from '@/types/api';
import { detectTenantFromEmail, setSessionTenant } from '@/utils/tenant';
import { useNotificationStore } from '@/stores/notifications';

const notifications = useNotificationStore();

const Schema = z.object({
  titulo: z.string().min(5, 'Mínimo 5 caracteres').max(120, 'Máximo 120 caracteres'),
  descripcion: z.string().min(20, 'Mínimo 20 caracteres').max(5000, 'Máximo 5000 caracteres'),
  categoriaDeclarada: z.enum(['ACADEMICA', 'INFRAESTRUCTURA', 'ACOSO', 'ADMINISTRATIVA', 'SALUD', 'OTRA']),
  sede: z.string().max(100).optional().or(z.literal('')),
  facultad: z.string().max(100).optional().or(z.literal('')),
  anonima: z.boolean(),
  contactoEmail: z.string().email('Email inválido').optional().or(z.literal('')),
  cursoCodigo: z.string().max(20).optional().or(z.literal('')),
});

type FormData = z.infer<typeof Schema>;

const form = ref<FormData>({
  titulo: '',
  descripcion: '',
  categoriaDeclarada: 'OTRA',
  sede: '',
  facultad: '',
  anonima: false,
  contactoEmail: '',
  cursoCodigo: '',
});

// Categorías: solo ACADEMICA, ACOSO, ADMINISTRATIVA y SALUD requieren email
const EMAIL_REQUIRED_CATEGORIES: Categoria[] = ['ACADEMICA', 'ACOSO', 'ADMINISTRATIVA', 'SALUD'];
const requiresEmail = computed(() => EMAIL_REQUIRED_CATEGORIES.includes(form.value.categoriaDeclarada));
const requiresCursoCodigo = computed(() => form.value.categoriaDeclarada === 'ACADEMICA');

watch(
  () => form.value.categoriaDeclarada,
  () => {
    if (requiresEmail.value && form.value.anonima) {
      form.value.anonima = false;
    }
  }
);

const isValid = computed(() => {
  let valid =
    form.value.titulo.length >= 5 &&
    form.value.descripcion.length >= 20 &&
    !!form.value.categoriaDeclarada;
  if (requiresEmail.value) {
    valid = valid && !!form.value.contactoEmail;
  }
  if (requiresCursoCodigo.value) {
    valid = valid && !!form.value.cursoCodigo;
  }
  return valid;
});

const errors = ref<Partial<Record<keyof FormData, string>>>({});
const submitting = ref(false);

interface CategoriaOption {
  value: Categoria;
  label: string;
  description: string;
  icon: string;
  gradient: string;
  ring: string;
}

const categorias: CategoriaOption[] = [
  {
    value: 'ACADEMICA',
    label: 'Académica',
    description: 'Notas, cursos, profesores, evaluaciones',
    icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    gradient: 'from-brand-500 to-brand-700',
    ring: 'ring-brand-500',
  },
  {
    value: 'INFRAESTRUCTURA',
    label: 'Infraestructura',
    description: 'Aulas, baños, equipos, instalaciones',
    icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
    gradient: 'from-amber-500 to-amber-700',
    ring: 'ring-amber-500',
  },
  {
    value: 'ACOSO',
    label: 'Acoso',
    description: 'Bullying, hostigamiento, discriminación',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    gradient: 'from-danger-500 to-danger-700',
    ring: 'ring-danger-500',
  },
  {
    value: 'ADMINISTRATIVA',
    label: 'Administrativa',
    description: 'Trámites, servicios, atención al estudiante',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    gradient: 'from-purple-500 to-purple-700',
    ring: 'ring-purple-500',
  },
  {
    value: 'SALUD',
    label: 'Salud',
    description: 'Bienestar físico, mental, accesibilidad',
    icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    gradient: 'from-pink-500 to-pink-700',
    ring: 'ring-pink-500',
  },
  {
    value: 'OTRA',
    label: 'Otra',
    description: 'Sugerencias u otros temas',
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    gradient: 'from-ink-500 to-ink-700',
    ring: 'ring-ink-500',
  },
];

const emit = defineEmits<{
  submit: [input: CreateQuejaInput];
  cancel: [];
}>();

const detectedTenant = ref<ReturnType<typeof detectTenantFromEmail>>(null);

watch(
  () => form.value.contactoEmail,
  (email) => {
    if (!email) {
      detectedTenant.value = null;
      return;
    }
    const tenant = detectTenantFromEmail(email);
    if (tenant) {
      detectedTenant.value = tenant;
      setSessionTenant(tenant);
      notifications.info(`Universidad detectada: ${tenant.name}`);
    } else {
      detectedTenant.value = null;
    }
  }
);

function validateField(field: keyof FormData) {
  try {
    const fieldSchema = (Schema.shape as any)[field];
    if (fieldSchema) {
      fieldSchema.parse(form.value[field]);
      errors.value[field] = undefined;
    }
  } catch (e) {
    if (e instanceof z.ZodError) {
      errors.value[field] = e.errors[0]?.message;
    }
  }
}

async function onSubmit() {
  const result = Schema.safeParse(form.value);
  if (!result.success) {
    for (const issue of result.error.issues) {
      const path = issue.path[0] as keyof FormData;
      errors.value[path] = issue.message;
    }
    return;
  }

  if (requiresEmail.value && result.data.anonima) {
    errors.value.anonima = `Las quejas de tipo ${form.value.categoriaDeclarada} no pueden ser anónimas`;
    return;
  }
  if (requiresEmail.value && !result.data.contactoEmail) {
    errors.value.contactoEmail = 'El email es obligatorio para esta categoría';
    return;
  }
  if (requiresCursoCodigo.value && !result.data.cursoCodigo) {
    errors.value.cursoCodigo = 'El código del curso es obligatorio para quejas ACADÉMICA';
    return;
  }

  submitting.value = true;
  try {
    const data: CreateQuejaInput = {
      titulo: result.data.titulo,
      descripcion: result.data.descripcion,
      categoriaDeclarada: result.data.categoriaDeclarada,
      anonima: result.data.anonima,
      ...(result.data.sede && { sede: result.data.sede }),
      ...(result.data.facultad && { facultad: result.data.facultad }),
      ...(!result.data.anonima && result.data.contactoEmail && { contactoEmail: result.data.contactoEmail }),
      ...(result.data.cursoCodigo && { cursoCodigo: result.data.cursoCodigo }),
    };
    emit('submit', data);
  } finally {
    submitting.value = false;
  }
}

function selectCategoria(cat: Categoria) {
  form.value.categoriaDeclarada = cat;
  errors.value.categoriaDeclarada = undefined;
}
</script>

<template>
  <form class="max-w-3xl mx-auto" @submit.prevent="onSubmit" novalidate>
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-soft">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
          </svg>
        </div>
        <div>
          <h1 class="text-2xl font-semibold text-ink-900 tracking-tight">Reportar una Queja</h1>
          <p class="text-sm text-ink-500">Tu reporte será analizado por IA y asignado a la autoridad correcta en menos de 30 segundos.</p>
        </div>
      </div>
    </div>

    <!-- Privacy banner -->
    <div class="mb-6 flex items-start gap-3 p-4 rounded-xl bg-brand-50 border border-brand-100">
      <svg class="w-5 h-5 text-brand-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
      </svg>
      <div class="text-sm text-ink-700">
        <strong class="text-ink-900">Información 100% confidencial.</strong>
        Solo la autoridad competente verá tu reporte. Los datos están protegidos y encriptados.
      </div>
    </div>

    <!-- Tenant detected banner -->
    <div
      v-if="detectedTenant"
      class="mb-6 flex items-start gap-3 p-4 rounded-xl bg-success-50 border border-success-500/20"
      role="status"
    >
      <div class="w-9 h-9 rounded-lg bg-success-500 text-white flex items-center justify-center flex-shrink-0 text-sm font-bold">
        {{ detectedTenant.tenantId.replace('demo-', '').toUpperCase() }}
      </div>
      <div class="text-sm">
        <strong class="text-ink-900 block">{{ detectedTenant.name }}</strong>
        <span class="text-ink-600">Universidad detectada desde tu email. Las notificaciones se enviarán al bienestar de esta institución.</span>
      </div>
    </div>

    <!-- Form card -->
    <div class="card p-6 sm:p-8 space-y-7">

      <!-- Título -->
      <div>
        <AppInput
          v-model="form.titulo"
          label="Título de la queja"
          placeholder="Ej: Falla en aire acondicionado del salón B-301"
          :required="true"
          :maxlength="120"
          :error="errors.titulo"
          @blur="validateField('titulo')"
        />
      </div>

      <!-- Descripción -->
      <div>
        <AppTextarea
          v-model="form.descripcion"
          label="Descripción detallada"
          placeholder="Describe la situación con el mayor detalle posible. Incluye fechas, lugares y personas involucradas si aplica."
          :required="true"
          :rows="6"
          :maxlength="5000"
          :error="errors.descripcion"
          hint="Mínimo 20 caracteres. Sé específico: ayuda a la IA a clasificar correctamente."
          @blur="validateField('descripcion')"
        />
      </div>

      <!-- Categoría con cards -->
      <div>
        <label class="block text-sm font-medium text-ink-800 mb-2">
          Categoría
          <span class="text-danger-500 ml-0.5">*</span>
        </label>
        <p class="text-xs text-ink-500 mb-3">Selecciona la categoría que mejor describe tu reporte. La IA puede ajustarla después del análisis.</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <button
            v-for="cat in categorias"
            :key="cat.value"
            type="button"
            @click="selectCategoria(cat.value)"
            :class="[
              'group relative p-3 rounded-xl border-2 text-left transition-all duration-150',
              'hover:shadow-soft focus:outline-none focus:ring-2 focus:ring-offset-1',
              form.categoriaDeclarada === cat.value
                ? `border-brand-500 bg-brand-50 ring-2 ${cat.ring} ring-offset-1`
                : 'border-ink-200 bg-white hover:border-ink-300'
            ]"
          >
            <div :class="['w-9 h-9 rounded-lg bg-gradient-to-br flex items-center justify-center mb-2 shadow-soft', cat.gradient]">
              <svg class="w-4.5 h-4.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" :d="cat.icon" />
              </svg>
            </div>
            <div class="text-sm font-semibold text-ink-900">{{ cat.label }}</div>
            <div class="text-xs text-ink-500 mt-0.5 leading-tight">{{ cat.description }}</div>
            <div
              v-if="form.categoriaDeclarada === cat.value"
              class="absolute top-2 right-2 w-5 h-5 rounded-full bg-brand-500 text-white flex items-center justify-center"
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
          </button>
        </div>
        <p v-if="errors.categoriaDeclarada" class="mt-1.5 text-xs text-danger-600 font-medium">{{ errors.categoriaDeclarada }}</p>
      </div>

      <!-- Curso (condicional para ACADEMICA) -->
      <div v-if="requiresCursoCodigo" class="p-4 rounded-xl bg-brand-50 border border-brand-100 space-y-3">
        <div class="flex items-start gap-2">
          <svg class="w-4 h-4 text-brand-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.97 7.97 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/>
          </svg>
          <p class="text-xs text-ink-700">
            <strong class="text-ink-900">Requerido para categoría Académica:</strong> indica el código del curso afectado.
          </p>
        </div>
        <AppInput
          v-model="form.cursoCodigo"
          label="Código del curso"
          placeholder="Ej: CS101, MAT202, FIS301"
          :required="true"
          :maxlength="20"
          :error="errors.cursoCodigo"
        />
      </div>

      <!-- Sede y Facultad -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <AppInput
          v-model="form.sede"
          label="Sede (opcional)"
          placeholder="Ej: Sede Norte"
          :maxlength="100"
        />
        <AppInput
          v-model="form.facultad"
          label="Facultad (opcional)"
          placeholder="Ej: Ingeniería"
          :maxlength="100"
        />
      </div>

      <!-- Anonimato (toggle switch) -->
      <div class="p-4 rounded-xl bg-ink-50 border border-ink-200">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">
            <svg class="w-5 h-5 text-ink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <label class="flex items-center justify-between gap-3 cursor-pointer">
              <div class="flex-1">
                <div class="text-sm font-medium text-ink-900">Reportar de forma anónima</div>
                <div class="text-xs text-ink-500 mt-0.5">
                  <span v-if="requiresEmail">
                    No disponible para esta categoría. Se requiere email para dar seguimiento.
                  </span>
                  <span v-else>
                    Tu identidad no se compartirá con la autoridad. Las quejas anónimas se procesan cuando se acumulan 10 similares.
                  </span>
                </div>
              </div>
              <button
                type="button"
                role="switch"
                :aria-checked="form.anonima"
                :disabled="requiresEmail"
                @click="form.anonima = !form.anonima"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors duration-200 ease-in-out',
                  'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  form.anonima ? 'bg-brand-600' : 'bg-ink-300'
                ]"
              >
                <span
                  :class="[
                    'inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition duration-200 ease-in-out',
                    form.anonima ? 'translate-x-6' : 'translate-x-1'
                  ]"
                />
              </button>
            </label>
            <p v-if="errors.anonima" class="mt-1.5 text-xs text-danger-600 font-medium">{{ errors.anonima }}</p>
          </div>
        </div>
      </div>

      <!-- Email (siempre visible, requerido condicionalmente) -->
      <div v-if="!form.anonima">
        <AppInput
          v-model="form.contactoEmail"
          :label="requiresEmail ? 'Email de contacto (obligatorio)' : 'Email de contacto (opcional)'"
          type="email"
          placeholder="tu-email@universidad.edu"
          :required="requiresEmail"
          :error="errors.contactoEmail"
          :hint="requiresEmail ? 'Necesario para que bienestar pueda darte seguimiento.' : 'Si lo proporcionas, podrás recibir seguimiento del caso.'"
          autocomplete="email"
        />
      </div>
    </div>

    <!-- Botones de acción -->
    <div class="mt-8 flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-end gap-3">
      <AppButton variant="ghost" type="button" @click="emit('cancel')">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
        </svg>
        Cancelar
      </AppButton>
      <AppButton
        type="submit"
        variant="primary"
        size="lg"
        :loading="submitting"
        :disabled="!isValid"
      >
        <template v-if="!submitting">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
          Enviar reporte
        </template>
        <template v-else>
          Enviando...
        </template>
      </AppButton>
    </div>
  </form>
</template>
