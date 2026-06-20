// Tipos del dominio - inferidos del OpenAPI spec
// Para regenerar: npx openapi-typescript api-mock/openapi.yaml -o src/types/api.ts

export type Categoria =
  | 'ACADEMICA'
  | 'INFRAESTRUCTURA'
  | 'ACOSO'
  | 'ADMINISTRATIVA'
  | 'SALUD'
  | 'OTRA';

export type Criticidad = 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA';

export type Sentimiento = 'POSITIVO' | 'NEUTRO' | 'NEGATIVO' | 'NEGATIVO_FUERTE';

export type QuejaStatus =
  | 'PENDIENTE'
  | 'EN_COLA'
  | 'PROCESANDO'
  | 'ANALIZADA'
  | 'NOTIFICADA'
  | 'ERROR';

export interface CreateQuejaInput {
  titulo: string;
  descripcion: string;
  categoriaDeclarada: Categoria;
  adjuntos?: string[];
  anonima?: boolean;
  sede?: string;
  facultad?: string;
  contactoEmail?: string;
  contactoTelefono?: string;
  cursoCodigo?: string;
}

export interface QuejaAccepted {
  quejaId: string;
  status: QuejaStatus;
  correlationId: string;
  createdAt: string;
  estimatedAnalysisTime?: number;
}

export interface Analisis {
  categoria: Categoria;
  subcategoria?: string;
  criticidad: Criticidad;
  criticidadJustificacion?: string;
  sentimiento: Sentimiento;
  entidades?: Array<{ tipo: string; texto: string }>;
  temasClave?: string[];
  accionSugerida: string;
  prioridad: number;
  requiereNotificacionInmediata?: boolean;
  modeloUsado?: string;
  tokensConsumidos?: number;
  latenciaMs?: number;
  confidence?: number;
  generatedAt?: string;
}

export interface Queja {
  quejaId: string;
  titulo: string;
  descripcion: string;
  categoriaDeclarada: Categoria;
  status: QuejaStatus;
  userId?: string;
  createdAt: string;
  updatedAt?: string;
  analysis?: Analisis;
  adjuntos?: string[];
  sede?: string;
  facultad?: string;
  anonima?: boolean;
  escalada?: boolean;
  escalaAt?: string;
}

export interface QuejaListItem {
  quejaId: string;
  titulo: string;
  categoria: Categoria;
  criticidad?: Criticidad;
  status: QuejaStatus;
  createdAt: string;
  prioridad?: number;
}

export interface QuejaListResponse {
  items: QuejaListItem[];
  total: number;
  nextCursor?: string | null;
}

export interface DashboardResumen {
  totalQuejas: number;
  quejasCriticas: number;
  quejasPendientes: number;
  tiempoPromedioResolucion: number;
}

export interface DashboardMetrics {
  resumen: DashboardResumen;
  distribucionPorCategoria: Record<string, number>;
  distribucionPorCriticidad: Record<Criticidad, number>;
  tendenciaDiaria: Array<{ fecha: string; total: number; criticas: number }>;
  topSedes: Array<{ sede: string; count: number }>;
  topFacultades: Array<{ facultad: string; count: number }>;
  rangoDias: number;
}

export interface ChatRequest {
  question: string;
  context?: 'REGLAMENTO' | 'QUEJAS' | 'TODOS';
  conversationId?: string;
}

export interface ChatSource {
  id?: string;
  title?: string;
  source?: string;
  content: string;
  score?: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  conversationId: string;
  modeloUsado: string;
  tokensUsados: number;
  latenciaMs: number;
}

export interface ApiError {
  code: string;
  message: string;
  correlationId: string;
  details?: Record<string, unknown>;
  timestamp?: string;
}

export interface QuejaFilters {
  status?: QuejaStatus;
  criticidad?: Criticidad;
  limit?: number;
  cursor?: string;
}

// UI-specific types
export interface ChatMessageUI {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: ChatSource[];
  complete: boolean;
  correlationId?: string;
  timestamp: string;
}

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}
