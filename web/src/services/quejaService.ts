import { apiClient } from './apiClient';
import type {
  CreateQuejaInput,
  QuejaAccepted,
  Queja,
  QuejaListResponse,
  Analisis,
  QuejaFilters,
} from '@/types/api';

export const quejaService = {
  async create(input: CreateQuejaInput): Promise<QuejaAccepted> {
    const { data } = await apiClient.post<QuejaAccepted>('/api/quejas', input);
    return data;
  },

  async getById(id: string): Promise<Queja> {
    const { data } = await apiClient.get<Queja>(`/api/quejas/${id}`);
    return data;
  },

  async list(filters?: QuejaFilters): Promise<QuejaListResponse> {
    const { data } = await apiClient.get<QuejaListResponse>('/api/quejas', {
      params: filters,
    });
    return data;
  },

  async getAnalysis(id: string): Promise<Analisis> {
    const { data } = await apiClient.get<Analisis>(`/api/quejas/${id}/analysis`);
    return data;
  },

  async escalate(id: string, motivo: string): Promise<Queja> {
    const { data } = await apiClient.post<Queja>(`/api/quejas/${id}/escalate`, {
      motivo,
    });
    return data;
  },
};
