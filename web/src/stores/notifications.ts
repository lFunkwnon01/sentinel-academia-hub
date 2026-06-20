import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Toast } from '@/types/api';

export const useNotificationStore = defineStore('notifications', () => {
  const toasts = ref<Toast[]>([]);

  function show(toast: Omit<Toast, 'id'>): string {
    const id = crypto.randomUUID();
    const fullToast: Toast = { id, ...toast };
    toasts.value.push(fullToast);

    if (toast.duration !== 0) {
      setTimeout(() => dismiss(id), toast.duration ?? 5000);
    }
    return id;
  }

  function dismiss(id: string): void {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  function clear(): void {
    toasts.value = [];
  }

  const success = (message: string, duration?: number) =>
    show({ message, type: 'success', duration });
  const error = (message: string, duration?: number) =>
    show({ message, type: 'error', duration });
  const info = (message: string, duration?: number) =>
    show({ message, type: 'info', duration });
  const warning = (message: string, duration?: number) =>
    show({ message, type: 'warning', duration });

  return { toasts, show, dismiss, clear, success, error, info, warning };
});
