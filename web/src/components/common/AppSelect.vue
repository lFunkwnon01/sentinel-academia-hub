<script setup lang="ts">
import { useId, computed } from 'vue';

interface Option {
  value: string;
  label: string;
}

interface Props {
  modelValue: string;
  options: Option[];
  label?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
  disabled: false,
});

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const inputId = useId();
const errorId = computed(() => `${inputId}-error`);

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <div :class="['app-select', { 'app-select--error': error, 'app-select--disabled': disabled }]">
    <label v-if="label" :for="inputId" class="app-select__label">
      {{ label }}
      <span v-if="required" class="app-select__required" aria-hidden="true">*</span>
    </label>
    <div class="app-select__wrapper">
      <select
        :id="inputId"
        :value="modelValue"
        :required="required"
        :disabled="disabled"
        :aria-invalid="!!error"
        :aria-describedby="error ? errorId : undefined"
        class="app-select__field"
        @change="onChange"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <svg class="app-select__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </div>
    <span v-if="error" :id="errorId" class="app-select__error" role="alert">{{ error }}</span>
  </div>
</template>

<style scoped>
.app-select {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: 100%;
}

.app-select__label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.app-select__required {
  color: var(--color-danger);
  margin-left: var(--space-1);
}

.app-select__wrapper {
  position: relative;
}

.app-select__field {
  width: 100%;
  padding: var(--space-3) var(--space-10) var(--space-3) var(--space-4);
  font-size: var(--text-base);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  appearance: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 42px;
}

.app-select__field:hover:not(:disabled) {
  border-color: var(--color-border-strong);
}

.app-select__field:focus-visible {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.app-select--error .app-select__field {
  border-color: var(--color-danger);
}

.app-select--disabled .app-select__field {
  background: var(--color-bg-muted);
  cursor: not-allowed;
}

.app-select__chevron {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.app-select__error {
  color: var(--color-danger);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}
</style>
