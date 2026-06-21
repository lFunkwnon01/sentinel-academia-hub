<script setup lang="ts">
import { computed } from 'vue';
import type { Criticidad } from '@/types/api';

interface Props {
  criticidad: Criticidad;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showLabel: true,
});

const labels: Record<Criticidad, string> = {
  BAJA: 'Baja',
  MEDIA: 'Media',
  ALTA: 'Alta',
  CRITICA: 'Crítica',
};

const styles = computed(() => {
  const map: Record<Criticidad, { bg: string; color: string; border: string }> = {
    BAJA: { bg: 'var(--color-crit-low-bg)', color: 'var(--color-crit-low)', border: 'var(--color-crit-low)' },
    MEDIA: { bg: 'var(--color-crit-medium-bg)', color: 'var(--color-crit-medium)', border: 'var(--color-crit-medium)' },
    ALTA: { bg: 'var(--color-crit-high-bg)', color: 'var(--color-crit-high)', border: 'var(--color-crit-high)' },
    CRITICA: { bg: 'var(--color-crit-critical-bg)', color: 'var(--color-crit-critical)', border: 'var(--color-crit-critical)' },
  };
  return map[props.criticidad];
});
</script>

<template>
  <span
    :class="['criticidad-indicator', `criticidad-indicator--${size}`, criticidad === 'CRITICA' && 'criticidad-indicator--pulse']"
    :style="{
      backgroundColor: styles.bg,
      color: styles.color,
      borderColor: styles.border,
    }"
    :aria-label="`Criticidad: ${labels[criticidad]}`"
    role="status"
  >
    <span class="criticidad-indicator__dot" :style="{ backgroundColor: styles.color }" aria-hidden="true" />
    <span v-if="showLabel" class="criticidad-indicator__label">{{ labels[criticidad] }}</span>
  </span>
</template>

<style scoped>
.criticidad-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border: 1px solid;
  border-radius: var(--radius-full);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  white-space: nowrap;
}

.criticidad-indicator--sm {
  font-size: var(--text-xs);
  padding: 2px var(--space-2);
}

.criticidad-indicator--md {
  font-size: var(--text-xs);
}

.criticidad-indicator--lg {
  font-size: var(--text-sm);
  padding: var(--space-2) var(--space-4);
}

.criticidad-indicator__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.criticidad-indicator--pulse .criticidad-indicator__dot {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
</style>
