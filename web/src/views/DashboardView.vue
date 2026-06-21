<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { dashboardService } from '@/services/dashboardService';
import { useNotificationStore } from '@/stores/notifications';
import type { DashboardMetrics, QuejaListItem } from '@/types/api';
import CriticidadIndicator from '@/components/domain/CriticidadIndicator.vue';

const notifications = useNotificationStore();
const metrics = ref<DashboardMetrics | null>(null);
const quejas = ref<QuejaListItem[]>([]);
const loading = ref(false);
const rango = ref<7 | 30 | 90>(30);

const filtroCategoria = ref<string>('');
const filtroCriticidad = ref<string>('');
const filtroStatus = ref<string>('');
const busqueda = ref<string>('');

const criticidadConfig: Record<string, { label: string; cls: string }> = {
  BAJA:  { label: 'Baja',  cls: 'badge-low' },
  MEDIA: { label: 'Media', cls: 'badge-medium' },
  ALTA:  { label: 'Alta',  cls: 'badge-high' },
  CRITICA: { label: 'Crítica', cls: 'badge-critical' },
};

const statusConfig: Record<string, { label: string; cls: string }> = {
  PENDIENTE:   { label: 'Pendiente',   cls: 'badge-warning' },
  EN_COLA:     { label: 'En cola',     cls: 'badge-ink' },
  PROCESANDO:  { label: 'Procesando',  cls: 'badge-info' },
  ANALIZADA:   { label: 'Analizada',   cls: 'badge-success' },
  NOTIFICADA:  { label: 'Notificada',  cls: 'badge-success' },
  ERROR:       { label: 'Error',       cls: 'badge-critical' },
};

const totalCategorias = computed(() => {
  if (!metrics.value) return 0;
  return Object.values(metrics.value.distribucionPorCategoria).reduce((a, b) => a + b, 0);
});

const filteredQuejas = computed(() => {
  let result = quejas.value;
  const q = busqueda.value.trim().toLowerCase();
  if (q) {
    result = result.filter(item =>
      item.titulo.toLowerCase().includes(q) ||
      item.quejaId.toLowerCase().includes(q)
    );
  }
  return result;
});

async function fetchAll() {
  loading.value = true;
  try {
    const [m, list] = await Promise.all([
      dashboardService.getMetrics(rango.value),
      dashboardService.getRecentQuejas(200, {
        ...(filtroCategoria.value && { categoria: filtroCategoria.value }),
        ...(filtroCriticidad.value && { criticidad: filtroCriticidad.value }),
        ...(filtroStatus.value && { status: filtroStatus.value }),
      }),
    ]);
    metrics.value = m;
    quejas.value = list.items;
  } catch (e) {
    notifications.error(e instanceof Error ? e.message : 'Error al cargar datos');
  } finally {
    loading.value = false;
  }
}

