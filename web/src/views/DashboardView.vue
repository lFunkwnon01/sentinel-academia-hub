<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { dashboardService } from '@/services/dashboardService';
import { useNotificationStore } from '@/stores/notifications';
import type { DashboardMetrics } from '@/types/api';

const notifications = useNotificationStore();
const metrics = ref<DashboardMetrics | null>(null);
const loading = ref(false);
const rango = ref<7 | 30 | 90>(30);

async function fetchMetrics() {
  loading.value = true;
  try {
    metrics.value = await dashboardService.getMetrics(rango.value);
  } catch (e) {
    notifications.error(e instanceof Error ? e.message : 'Error al cargar metricas');
  } finally {
    loading.value = false;
  }
}

onMounted(fetchMetrics);
</script>

<template>
  <div class="dashboard">
    <header class="dashboard__header">
      <h1>Dashboard Institucional</h1>
      <div class="dashboard__filters">
        <label>Rango:</label>
        <select v-model.number="rango" @change="fetchMetrics">
          <option :value="7">Ultimos 7 dias</option>
          <option :value="30">Ultimos 30 dias</option>
          <option :value="90">Ultimos 90 dias</option>
        </select>
      </div>
    </header>

    <div v-if="loading" class="dashboard__loading">Cargando metricas...</div>

    <template v-else-if="metrics">
      <section class="dashboard__resumen">
        <article class="dashboard__kpi">
          <div class="dashboard__kpi-icon" aria-hidden="true">📋</div>
          <div class="dashboard__kpi-value">{{ metrics.resumen.totalQuejas }}</div>
          <div class="dashboard__kpi-label">Total de quejas</div>
        </article>
        <article class="dashboard__kpi dashboard__kpi--critical">
          <div class="dashboard__kpi-icon" aria-hidden="true">🚨</div>
          <div class="dashboard__kpi-value">{{ metrics.resumen.quejasCriticas }}</div>
          <div class="dashboard__kpi-label">Casos criticos</div>
        </article>
        <article class="dashboard__kpi">
          <div class="dashboard__kpi-icon" aria-hidden="true">⏳</div>
          <div class="dashboard__kpi-value">{{ metrics.resumen.quejasPendientes }}</div>
          <div class="dashboard__kpi-label">Pendientes</div>
        </article>
        <article class="dashboard__kpi">
          <div class="dashboard__kpi-icon" aria-hidden="true">⏱️</div>
          <div class="dashboard__kpi-value">{{ metrics.resumen.tiempoPromedioResolucion }}h</div>
          <div class="dashboard__kpi-label">Resolucion promedio</div>
        </article>
      </section>

      <section class="dashboard__distribuciones">
        <article class="dashboard__card">
          <h3>Distribucion por Categoria</h3>
          <ul class="dashboard__list">
            <li v-for="(count, categoria) in metrics.distribucionPorCategoria" :key="categoria">
              <span class="dashboard__list-label">{{ categoria }}</span>
              <div class="dashboard__bar-wrapper">
                <div
                  class="dashboard__bar"
                  :style="{ width: `${(count / metrics.resumen.totalQuejas) * 100}%` }"
                />
                <span class="dashboard__bar-value">{{ count }}</span>
              </div>
            </li>
          </ul>
        </article>

        <article class="dashboard__card">
          <h3>Distribucion por Criticidad</h3>
          <ul class="dashboard__list">
            <li v-for="(count, crit) in metrics.distribucionPorCriticidad" :key="crit">
              <span class="dashboard__list-label">{{ crit }}</span>
              <div class="dashboard__bar-wrapper">
                <div
                  :class="['dashboard__bar', `dashboard__bar--${crit.toLowerCase()}`]"
                  :style="{ width: `${(count / metrics.resumen.totalQuejas) * 100}%` }"
                />
                <span class="dashboard__bar-value">{{ count }}</span>
              </div>
            </li>
          </ul>
        </article>
      </section>

      <section v-if="metrics.topSedes.length" class="dashboard__tops">
        <article class="dashboard__card">
          <h3>Top Sedes</h3>
          <ol class="dashboard__ranking">
            <li v-for="item in metrics.topSedes" :key="item.sede">
              <span class="dashboard__ranking-label">{{ item.sede }}</span>
              <span class="dashboard__ranking-count">{{ item.count }}</span>
            </li>
          </ol>
        </article>
        <article v-if="metrics.topFacultades.length" class="dashboard__card">
          <h3>Top Facultades</h3>
          <ol class="dashboard__ranking">
            <li v-for="item in metrics.topFacultades" :key="item.facultad">
              <span class="dashboard__ranking-label">{{ item.facultad }}</span>
              <span class="dashboard__ranking-count">{{ item.count }}</span>
            </li>
          </ol>
        </article>
      </section>
    </template>

    <div v-else class="dashboard__empty">
      No hay datos disponibles
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.dashboard__header h1 {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
}

.dashboard__filters {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.dashboard__filters select {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  font-size: var(--text-sm);
  cursor: pointer;
}

.dashboard__resumen {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
}

.dashboard__kpi {
  padding: var(--space-6);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.dashboard__kpi--critical {
  background: var(--color-crit-critical-bg);
  border-color: var(--color-crit-critical);
}

.dashboard__kpi--critical .dashboard__kpi-value {
  color: var(--color-crit-critical);
}

.dashboard__kpi-icon {
  font-size: 36px;
}

.dashboard__kpi-value {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.dashboard__kpi-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: center;
}

.dashboard__distribuciones,
.dashboard__tops {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: var(--space-4);
}

.dashboard__card {
  padding: var(--space-6);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.dashboard__card h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin-bottom: var(--space-4);
  color: var(--color-text);
}

.dashboard__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.dashboard__list li {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-sm);
}

.dashboard__list-label {
  min-width: 110px;
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.dashboard__bar-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 24px;
  background: var(--color-bg-muted);
  border-radius: var(--radius-sm);
  overflow: hidden;
  position: relative;
}

.dashboard__bar {
  height: 100%;
  background: var(--color-primary);
  transition: width var(--transition-base);
}

.dashboard__bar--baja { background: var(--color-crit-low); }
.dashboard__bar--media { background: var(--color-crit-medium); }
.dashboard__bar--alta { background: var(--color-crit-high); }
.dashboard__bar--critica { background: var(--color-crit-critical); }

.dashboard__bar-value {
  position: absolute;
  right: var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.dashboard__ranking {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  counter-reset: ranking;
}

.dashboard__ranking li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-muted);
  border-radius: var(--radius-sm);
  counter-increment: ranking;
}

.dashboard__ranking li::before {
  content: counter(ranking);
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: white;
  border-radius: 50%;
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  margin-right: var(--space-2);
}

.dashboard__ranking-label {
  flex: 1;
  color: var(--color-text);
  font-weight: var(--font-medium);
}

.dashboard__ranking-count {
  font-weight: var(--font-semibold);
  color: var(--color-primary);
}

.dashboard__loading,
.dashboard__empty {
  padding: var(--space-12);
  text-align: center;
  color: var(--color-text-muted);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
}
</style>
