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
const isWarn = computed(() => props.maxlength ? charCount.value > props.maxlength * 0.9 : false);

function onInput(event: Event) {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <div class="w-full">
    <label v-if="label" :for="inputId" class="block text-sm font-medium text-ink-800 mb-1.5">
      {{ label }}
      <span v-if="required" class="text-danger-500 ml-0.5" aria-hidden="true">*</span>
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
      :class="[
        'w-full px-4 py-2.5 text-sm text-ink-900 placeholder:text-ink-400',
        'bg-white border rounded-lg shadow-soft',
        'transition-all duration-150',
        'focus:outline-none focus:ring-2 focus:ring-offset-0',
        'disabled:bg-ink-50 disabled:text-ink-500 disabled:cursor-not-allowed',
        error
          ? 'border-danger-400 focus:border-danger-500 focus:ring-danger-200'
          : 'border-ink-300 hover:border-ink-400 focus:border-brand-500 focus:ring-brand-100'
      ]"
      @input="onInput"
      @blur="emit('blur')"
    />
    <div v-if="hint || error || maxlength" class="flex items-start justify-between gap-2 mt-1.5 text-xs">
      <div class="flex-1 min-w-0">
        <p v-if="hint && !error" :id="hintId" class="text-ink-500">{{ hint }}</p>
        <p v-if="error" :id="errorId" class="text-danger-600 font-medium flex items-center gap-1" role="alert">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          {{ error }}
        </p>
      </div>
      <span
        v-if="maxlength"
        :class="[
          'tabular-nums font-medium flex-shrink-0',
          isWarn ? 'text-warning-600' : 'text-ink-400'
        ]"
      >
        {{ charCount }}/{{ maxlength }}
      </span>
    </div>
  </div>
</template>
