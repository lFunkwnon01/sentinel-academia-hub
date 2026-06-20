import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { generateUUID } from '@/utils/uuid';
import { getSessionTenant } from '@/utils/tenant';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:4010';

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: agregar correlationId y X-Tenant-ID (de sessionStorage) a cada request
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  let correlationId = sessionStorage.getItem('correlationId');
  if (!correlationId) {
    correlationId = generateUUID();
    sessionStorage.setItem('correlationId', correlationId);
  }
  config.headers.set('x-correlation-id', correlationId);
  // Tenant viene de sessionStorage (configurado via login/email o setTenant())
  const tenant = getSessionTenant();
  config.headers.set('X-Tenant-ID', tenant.tenantId);
  return config;
});

// Interceptor: manejo uniforme de errores
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const data = error.response?.data;
    let message = 'Error desconocido';

    if (data?.message) {
      message = data.message;
    } else if (status === 429) {
      message = 'Demasiadas solicitudes. Intenta en unos minutos.';
    } else if (status === 404) {
      message = 'Recurso no encontrado.';
    } else if (status && status >= 500) {
      message = 'Error del servidor. Intenta de nuevo.';
    } else if (error.code === 'ECONNABORTED') {
      message = 'La solicitud tardo demasiado. Intenta de nuevo.';
    } else if (error.message === 'Network Error') {
      message = 'No se pudo conectar al servidor. Verifica tu conexion.';
    }

    return Promise.reject(new Error(message));
  }
);
