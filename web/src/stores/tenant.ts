import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import {
  detectTenantFromEmail,
  getSessionTenant,
  setSessionTenant,
  listAvailableTenants,
  type TenantInfo,
} from '@/utils/tenant';

const SESSION_KEY = 'sentinel.tenant';

export const useTenantStore = defineStore('tenant', () => {
  // Estado reactivo global del tenant activo
  const current = ref<TenantInfo>(getSessionTenant());
  const available = ref(listAvailableTenants());

  const tenantId = computed(() => current.value.tenantId);
  const tenantName = computed(() => current.value.name);

  function setTenant(tenant: TenantInfo) {
    current.value = tenant;
    setSessionTenant(tenant);
    // Emitir un evento custom para que componentes que no usan Pinia se enteren
    window.dispatchEvent(new CustomEvent('sentinel:tenant-changed', { detail: tenant }));
  }

  function selectTenant(tenantId: string) {
    const t = available.value.find((x) => x.tenantId === tenantId);
    if (t) {
      setTenant({ ...t, source: 'session' });
    }
  }

  function detectFromEmail(email: string | null | undefined) {
    if (!email) return null;
    const t = detectTenantFromEmail(email);
    if (t) setTenant(t);
    return t;
  }

  function refresh() {
    current.value = getSessionTenant();
  }

  return {
    current,
    available,
    tenantId,
    tenantName,
    setTenant,
    selectTenant,
    detectFromEmail,
    refresh,
  };
});
