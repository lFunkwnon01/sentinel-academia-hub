import { ref } from 'vue';
import { quejaService } from '@/services/quejaService';
import type {
  Queja,
  QuejaListItem,
  QuejaListResponse,
  CreateQuejaInput,
  QuejaAccepted,
  Analisis,
  QuejaFilters,
} from '@/types/api';

export function useQuejas() {
  const quejas = ref<QuejaListItem[]>([]);
  const quejaActual = ref<Queja | null>(null);
  const analisis = ref<Analisis | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchQuejas(filters?: QuejaFilters): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const response: QuejaListResponse = await quejaService.list(filters);
      quejas.value = response.items;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar quejas';
    } finally {
      loading.value = false;
    }
  }

  async function fetchQueja(id: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      quejaActual.value = await quejaService.getById(id);
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar queja';
    } finally {
      loading.value = false;
    }
  }

  async function fetchAnalysis(id: string): Promise<Analisis | null> {
    loading.value = true;
    error.value = null;
    try {
      analisis.value = await quejaService.getAnalysis(id);
      return analisis.value;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar analisis';
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function crearQueja(input: CreateQuejaInput): Promise<QuejaAccepted | null> {
    loading.value = true;
    error.value = null;
    try {
      return await quejaService.create(input);
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al crear queja';
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function escalarQueja(id: string, motivo: string): Promise<Queja | null> {
    loading.value = true;
    error.value = null;
    try {
      const result = await quejaService.escalate(id, motivo);
      quejaActual.value = result;
      return result;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al escalar queja';
      return null;
    } finally {
      loading.value = false;
    }
  }

  function clearError(): void {
    error.value = null;
  }

  return {
    quejas,
    quejaActual,
    analisis,
    loading,
    error,
    fetchQuejas,
    fetchQueja,
    fetchAnalysis,
    crearQueja,
    escalarQueja,
    clearError,
  };
}
