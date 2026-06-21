<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { RouterView, RouterLink, useRoute } from 'vue-router';
import { useNotificationStore } from '@/stores/notifications';
import { getSessionTenant } from '@/utils/tenant';
import { useTenantStore } from '@/stores/tenant';
import AppToast from '@/components/common/AppToast.vue';

const notifications = useNotificationStore();
const route = useRoute();
const tenantStore = useTenantStore();
const showTenantMenu = ref(false);

const navItems = [
  { name: 'Dashboard', to: '/dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { name: 'Reportar', to: '/queja', icon: 'M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z' },
  { name: 'Chat IA', to: '/chat', icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z' },
  { name: 'Inicio', to: '/', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
];

function selectTenant(tenantId: string) {
  if (tenantStore.tenantId === tenantId) {
    showTenantMenu.value = false;
    return;
  }
  tenantStore.selectTenant(tenantId);
  showTenantMenu.value = false;
  const t = tenantStore.current;
  notifications.success(`Tenant cambiado a: ${t.name}`);
  // NO recargar la página: el store es reactivo y el apiClient
  // lee el tenant actual en cada request desde sessionStorage.
  // Los componentes que tengan datos cacheados deben re-fetchearse
  // observando el cambio de tenant (ver watchers en cada view).
}

// Cerrar el menú al hacer click fuera
const sidebarRef = ref<HTMLElement | null>(null);
function onClickOutside(event: MouseEvent) {
  if (!showTenantMenu.value) return;
  const target = event.target as HTMLElement;
  if (sidebarRef.value && !sidebarRef.value.contains(target)) {
    showTenantMenu.value = false;
  }
}

onMounted(() => {
  // Inicializar store desde sessionStorage
  tenantStore.refresh();
  document.addEventListener('click', onClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside);
});
</script>

<template>
  <div class="min-h-screen bg-ink-50 flex">
    <!-- Sidebar -->
    <aside
      ref="sidebarRef"
      class="w-64 bg-white border-r border-ink-200 flex flex-col fixed inset-y-0 left-0 z-30"
    >
      <RouterLink to="/" class="flex items-center gap-2.5 px-5 h-16 border-b border-ink-200 hover:bg-ink-50">
        <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-600 to-brand-800 flex items-center justify-center shadow-soft">
          <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
        </div>
        <div>
          <div class="text-sm font-semibold text-ink-900 leading-tight">Sentinel</div>
          <div class="text-xs text-ink-500 leading-tight">AcademIA</div>
        </div>
      </RouterLink>

      <!-- Tenant selector -->
      <div class="px-3 pt-3">
        <button
          @click.stop="showTenantMenu = !showTenantMenu"
          class="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-ink-50 hover:bg-ink-100 transition-colors text-left"
        >
          <div class="flex items-center gap-2 min-w-0">
            <div class="w-7 h-7 rounded-md bg-brand-100 text-brand-700 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
              {{ tenantStore.current.tenantId.replace('demo-', '').toUpperCase() }}
            </div>
            <div class="min-w-0">
              <div class="text-xs font-medium text-ink-900 truncate">{{ tenantStore.current.name }}</div>
              <div class="text-[10px] text-ink-500 truncate">Tenant activo</div>
            </div>
          </div>
          <svg
            :class="['w-4 h-4 text-ink-400 flex-shrink-0 transition-transform', showTenantMenu ? 'rotate-180' : '']"
            fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7"/>
          </svg>
        </button>
        <div
          v-if="showTenantMenu"
          class="mt-1 bg-white border border-ink-200 rounded-lg shadow-lift overflow-hidden"
        >
          <button
            v-for="t in tenantStore.available"
            :key="t.tenantId"
            @click="selectTenant(t.tenantId)"
            :class="[
              'w-full text-left px-3 py-2 hover:bg-ink-50 text-xs flex items-center gap-2 transition-colors',
              t.tenantId === tenantStore.tenantId ? 'bg-brand-50 text-brand-700 font-medium' : 'text-ink-700'
            ]"
          >
            <span
              :class="[
                'w-5 h-5 rounded text-[9px] font-bold flex items-center justify-center flex-shrink-0',
                t.tenantId === tenantStore.tenantId ? 'bg-brand-200 text-brand-800' : 'bg-ink-100 text-ink-600'
              ]"
            >{{ t.tenantId.replace('demo-', '').toUpperCase() }}</span>
            <span class="truncate">{{ t.name }}</span>
            <svg
              v-if="t.tenantId === tenantStore.tenantId"
              class="w-3.5 h-3.5 ml-auto text-brand-600 flex-shrink-0"
              fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-4 space-y-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{ 'sidebar-link-active': route.path === item.to || (item.to !== '/' && route.path.startsWith(item.to)) }"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" :d="item.icon" />
          </svg>
          <span>{{ item.name }}</span>
        </RouterLink>
      </nav>

      <!-- Footer user -->
      <div class="p-3 border-t border-ink-200">
        <div class="flex items-center gap-2.5 px-2 py-2">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center text-xs font-bold">
            AR
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium text-ink-900 truncate">Aracely Ayala</div>
            <div class="text-xs text-ink-500 truncate">Bienestar Estudiantil</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 ml-64 min-h-screen">
      <RouterView />
    </main>

    <!-- Toasts -->
    <div class="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      <div class="pointer-events-auto">
        <AppToast
          v-for="toast in notifications.toasts"
          :key="toast.id"
          :message="toast.message"
          :type="toast.type"
          @close="notifications.dismiss(toast.id)"
        />
      </div>
    </div>
  </div>
</template>
