<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { dashboardService } from '@/services/dashboardService';
import { useNotificationStore } from '@/stores/notifications';
import type { DashboardMetrics } from '@/types/api';

const notifications = useNotificationStore();
const metrics = ref<DashboardMetrics | null>(null);
const loading = ref(false);
const rango = ref<7 | 30 | 90>(30);

const criticidadConfig: Record<string, { label: string; cls: string }> = {
  BAJA:  { label: 'Baja',  cls: 'badge-low' },
  MEDIA: { label: 'Media', cls: 'badge-medium' },
  ALTA:  { label: 'Alta',  cls: 'badge-high' },
  CRITICA: { label: 'Cr\'itica', cls: 'badge-critical' },
};

const totalCategorias = computed(() => {
  if (!metrics.value) return 0;
  return Object.values(metrics.value.distribucionPorCategoria).reduce((a, b) => a + b, 0);
});

async function fetchMetrics() {
  loading.value = true;
  try {
    metrics.value = await dashboardService.getMetrics(rango.value);
  } catch (e) {
    notifications.error(e instanceof Error ? e.message : 'Error al cargar m\'etricas');
  } finally {
    loading.value = false;
  }
}

onMounted(fetchMetrics);
</script>

<template>
  <div class="p-8 max-w-7xl mx-auto">
    <!-- Header -->
    <header class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-ink-900 tracking-tight">Dashboard</h1>
        <p class="mt-1 text-sm text-ink-500">M\'etricas y an\'alisis de quejas en tiempo real</p>
      </div>
      <div class="flex items-center gap-1 p-1 bg-ink-100 rounded-lg">
        <button
          v-for="r in [7, 30, 90] as const"
          :key="r"
          @click="rango = r; fetchMetrics()"
          :class="[
            'px-3.5 py-1.5 text-sm font-medium rounded-md transition-all',
            rango === r ? 'bg-white text-ink-900 shadow-soft' : 'text-ink-600 hover:text-ink-900'
          ]"
        >
          {{ r }} d\'ias
        </button>
      </div>
    </header>

    <!-- Loading state -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="card p-5 h-24 animate-pulse">
        <div class="h-3 bg-ink-200 rounded w-1/3 mb-3"></div>
        <div class="h-7 bg-ink-200 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Stats grid -->
    <div v-else-if="metrics" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat-card">
          <div class="flex items-center justify-between">
            <span class="stat-label">Total quejas</span>
            <div class="w-8 h-8 rounded-md bg-brand-50 text-brand-600 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
            </div>
          </div>
          <div class="stat-value mt-3">{{ metrics.resumen.totalQuejas }}</div>
        </div>

        <div class="stat-card">
          <div class="flex items-center justify-between">
            <span class="stat-label">Cr\'iticas</span>
            <div class="w-8 h-8 rounded-md bg-danger-50 text-danger-600 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
            </div>
          </div>
          <div class="stat-value mt-3 text-danger-700">{{ metrics.resumen.quejasCriticas }}</div>
        </div>

        <div class="stat-card">
          <div class="flex items-center justify-between">
            <span class="stat-label">Pendientes</span>
            <div class="w-8 h-8 rounded-md bg-warning-50 text-warning-600 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
          </div>
          <div class="stat-value mt-3 text-warning-700">{{ metrics.resumen.quejasPendientes }}</div>
        </div>

        <div class="stat-card">
          <div class="flex items-center justify-between">
            <span class="stat-label">Prioridad promedio</span>
            <div class="w-8 h-8 rounded-md bg-success-50 text-success-700 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
              </svg>
            </div>
          </div>
          <div class="stat-value mt-3">{{ metrics.resumen.prioridadPromedio }}<span class="text-base text-ink-400 ml-1">/10</span></div>
        </div>
      </div>

      <!-- Distributions row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- By categoria -->
        <div class="card p-6">
          <h3 class="font-semibold text-ink-900 mb-4">Por categor\'ia</h3>
          <div v-if="totalCategorias === 0" class="text-sm text-ink-500">Aun no hay datos</div>
          <div v-else class="space-y-2">
            <div v-for="(count, cat) in metrics.distribucionPorCategoria" :key="cat" class="flex items-center gap-3">
              <div class="text-sm font-medium text-ink-700 w-32 truncate">{{ cat }}</div>
              <div class="flex-1 h-2 bg-ink-100 rounded-full overflow-hidden">
                <div class="h-full bg-brand-500 rounded-full" :style="{ width: (count / totalCategorias * 100) + '%' }"></div>
              </div>
              <div class="text-sm font-semibold text-ink-900 w-8 text-right">{{ count }}</div>
            </div>
          </div>
        </div>

        <!-- By criticidad -->
        <div class="card p-6">
          <h3 class="font-semibold text-ink-900 mb-4">Por criticidad</h3>
          <div v-if="Object.keys(metrics.distribucionPorCriticidad).length === 0" class="text-sm text-ink-500">Aun no hay datos</div>
          <div v-else class="grid grid-cols-2 gap-3">
            <div v-for="(count, crit) in metrics.distribucionPorCriticidad" :key="crit" class="border border-ink-200 rounded-lg p-4">
              <span :class="['badge', criticidadConfig[crit]?.cls || 'badge-ink']">
                {{ criticidadConfig[crit]?.label || crit }}
              </span>
              <div class="mt-2 text-2xl font-semibold text-ink-900">{{ count }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top row -->
      <div v-if="metrics.topSedes.length || metrics.topFacultades.length" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div v-if="metrics.topSedes.length" class="card p-6">
          <h3 class="font-semibold text-ink-900 mb-4">Top sedes</h3>
          <div class="space-y-2">
            <div v-for="(item, i) in metrics.topSedes" :key="item.sede" class="flex items-center justify-between py-2 border-b border-ink-100 last:border-0">
              <div class="flex items-center gap-3">
                <span class="w-6 h-6 rounded-full bg-ink-100 text-ink-600 flex items-center justify-center text-xs font-bold">{{ i + 1 }}</span>
                <span class="text-sm font-medium text-ink-900">{{ item.sede }}</span>
              </div>
              <span class="badge badge-ink">{{ item.count }}</span>
            </div>
          </div>
        </div>

        <div v-if="metrics.topFacultades.length" class="card p-6">
          <h3 class="font-semibold text-ink-900 mb-4">Top facultades</h3>
          <div class="space-y-2">
            <div v-for="(item, i) in metrics.topFacultades" :key="item.facultad" class="flex items-center justify-between py-2 border-b border-ink-100 last:border-0">
              <div class="flex items-center gap-3">
                <span class="w-6 h-6 rounded-full bg-ink-100 text-ink-600 flex items-center justify-center text-xs font-bold">{{ i + 1 }}</span>
                <span class="text-sm font-medium text-ink-900">{{ item.facultad }}</span>
              </div>
              <span class="badge badge-ink">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="card p-12 text-center">
      <div class="text-ink-400 mb-3">No hay datos en este rango</div>
      <RouterLink to="/queja" class="btn-primary inline-flex">Crear primera queja</RouterLink>
    </div>
  </div>
</template>
