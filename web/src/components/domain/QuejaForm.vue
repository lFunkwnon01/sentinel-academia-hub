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

// Categories where 1 queja is enough to act on -> email required, no anonymous
const EMAIL_REQUIRED_CATEGORIES: Categoria[] = ['ACADEMICA', 'ACOSO', 'ADMINISTRATIVA', 'SALUD'];
const requiresEmail = computed(() => EMAIL_REQUIRED_CATEGORIES.includes(form.value.categoriaDeclarada));
const requiresCursoCodigo = computed(() => form.value.categoriaDeclarada === 'ACADEMICA');

// If user switches to a category that requires email, force anonima off
watch(
  () => form.value.categoriaDeclarada,
  () => {
    if (requiresEmail.value && form.value.anonima) {
      form.value.anonima = false;
    }
  }
);

const isValid = computed(() => {
  let valid = form.value.titulo.length >= 5 &&
              form.value.descripcion.length >= 20 &&
              !!form.value.categoriaDeclarada;
  if (requiresEmail.value) {
    valid = valid && !!form.value.contactoEmail && form.value.contactoEmail.length > 0;
  }
  if (requiresCursoCodigo.value) {
    valid = valid && !!form.value.cursoCodigo && form.value.cursoCodigo.length > 0;
  }
  return valid;
});

const errors = ref<Partial<Record<keyof FormData, string>>>({});
const submitting = ref(false);

const categorias: Array<{ value: Categoria; label: string }> = [
  { value: 'ACADEMICA', label: 'Académica' },
  { value: 'INFRAESTRUCTURA', label: 'Infraestructura' },
  { value: 'ACOSO', label: 'Acoso' },
  { value: 'ADMINISTRATIVA', label: 'Administrativa' },
  { value: 'SALUD', label: 'Salud' },
  { value: 'OTRA', label: 'Otra' },
];

const emit = defineEmits<{
  submit: [input: CreateQuejaInput];
  cancel: [];
}>();

const detectedTenant = ref<ReturnType<typeof detectTenantFromEmail>>(null);

// Auto-detect tenant when email changes
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
  // Validar todos los campos
  const result = Schema.safeParse(form.value);
  if (!result.success) {
    for (const issue of result.error.issues) {
      const path = issue.path[0] as keyof FormData;
      errors.value[path] = issue.message;
    }
    return;
  }

  // Reglas de negocio: email obligatorio, anonima deshabilitada segun categoria
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
</script>

<template>
  <form class="queja-form" @submit.prevent="onSubmit">
    <h2 class="queja-form__title">Reportar una Queja</h2>
    <p class="queja-form__description">
      Tu reporte será analizado automáticamente por IA para asignar prioridad y categoría.
      Toda la información es confidencial.
    </p>

    <div v-if="detectedTenant" class="queja-form__tenant-badge" role="status">
      <span class="queja-form__tenant-icon" aria-hidden="true">🏛️</span>
      <div>
        <strong>{{ detectedTenant.name }}</strong>
        <p>Universidad detectada automáticamente desde el dominio de tu email. Las notificaciones se enviarán al bienestar de esta institución.</p>
      </div>
    </div>

    <AppInput
      v-model="form.titulo"
      label="Título de la queja"
      placeholder="Ej: Falla en aire acondicionado del salón B-301"
      :required="true"
      :maxlength="120"
      :error="errors.titulo"
      @blur="validateField('titulo')"
    />

    <AppTextarea
      v-model="form.descripcion"
      label="Descripción detallada"
      placeholder="Describe la situación con el mayor detalle posible..."
      :required="true"
      :rows="6"
      :maxlength="5000"
      :error="errors.descripcion"
      hint="Incluye fechas, personas involucradas (si aplica) y contexto relevante"
      @blur="validateField('descripcion')"
    />

    <AppSelect
      v-model="form.categoriaDeclarada"
      label="Categoría"
      :options="categorias"
      :required="true"
    />

    <div v-if="requiresCursoCodigo" class="queja-form__info">
      <AppInput
        v-model="form.cursoCodigo"
        label="Código del curso"
        placeholder="Ej: CS101, MAT202"
        :required="true"
        :maxlength="20"
        :error="errors.cursoCodigo"
        hint="Las quejas académicas requieren el código del curso afectado"
      />
    </div>

    <div v-if="requiresEmail" class="queja-form__info">
      <p class="queja-form__info-text">
        <strong>Esta categoría requiere email de contacto</strong> para poder darte seguimiento.
        Las quejas individuales se procesan de inmediato; no es posible enviarlas anónimas.
      </p>
    </div>

    <div class="queja-form__row">
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

    <label class="queja-form__checkbox" :class="{ 'queja-form__checkbox--disabled': requiresEmail }">
      <input
        v-model="form.anonima"
        type="checkbox"
        :disabled="requiresEmail"
      />
      <span>
        Reportar de forma anónima
        <small v-if="requiresEmail" class="queja-form__checkbox-hint">
          (no disponible para esta categoría)
        </small>
      </span>
    </label>

    <AppInput
      v-if="!form.anonima"
      v-model="form.contactoEmail"
      label="Email de contacto (opcional)"
      type="email"
      placeholder="tu-email@universidad.edu"
      :error="errors.contactoEmail"
      hint="Para recibir seguimiento de tu caso"
    />

    <div class="queja-form__actions">
      <AppButton variant="secondary" type="button" @click="emit('cancel')">
        Cancelar
      </AppButton>
      <AppButton
        type="submit"
        variant="primary"
        :loading="submitting"
        :disabled="!isValid"
      >
        Enviar reporte
      </AppButton>
    </div>
  </form>
</template>

<style scoped>
.queja-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  max-width: 640px;
  margin: 0 auto;
  padding: var(--space-6);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.queja-form__title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.queja-form__description {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.queja-form__tenant-badge {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-primary-light, #dbeafe);
  border: 1px solid var(--color-primary, #2563eb);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.queja-form__tenant-badge strong {
  display: block;
  color: var(--color-primary, #2563eb);
  margin-bottom: var(--space-1);
}

.queja-form__tenant-badge p {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  margin: 0;
  line-height: var(--leading-relaxed);
}

.queja-form__tenant-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.queja-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.queja-form__checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  user-select: none;
}

.queja-form__checkbox input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.queja-form__checkbox--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.queja-form__checkbox--disabled input[type='checkbox'] {
  cursor: not-allowed;
}

.queja-form__checkbox-hint {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  margin-left: var(--space-1);
}

.queja-form__info {
  padding: var(--space-3) var(--space-4);
  background: var(--color-primary-light, #dbeafe);
  border-left: 3px solid var(--color-primary, #2563eb);
  border-radius: var(--radius-md);
}

.queja-form__info-text {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text);
}

.queja-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

@media (max-width: 640px) {
  .queja-form__row {
    grid-template-columns: 1fr;
  }

  .queja-form__actions {
    flex-direction: column-reverse;
  }

  .queja-form__actions > * {
    width: 100%;
  }
}
</style>
