<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import QuejaForm from '@/components/domain/QuejaForm.vue';
import { quejaService } from '@/services/quejaService';
import { useNotificationStore } from '@/stores/notifications';
import type { CreateQuejaInput, QuejaAccepted } from '@/types/api';

const router = useRouter();
const notifications = useNotificationStore();
const submitting = ref(false);
const lastResult = ref<QuejaAccepted | null>(null);

async function onSubmit(input: CreateQuejaInput) {
  submitting.value = true;
  try {
    const result = await quejaService.create(input);
    lastResult.value = result;
    notifications.success(`Queja ${result.quejaId.slice(0, 8)} enviada. Será analizada en ~30 segundos.`);
  } catch (e) {
    notifications.error(e instanceof Error ? e.message : 'Error al enviar la queja');
  } finally {
    submitting.value = false;
  }
}

function onCancel() {
  router.push('/');
}

function verDashboard() {
  router.push('/dashboard');
}
</script>

<template>
  <div class="queja-view">
    <div v-if="lastResult" class="queja-view__success">
      <div class="queja-view__success-icon" aria-hidden="true">✅</div>
      <h2>Queja enviada exitosamente</h2>
      <p>
        Tu queja fue recibida con el ID
        <code class="queja-view__id">{{ lastResult.quejaId }}</code>
      </p>
      <p>
        El análisis automático se completará en aproximadamente
        <strong>{{ lastResult.estimatedAnalysisTime ?? 30 }} segundos</strong>.
        Si es un caso crítico, se notificará a bienestar inmediatamente.
      </p>
      <div class="queja-view__success-actions">
        <button class="queja-view__btn-secondary" @click="lastResult = null">
          Enviar otra queja
        </button>
        <button class="queja-view__btn-primary" @click="verDashboard">
          Ver dashboard
        </button>
      </div>
    </div>
    <QuejaForm v-else @submit="onSubmit" @cancel="onCancel" />
  </div>
</template>

<style scoped>
.queja-view {
  padding: var(--space-6) 0;
}

.queja-view__success {
  max-width: 640px;
  margin: 0 auto;
  padding: var(--space-12) var(--space-6);
  background: var(--color-bg);
  border: 1px solid var(--color-success);
  border-radius: var(--radius-lg);
  text-align: center;
  box-shadow: var(--shadow-md);
}

.queja-view__success-icon {
  font-size: 64px;
  margin-bottom: var(--space-4);
}

.queja-view__success h2 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin-bottom: var(--space-3);
}

.queja-view__success p {
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
  line-height: var(--leading-relaxed);
}

.queja-view__id {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-muted);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--color-text);
}

.queja-view__success-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: var(--space-6);
  flex-wrap: wrap;
}

.queja-view__btn-primary,
.queja-view__btn-secondary {
  padding: var(--space-2) var(--space-5);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 40px;
}

.queja-view__btn-primary {
  background: var(--color-primary);
  color: white;
  border: none;
}

.queja-view__btn-primary:hover {
  background: var(--color-primary-hover);
}

.queja-view__btn-secondary {
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.queja-view__btn-secondary:hover {
  background: var(--color-bg-muted);
}
</style>
