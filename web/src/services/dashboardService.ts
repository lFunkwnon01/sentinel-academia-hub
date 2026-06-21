import { apiClient } from './apiClient';
import type { DashboardMetrics, QuejaListItem, QuejaListResponse } from '@/types/api';

export const dashboardService = {
  async getMetrics(rango: 7 | 30 | 90 = 30): Promise<DashboardMetrics> {
    const { data } = await apiClient.get<DashboardMetrics>('/api/dashboard/metrics', {
      params: { rango },
    });
    return data;
  },

  async getRecentQuejas(limit = 100, filters?: {
    categoria?: string;
    criticidad?: string;
    status?: string;
  }): Promise<QuejaListResponse> {
    const { data } = await apiClient.get<QuejaListResponse>('/api/quejas', {
      params: { limit, ...filters },
    });
    return data;
  },
};
