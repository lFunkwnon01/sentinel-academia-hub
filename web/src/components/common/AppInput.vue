<script setup lang="ts">
import { computed, useId } from 'vue';

interface Props {
  modelValue: string;
  label?: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  error?: string;
  hint?: string;
  maxlength?: number;
  autocomplete?: string;
  ariaLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  required: false,
  disabled: false,
  readonly: false,
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
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <div :class="['app-input', { 'app-input--error': error, 'app-input--disabled': disabled }]">
    <label v-if="label" :for="inputId" class="app-input__label">
      {{ label }}
      <span v-if="required" class="app-input__required" aria-hidden="true">*</span>
    </label>
    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :readonly="readonly"
      :maxlength="maxlength"
      :autocomplete="autocomplete"
      :aria-label="ariaLabel ?? label"
      :aria-invalid="!!error"
      :aria-describedby="describedBy"
      :aria-required="required"
      class="app-input__field"
      @input="onInput"
      @blur="emit('blur')"
    />
    <div v-if="hint || error || maxlength" class="app-input__meta">
      <span v-if="hint" :id="hintId" class="app-input__hint">{{ hint }}</span>
      <span v-if="error" :id="errorId" class="app-input__error" role="alert">{{ error }}</span>
      <span v-if="maxlength" class="app-input__count" :class="{ 'app-input__count--warn': charCount > maxlength * 0.9 }">
        {{ charCount }}/{{ maxlength }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.app-input {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: 100%;
}

.app-input__label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.app-input__required {
  color: var(--color-danger);
  margin-left: var(--space-1);
}

.app-input__field {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-base);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  min-height: 42px;
}

.app-input__field::placeholder {
  color: var(--color-text-subtle);
}

.app-input__field:hover:not(:disabled) {
  border-color: var(--color-border-strong);
}

.app-input__field:focus-visible {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.app-input--error .app-input__field {
  border-color: var(--color-danger);
}

.app-input--error .app-input__field:focus-visible {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.app-input--disabled .app-input__field {
  background: var(--color-bg-muted);
  cursor: not-allowed;
}

.app-input__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
}

.app-input__hint {
  color: var(--color-text-muted);
}

.app-input__error {
  color: var(--color-danger);
  font-weight: var(--font-medium);
}

.app-input__count {
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
  margin-left: auto;
}

.app-input__count--warn {
  color: var(--color-warning);
  font-weight: var(--font-medium);
}
</style>
