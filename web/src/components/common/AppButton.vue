<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'success';
  size?: 'sm' | 'md' | 'lg';
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
  loading?: boolean;
  block?: boolean;
  ariaLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  block: false,
});

const emit = defineEmits<{
  click: [event: MouseEvent];
}>();

const variantClass = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-brand-600 text-white shadow-soft hover:bg-brand-700 hover:shadow-lift focus:ring-brand-500';
    case 'secondary':
      return 'bg-white text-ink-700 border border-ink-300 hover:bg-ink-50 hover:border-ink-400 focus:ring-brand-500';
    case 'danger':
      return 'bg-danger-500 text-white hover:bg-danger-700 focus:ring-danger-500';
    case 'ghost':
      return 'bg-transparent text-ink-600 hover:bg-ink-100 hover:text-ink-900 focus:ring-brand-500';
    case 'success':
      return 'bg-success-500 text-white hover:bg-success-700 focus:ring-success-500';
    default:
      return '';
  }
});

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-3 py-1.5 text-sm min-h-[32px]';
    case 'md':
      return 'px-4 py-2.5 text-sm min-h-[40px]';
    case 'lg':
      return 'px-6 py-3 text-base min-h-[48px]';
    default:
      return '';
  }
});

function onClick(event: MouseEvent) {
  if (!props.disabled && !props.loading) {
    emit('click', event);
  }
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading"
    :aria-label="ariaLabel"
    :class="[
      'inline-flex items-center justify-center gap-2',
      'font-medium rounded-lg whitespace-nowrap select-none',
      'transition-all duration-150',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variantClass,
      sizeClass,
      block ? 'w-full' : ''
    ]"
    @click="onClick"
  >
    <svg
      v-if="loading"
      class="animate-spin w-4 h-4 flex-shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    <slot />
  </button>
</template>