function formatDate(iso: string): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = (now.getTime() - d.getTime()) / 1000;
    if (diff < 60) return 'hace un momento';
    if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`;
    if (diff < 7 * 86400) return `hace ${Math.floor(diff / 86400)} d`;
    return d.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return iso.slice(0, 10);
  }
}

function critClass(crit?: string): string {
  if (!crit) return 'badge-ink';
  return criticidadConfig[crit]?.cls || 'badge-ink';
}

function critLabel(crit?: string): string {
  if (!crit) return 'Sin análisis';
  return criticidadConfig[crit]?.label || crit;
}

function statusLabel(s?: string): string {
  if (!s) return '—';
  return statusConfig[s]?.label || s;
}

function statusClass(s?: string): string {
  if (!s) return 'badge-ink';
  return statusConfig[s]?.cls || 'badge-ink';
}

onMounted(fetchAll);
</script>

<template>
  <div class="p-8 max-w-7xl mx-auto">
    <!-- Header -->
    <header class="flex flex-wrap items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-ink-900 tracking-tight">Dashboard</h1>
        <p class="mt-1 text-sm text-ink-500">Métricas y análisis de quejas en tiempo real</p>
      </div>
      <div class="flex items-center gap-1 p-1 bg-ink-100 rounded-lg">
        <button
          v-for="r in [7, 30, 90] as const"
          :key="r"
          @click="rango = r; fetchAll()"
          :class="[
            'px-3.5 py-1.5 text-sm font-medium rounded-md transition-all',
            rango === r ? 'bg-white text-ink-900 shadow-soft' : 'text-ink-600 hover:text-ink-900'
          ]"
        >
          {{ r }} días
        </button>
      </div>
    </header>

    <!-- Loading state -->
    <div v-if="loading && !metrics" class="grid grid-cols-1 md:grid-cols-4 gap-4">
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
            <span class="stat-label">Críticas</span>
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
        <div class="card p-6">
          <h3 class="font-semibold text-ink-900 mb-4">Por categoría</h3>
          <div v-if="totalCategorias === 0" class="text-sm text-ink-500">Aún no hay datos</div>
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

        <div class="card p-6">
          <h3 class="font-semibold text-ink-900 mb-4">Por criticidad</h3>
          <div v-if="Object.keys(metrics.distribucionPorCriticidad).length === 0" class="text-sm text-ink-500">Aún no hay datos</div>
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

      <!-- EVENTOS RECIENTES - lista de quejas -->
      <div class="card overflow-hidden">
        <div class="p-6 border-b border-ink-200">
          <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
            <div>
              <h3 class="font-semibold text-ink-900">Eventos recientes</h3>
              <p class="mt-1 text-xs text-ink-500">{{ filteredQuejas.length }} de {{ quejas.length }} quejas mostradas</p>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <input
                v-model="busqueda"
                type="text"
                placeholder="Buscar por título o ID…"
                class="input text-sm py-1.5 px-3 w-56"
              />
              <select v-model="filtroCategoria" @change="fetchAll" class="input text-sm py-1.5 px-3">
                <option value="">Todas las categorías</option>
                <option value="ACADEMICA">Académica</option>
                <option value="INFRAESTRUCTURA">Infraestructura</option>
                <option value="ACOSO">Acoso</option>
                <option value="ADMINISTRATIVA">Administrativa</option>
                <option value="SALUD">Salud</option>
                <option value="OTRA">Otra</option>
              </select>
              <select v-model="filtroCriticidad" @change="fetchAll" class="input text-sm py-1.5 px-3">
                <option value="">Toda criticidad</option>
                <option value="BAJA">Baja</option>
                <option value="MEDIA">Media</option>
                <option value="ALTA">Alta</option>
                <option value="CRITICA">Crítica</option>
              </select>
              <select v-model="filtroStatus" @change="fetchAll" class="input text-sm py-1.5 px-3">
                <option value="">Todos los estados</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="EN_COLA">En cola</option>
                <option value="PROCESANDO">Procesando</option>
                <option value="ANALIZADA">Analizada</option>
                <option value="NOTIFICADA">Notificada</option>
                <option value="ERROR">Error</option>
              </select>
              <button
                @click="filtroCategoria=''; filtroCriticidad=''; filtroStatus=''; busqueda=''; fetchAll()"
                class="btn-secondary text-sm py-1.5 px-3"
                :disabled="!filtroCategoria && !filtroCriticidad && !filtroStatus && !busqueda"
              >
                Limpiar
              </button>
            </div>
          </div>
        </div>

        <div v-if="loading" class="p-12 text-center text-ink-500">Cargando eventos…</div>
        <div v-else-if="filteredQuejas.length === 0" class="p-12 text-center">
          <div class="text-ink-400 mb-3">No se encontraron quejas con los filtros actuales</div>
          <button @click="filtroCategoria=''; filtroCriticidad=''; filtroStatus=''; busqueda=''; fetchAll()" class="btn-secondary">Limpiar filtros</button>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-xs font-semibold text-ink-500 uppercase tracking-wider border-b border-ink-200">
                <th class="px-6 py-3">ID</th>
                <th class="px-6 py-3">Título</th>
                <th class="px-6 py-3">Categoría</th>
                <th class="px-6 py-3">Criticidad</th>
                <th class="px-6 py-3">Estado</th>
                <th class="px-6 py-3">Prioridad</th>
                <th class="px-6 py-3">Fecha</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-ink-100">
              <tr v-for="item in filteredQuejas" :key="item.quejaId" class="hover:bg-ink-50 transition-colors">
                <td class="px-6 py-3 text-xs font-mono text-ink-500">
                  {{ item.quejaId.slice(0, 8) }}
                </td>
                <td class="px-6 py-3 text-sm text-ink-900 max-w-md truncate" :title="item.titulo">
                  {{ item.titulo }}
                </td>
                <td class="px-6 py-3 text-sm">
                  <span class="badge badge-ink">{{ item.categoria }}</span>
                </td>
                <td class="px-6 py-3 text-sm">
                  <span :class="['badge', critClass(item.criticidad)]">{{ critLabel(item.criticidad) }}</span>
                </td>
                <td class="px-6 py-3 text-sm">
                  <span :class="['badge', statusClass(item.status)]">{{ statusLabel(item.status) }}</span>
                </td>
                <td class="px-6 py-3 text-sm font-semibold text-ink-900">
                  {{ item.prioridad != null ? item.prioridad : '—' }}
                </td>
                <td class="px-6 py-3 text-xs text-ink-500">
                  {{ formatDate(item.createdAt) }}
                </td>
              </tr>
            </tbody>
          </table>
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
