import { apiClient } from './apiClient';
import type { DashboardMetrics } from '@/types/api';

export const dashboardService = {
  async getMetrics(rango: 7 | 30 | 90 = 30): Promise<DashboardMetrics> {
    const { data } = await apiClient.get<DashboardMetrics>('/api/dashboard/metrics', {
      params: { rango },
    });
    return data;
  },
};
