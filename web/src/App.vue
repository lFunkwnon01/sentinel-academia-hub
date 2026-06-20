<script setup lang="ts">
import { RouterView, RouterLink, useRoute } from 'vue-router';
import { computed, ref, onMounted, watch } from 'vue';
import { useNotificationStore } from '@/stores/notifications';
import { getSessionTenant, listAvailableTenants, setSessionTenant, type TenantInfo } from '@/utils/tenant';
import AppToast from '@/components/common/AppToast.vue';

const route = useRoute();
const notifications = useNotificationStore();

const isHome = computed(() => route.name === 'home');

const currentTenant = ref<TenantInfo>(getSessionTenant());
const availableTenants = listAvailableTenants();

function selectTenant(event: Event) {
  const target = event.target as HTMLSelectElement;
  const tenant = availableTenants.find((t) => t.tenantId === target.value);
  if (tenant) {
    currentTenant.value = { ...tenant, source: 'session' };
    setSessionTenant(currentTenant.value);
    notifications.info(`Universidad cambiada a ${tenant.name}. Recarga la pagina.`);
  }
}

onMounted(() => {
  currentTenant.value = getSessionTenant();
});
watch(
  () => route.fullPath,
  () => {
    currentTenant.value = getSessionTenant();
  }
);
</script>

<template>
  <div class="app">
    <header v-if="!isHome" class="app-header">
      <div class="app-header__container">
        <RouterLink to="/" class="app-header__logo">
          <span class="app-header__logo-icon">SA</span>
          <span class="app-header__logo-text">Sentinel AcademIA</span>
        </RouterLink>
        <nav class="app-header__nav">
          <label class="app-header__tenant" :title="`Tenant actual: ${currentTenant.tenantId}`">
            <span class="app-header__tenant-icon" aria-hidden="true">🏛️</span>
            <select :value="currentTenant.tenantId" @change="selectTenant" class="app-header__tenant-select">
              <option v-for="t in availableTenants" :key="t.tenantId" :value="t.tenantId">
                {{ t.name }}
              </option>
            </select>
          </label>
          <RouterLink to="/queja" class="app-header__link">Reportar</RouterLink>
          <RouterLink to="/dashboard" class="app-header__link">Dashboard</RouterLink>
          <RouterLink to="/chat" class="app-header__link">Chat IA</RouterLink>
        </nav>
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <footer class="app-footer">
      <p>Sentinel AcademIA &middot; Hackat&oacute;n 2025 &middot; Multi-nube AWS + OCI</p>
    </footer>

    <div class="app-toasts">
      <TransitionGroup name="toast">
        <AppToast
          v-for="toast in notifications.toasts"
          :key="toast.id"
          :message="toast.message"
          :type="toast.type"
          @close="notifications.dismiss(toast.id)"
        />
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-4) 0;
}

.app-header__container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
}

.app-header__logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
  color: var(--color-text);
  font-weight: var(--font-semibold);
}

.app-header__logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-primary);
  color: white;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
}

.app-header__nav {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.app-header__tenant {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
}

.app-header__tenant-icon {
  font-size: 14px;
}

.app-header__tenant-select {
  background: transparent;
  border: none;
  color: var(--color-text);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  cursor: pointer;
  outline: none;
  padding: 0 var(--space-1);
}

.app-header__tenant-select:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

.app-header__link {
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: var(--font-medium);
  transition: color var(--transition-fast);
}

.app-header__link:hover,
.app-header__link.router-link-active {
  color: var(--color-primary);
}

.app-main {
  flex: 1;
  padding: var(--space-8) var(--space-6);
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}

.app-footer {
  background: var(--color-bg-elevated);
  border-top: 1px solid var(--color-border);
  padding: var(--space-6);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.app-toasts {
  position: fixed;
  top: var(--space-6);
  right: var(--space-6);
  z-index: var(--z-toast);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  pointer-events: none;
}

.app-toasts > * {
  pointer-events: auto;
}

.toast-enter-active,
.toast-leave-active {
  transition: all var(--transition-base);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

@media (max-width: 640px) {
  .app-header__container {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .app-header__nav {
    gap: var(--space-4);
  }
}
</style>
