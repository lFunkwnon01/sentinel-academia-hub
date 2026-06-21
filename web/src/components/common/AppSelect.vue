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
  hint?: string;
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
const hintId = computed(() => `${inputId}-hint`);
const describedBy = computed(() => {
  const ids: string[] = [];
  if (props.hint) ids.push(hintId.value);
  if (props.error) ids.push(errorId.value);
  return ids.length > 0 ? ids.join(' ') : undefined;
});

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <div class="w-full">
    <label v-if="label" :for="inputId" class="block text-sm font-medium text-ink-800 mb-1.5">
      {{ label }}
      <span v-if="required" class="text-danger-500 ml-0.5" aria-hidden="true">*</span>
    </label>
    <div class="relative">
      <select
        :id="inputId"
        :value="modelValue"
        :required="required"
        :disabled="disabled"
        :aria-invalid="!!error"
        :aria-describedby="describedBy"
        :class="[
          'w-full pl-4 pr-10 py-2.5 text-sm text-ink-900',
          'bg-white border rounded-lg shadow-soft',
          'transition-all duration-150 appearance-none cursor-pointer',
          'focus:outline-none focus:ring-2 focus:ring-offset-0',
          'disabled:bg-ink-50 disabled:text-ink-500 disabled:cursor-not-allowed',
          error
            ? 'border-danger-400 focus:border-danger-500 focus:ring-danger-200'
            : 'border-ink-300 hover:border-ink-400 focus:border-brand-500 focus:ring-brand-100'
        ]"
        @change="onChange"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <svg
        class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-500"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        aria-hidden="true"
      >
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </div>
    <div v-if="hint || error" class="mt-1.5 text-xs">
      <p v-if="hint && !error" :id="hintId" class="text-ink-500">{{ hint }}</p>
      <p v-if="error" :id="errorId" class="text-danger-600 font-medium flex items-center gap-1" role="alert">
        <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
        </svg>
        {{ error }}
      </p>
    </div>
  </div>
</template>
