<script setup lang="ts">
import { RouterLink } from 'vue-router';
import AppButton from '@/components/common/AppButton.vue';
</script>

<template>
  <div class="not-found">
    <div class="not-found__content">
      <div class="not-found__code">404</div>
      <h1>Página no encontrada</h1>
      <p>La página que buscas no existe o fue movida.</p>
      <RouterLink to="/">
        <AppButton variant="primary">Volver al inicio</AppButton>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.not-found__code {
  font-size: 120px;
  font-weight: var(--font-bold);
  color: var(--color-primary);
  line-height: 1;
  margin-bottom: var(--space-4);
}

.not-found h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--space-2);
}

.not-found p {
  color: var(--color-text-muted);
  margin-bottom: var(--space-6);
}
</style>
