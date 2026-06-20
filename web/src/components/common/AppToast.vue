<script setup lang="ts">
import { useNotificationStore } from '@/stores/notifications';

interface Props {
  message: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

withDefaults(defineProps<Props>(), {
  type: 'info',
  duration: 5000,
});

const emit = defineEmits<{
  close: [];
}>();

const notifications = useNotificationStore();

function close() {
  emit('close');
}
</script>

<template>
  <div :class="['app-toast', `app-toast--${type}`]" role="alert" aria-live="polite">
    <div class="app-toast__icon" :aria-hidden="true">
      <svg v-if="type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <svg v-else-if="type === 'error'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <svg v-else-if="type === 'warning'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke-linejoin="round" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="16" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12.01" y2="8" />
      </svg>
    </div>
    <div class="app-toast__message">{{ message }}</div>
    <button type="button" class="app-toast__close" aria-label="Cerrar notificacion" @click="close">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.app-toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--color-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 280px;
  max-width: 420px;
  font-size: var(--text-sm);
}

.app-toast--success {
  border-left-color: var(--color-success);
}

.app-toast--success .app-toast__icon {
  color: var(--color-success);
}

.app-toast--error {
  border-left-color: var(--color-danger);
}

.app-toast--error .app-toast__icon {
  color: var(--color-danger);
}

.app-toast--warning {
  border-left-color: var(--color-warning);
}

.app-toast--warning .app-toast__icon {
  color: var(--color-warning);
}

.app-toast--info .app-toast__icon {
  color: var(--color-info);
}

.app-toast__icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.app-toast__message {
  flex: 1;
  color: var(--color-text);
}

.app-toast__close {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  color: var(--color-text-muted);
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.app-toast__close:hover {
  color: var(--color-text);
  background: var(--color-bg-muted);
}

.app-toast__close svg {
  width: 16px;
  height: 16px;
}
</style>
