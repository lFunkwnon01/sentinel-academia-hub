<script setup lang="ts">
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
    :class="['app-button', `app-button--${variant}`, `app-button--${size}`, { 'app-button--block': block, 'app-button--loading': loading }]"
    @click="onClick"
  >
    <span v-if="loading" class="app-button__spinner" aria-hidden="true" />
    <span class="app-button__content">
      <slot />
    </span>
  </button>
</template>

<style scoped>
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-weight: var(--font-medium);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  white-space: nowrap;
  user-select: none;
  border: 1px solid transparent;
}

.app-button--block {
  width: 100%;
}

.app-button--sm {
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
  min-height: 32px;
}

.app-button--md {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-base);
  min-height: 40px;
}

.app-button--lg {
  padding: var(--space-3) var(--space-6);
  font-size: var(--text-lg);
  min-height: 48px;
}

.app-button--primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.app-button--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.app-button--secondary {
  background: var(--color-bg-elevated);
  color: var(--color-text);
  border-color: var(--color-border);
}

.app-button--secondary:hover:not(:disabled) {
  background: var(--color-bg-muted);
  border-color: var(--color-border-strong);
}

.app-button--danger {
  background: var(--color-danger);
  color: var(--color-text-inverse);
}

.app-button--danger:hover:not(:disabled) {
  background: var(--color-danger-hover);
}

.app-button--ghost {
  background: transparent;
  color: var(--color-text);
}

.app-button--ghost:hover:not(:disabled) {
  background: var(--color-bg-muted);
}

.app-button--success {
  background: var(--color-success);
  color: var(--color-text-inverse);
}

.app-button--success:hover:not(:disabled) {
  background: #059669;
}

.app-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.app-button__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.app-button--loading .app-button__content {
  opacity: 0.7;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
