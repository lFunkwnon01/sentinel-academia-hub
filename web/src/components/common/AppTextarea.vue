<script setup lang="ts">
import { computed, useId } from 'vue';

interface Props {
  modelValue: string;
  label?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  error?: string;
  hint?: string;
  rows?: number;
  maxlength?: number;
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
  disabled: false,
  readonly: false,
  rows: 4,
});

const emit = defineEmits<{
  'update:modelValue': [value: string];
  blur: [];
}>();

const inputId = useId();
const errorId = computed(() => `${inputId}-error`);
const hintId = computed(() => `${inputId}-hint`);
const describedBy = computed(() => {
  const ids: string[] = [];
  if (props.hint) ids.push(hintId.value);
  if (props.error) ids.push(errorId.value);
  return ids.length > 0 ? ids.join(' ') : undefined;
});

const charCount = computed(() => props.modelValue?.length ?? 0);

function onInput(event: Event) {
  const target = event.target as HTMLTextAreaElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <div :class="['app-textarea', { 'app-textarea--error': error, 'app-textarea--disabled': disabled }]">
    <label v-if="label" :for="inputId" class="app-textarea__label">
      {{ label }}
      <span v-if="required" class="app-textarea__required" aria-hidden="true">*</span>
    </label>
    <textarea
      :id="inputId"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :readonly="readonly"
      :rows="rows"
      :maxlength="maxlength"
      :aria-invalid="!!error"
      :aria-describedby="describedBy"
      :aria-required="required"
      class="app-textarea__field"
      @input="onInput"
      @blur="emit('blur')"
    />
    <div v-if="hint || error || maxlength" class="app-textarea__meta">
      <span v-if="hint" :id="hintId" class="app-textarea__hint">{{ hint }}</span>
      <span v-if="error" :id="errorId" class="app-textarea__error" role="alert">{{ error }}</span>
      <span v-if="maxlength" class="app-textarea__count" :class="{ 'app-textarea__count--warn': charCount > maxlength * 0.9 }">
        {{ charCount }}/{{ maxlength }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.app-textarea {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: 100%;
}

.app-textarea__label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.app-textarea__required {
  color: var(--color-danger);
  margin-left: var(--space-1);
}

.app-textarea__field {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-base);
  font-family: var(--font-sans);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  resize: vertical;
  min-height: 80px;
  line-height: var(--leading-normal);
}

.app-textarea__field::placeholder {
  color: var(--color-text-subtle);
}

.app-textarea__field:hover:not(:disabled) {
  border-color: var(--color-border-strong);
}

.app-textarea__field:focus-visible {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.app-textarea--error .app-textarea__field {
  border-color: var(--color-danger);
}

.app-textarea--disabled .app-textarea__field {
  background: var(--color-bg-muted);
  cursor: not-allowed;
}

.app-textarea__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
}

.app-textarea__hint { color: var(--color-text-muted); }
.app-textarea__error { color: var(--color-danger); font-weight: var(--font-medium); }
.app-textarea__count { color: var(--color-text-muted); font-variant-numeric: tabular-nums; margin-left: auto; }
.app-textarea__count--warn { color: var(--color-warning); font-weight: var(--font-medium); }
</style>
