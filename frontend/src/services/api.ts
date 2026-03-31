<<<<<<< HEAD
import {
  ApiError,
  type NewInstanceRequest,
  type LabelRequest,
  type InferenceData,
  type CreateInstanceResponse,
  type NextInstancesResponse,
  type LabelInstanceResponse,
  type InstanceInfo,
  type InstancesListResponse,
  type InferenceResponse,
  type ConfigModelsResponse,
  type ConfigStrategiesResponse,
  type TicketsResponse,
  type TeamsResponse,
  type CategoriesResponse,
  type SubcategoriesResponse,
  type ExplainLimeResponse,
  type NearestTicketResponse,
  type ResolutionProcessRequest,
  type ResolutionProcessResponse,
  type ResolutionFeedbackRequest,
  type ResolutionFeedbackResponse,
  type EmbeddingsRebuildResponse,
  // Analytics types
  type AnalyticsOverview,
  type SessionSummary,
  type SessionLog,
  type LabelingMetrics,
  type ModelPerformanceMetrics,
  type ALEffectivenessMetrics,
  type ClassDistributionMetrics,
  type SessionComparison,
  type ExportRequest,
  type ExportResponse,
=======
import type {
  NewInstanceRequest,
  LabelRequest,
  InferenceData,
  CreateInstanceResponse,
  NextInstancesResponse,
  LabelInstanceResponse,
  InstanceInfo,
  InstancesListResponse,
  InferenceResponse,
  ApiResponse,
  ConfigModelsResponse,
  ConfigStrategiesResponse,
  ConfigCapabilitiesResponse,
  TicketsResponse,
  TeamsResponse,
  CategoriesResponse,
  SubcategoriesResponse,
  ExplainLimeResponse,
  NearestTicketResponse,
  XaiRequestResponse,
  XaiJobResponse,
  ResolutionProcessRequest,
  ResolutionProcessResponse,
  ResolutionFeedbackRequest,
  ResolutionFeedbackResponse
>>>>>>> 775514ca01a4df18b25f0b5ecbdea126e4b79bba
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Active Learning
  CREATE_INSTANCE: '/activelearning/new',
  GET_NEXT_INSTANCES: (id: number) => `/activelearning/${id}/next`,
  LABEL_INSTANCE: (id: number) => `/activelearning/${id}/label`,
  GET_INFO: (id: number) => `/activelearning/${id}/info`,
  SAVE_MODEL: (id: number) => `/activelearning/${id}/save`,
  GET_INSTANCES: '/activelearning/instances',
  DELETE_INSTANCE: (id: number) => `/activelearning/${id}`,

  // Inference
  INFER: (id: number) => `/activelearning/${id}/infer`,

  // XAI
  EXPLAIN_LIME: (id: number) => `/xai/${id}/explain_lime`,
  NEAREST_TICKET: (id: number) => `/xai/${id}/nearest_ticket`,
<<<<<<< HEAD

  // Config
  GET_MODELS: '/config/models',
  GET_QUERY_STRATEGIES: '/config/query-strategies',

  // Data
  GET_TICKETS: (id: number) => `/data/${id}/tickets`,
  GET_TEAMS: (id: number) => `/data/${id}/teams`,
  GET_CATEGORIES: (id: number) => `/data/${id}/categories`,
  GET_SUBCATEGORIES: (id: number) => `/data/${id}/subcategories`,

=======
  CREATE_XAI_REQUEST: (id: number) => `/xai/${id}/requests`,
  GET_XAI_JOB: (jobId: string) => `/xai/jobs/${jobId}`,
  
  // Config
  GET_MODELS: '/config/models',
  GET_QUERY_STRATEGIES: '/config/query-strategies',
  GET_CAPABILITIES: '/config/capabilities',
  
  // Data
  GET_TICKETS: '/data/tickets',
  GET_TEAMS: '/data/teams',
  GET_CATEGORIES: '/data/categories',
  GET_SUBCATEGORIES: '/data/subcategories',
  
>>>>>>> 775514ca01a4df18b25f0b5ecbdea126e4b79bba
  // Resolution
  RESOLUTION_PROCESS: '/resolution/process',
  RESOLUTION_FEEDBACK: '/resolution/feedback',
  RESOLUTION_REBUILD_EMBEDDINGS: '/resolution/rebuild-embeddings',

  // Analytics
  GET_ANALYTICS_OVERVIEW: '/analytics/overview',
  GET_SESSIONS: '/analytics/sessions',
  GET_SESSION: (sessionId: string) => `/analytics/sessions/${sessionId}`,
  GET_SESSION_DECISIONS: (sessionId: string) => `/analytics/sessions/${sessionId}/decisions`,
  GET_SESSION_LABELING: (sessionId: string) => `/analytics/sessions/${sessionId}/labeling`,
  GET_SESSION_PERFORMANCE: (sessionId: string) => `/analytics/sessions/${sessionId}/performance`,
  GET_SESSION_EFFECTIVENESS: (sessionId: string) => `/analytics/sessions/${sessionId}/effectiveness`,
  GET_SESSION_DISTRIBUTION: (sessionId: string) => `/analytics/sessions/${sessionId}/distribution`,
  GET_SESSION_EXPORT: (sessionId: string) => `/analytics/sessions/${sessionId}/export`,
  COMPARE_SESSIONS: '/analytics/compare',
  EXPORT_SESSIONS: '/analytics/export-bulk',
} as const;

/**
 * Generic API call function that throws ApiError on failure.
 * Designed to work with Vue Query - throws errors instead of returning error objects.
 */
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
  } catch (error) {
    // Network error (no connection, CORS, etc.)
    throw new ApiError(0, error instanceof Error ? error.message : 'Network error');
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    // Response is not valid JSON
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }
    // If response was ok but not JSON, return empty object
    return {} as T;
  }

  if (!response.ok) {
    const detail = (data as { detail?: string })?.detail || response.statusText;
    throw new ApiError(response.status, detail);
  }

  return data as T;
}

// API service functions - all throw ApiError on failure
export const apiService = {
  // Active Learning
  createInstance: (data: NewInstanceRequest) =>
    apiCall<CreateInstanceResponse>(API_ENDPOINTS.CREATE_INSTANCE, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getNextInstances: (id: number, batchSize: number = 1) =>
    apiCall<NextInstancesResponse>(`${API_ENDPOINTS.GET_NEXT_INSTANCES(id)}?batch_size=${batchSize}`),

  labelInstance: (id: number, data: LabelRequest) =>
    apiCall<LabelInstanceResponse>(API_ENDPOINTS.LABEL_INSTANCE(id), {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  getInstanceInfo: (id: number) => apiCall<InstanceInfo>(API_ENDPOINTS.GET_INFO(id)),

  saveModel: (id: number) =>
    apiCall<{ message: string }>(API_ENDPOINTS.SAVE_MODEL(id), {
      method: 'POST',
    }),

  getInstances: () => apiCall<InstancesListResponse>(API_ENDPOINTS.GET_INSTANCES),

  deleteInstance: (id: number) =>
    apiCall<{ message: string }>(API_ENDPOINTS.DELETE_INSTANCE(id), {
      method: 'DELETE',
    }),

  // Inference
  infer: async (id: number, data: InferenceData): Promise<InferenceResponse> => {
    // Backend returns array of predictions, e.g., ["Team Name"]
    // We need to transform it to InferenceResponse format
    const rawResponse = await apiCall<string[] | InferenceResponse>(API_ENDPOINTS.INFER(id), {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    // If backend returns array, convert to InferenceResponse format
    if (Array.isArray(rawResponse)) {
      return {
        prediction: rawResponse[0] ?? '',
        confidence: undefined,
        probabilities: undefined,
      };
    }
    
    // If backend already returns InferenceResponse format, use it directly
    return rawResponse;
  },

  // XAI
  explainLime: (
    id: number,
    payload: { ticket_data?: InferenceData; query_idx?: string[]; model_id?: number }
  ) => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    const endpoint = `${API_ENDPOINTS.EXPLAIN_LIME(id)}${params.toString() ? `?${params.toString()}` : ''}`;
    return apiCall<ExplainLimeResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload.ticket_data ?? payload.query_idx),
    });
  },

  findNearestTicket: (
    id: number,
    payload: { ticket_data?: InferenceData; query_idx?: string[]; model_id?: number }
  ) => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    if (payload.query_idx) {
      payload.query_idx.forEach((idx) => params.append('query_idx', idx));
    }
    const endpoint = `${API_ENDPOINTS.NEAREST_TICKET(id)}${params.toString() ? `?${params.toString()}` : ''}`;
    return apiCall<NearestTicketResponse>(endpoint, {
      method: 'POST',
      body: payload.ticket_data ? JSON.stringify(payload.ticket_data) : undefined,
    });
  },

  createXaiRequest: (id: number, payload: { ticket_data: InferenceData; model_id?: number; ticket_ref?: string }) => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    if (payload.ticket_ref) params.append('ticket_ref', payload.ticket_ref);
    const endpoint = `${API_ENDPOINTS.CREATE_XAI_REQUEST(id)}${params.toString() ? `?${params.toString()}` : ''}`;

    return apiCall<XaiRequestResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload.ticket_data),
    });
  },

  getXaiJob: (jobId: string) =>
    apiCall<XaiJobResponse>(API_ENDPOINTS.GET_XAI_JOB(jobId)),

  // Config
  getModels: () => apiCall<ConfigModelsResponse>(API_ENDPOINTS.GET_MODELS),

  getQueryStrategies: () => apiCall<ConfigStrategiesResponse>(API_ENDPOINTS.GET_QUERY_STRATEGIES),

  getCapabilities: () =>
    apiCall<ConfigCapabilitiesResponse>(API_ENDPOINTS.GET_CAPABILITIES),

  // Data
<<<<<<< HEAD
  getTickets: (instanceId: number, indices: string[], trainDataPath?: string) => {
    const url = trainDataPath
      ? `${API_ENDPOINTS.GET_TICKETS(instanceId)}?train_data_path=${encodeURIComponent(trainDataPath)}`
      : API_ENDPOINTS.GET_TICKETS(instanceId);
    return apiCall<TicketsResponse>(url, {
=======
  getTickets: (indices: string[]) => 
    apiCall<TicketsResponse>(API_ENDPOINTS.GET_TICKETS, {
>>>>>>> 775514ca01a4df18b25f0b5ecbdea126e4b79bba
      method: 'POST',
      body: JSON.stringify(indices),
    }),

<<<<<<< HEAD
  getTeams: (instanceId: number = 0, trainDataPath?: string) => {
    const url = trainDataPath
      ? `${API_ENDPOINTS.GET_TEAMS(instanceId)}?train_data_path=${encodeURIComponent(trainDataPath)}`
      : API_ENDPOINTS.GET_TEAMS(instanceId);
    return apiCall<TeamsResponse>(url);
  },

  getCategories: (instanceId: number = 0, trainDataPath?: string) => {
    const url = trainDataPath
      ? `${API_ENDPOINTS.GET_CATEGORIES(instanceId)}?train_data_path=${encodeURIComponent(trainDataPath)}`
      : API_ENDPOINTS.GET_CATEGORIES(instanceId);
    return apiCall<CategoriesResponse>(url);
  },

  getSubcategories: (instanceId: number = 0, trainDataPath?: string, category?: string) => {
    const params = new URLSearchParams();
    if (trainDataPath) {
      params.append('train_data_path', trainDataPath);
    }
    if (category) {
      params.append('category', category);
    }
    const url = params.toString()
      ? `${API_ENDPOINTS.GET_SUBCATEGORIES(instanceId)}?${params.toString()}`
      : API_ENDPOINTS.GET_SUBCATEGORIES(instanceId);
    return apiCall<SubcategoriesResponse>(url);
  },
=======
  getTeams: () => 
    apiCall<TeamsResponse>(API_ENDPOINTS.GET_TEAMS),

  getCategories: () => 
    apiCall<CategoriesResponse>(API_ENDPOINTS.GET_CATEGORIES),

  getSubcategories: () => 
    apiCall<SubcategoriesResponse>(API_ENDPOINTS.GET_SUBCATEGORIES),
>>>>>>> 775514ca01a4df18b25f0b5ecbdea126e4b79bba

  // Resolution
  processResolution: (data: ResolutionProcessRequest) =>
    apiCall<ResolutionProcessResponse>(API_ENDPOINTS.RESOLUTION_PROCESS, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  sendResolutionFeedback: (data: ResolutionFeedbackRequest) =>
    apiCall<ResolutionFeedbackResponse>(API_ENDPOINTS.RESOLUTION_FEEDBACK, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  rebuildEmbeddings: () =>
    apiCall<EmbeddingsRebuildResponse>(API_ENDPOINTS.RESOLUTION_REBUILD_EMBEDDINGS, {
      method: 'POST',
    }),

  // Analytics
  getAnalyticsOverview: () =>
    apiCall<AnalyticsOverview>(API_ENDPOINTS.GET_ANALYTICS_OVERVIEW),

  getSessions: () =>
    apiCall<SessionSummary[]>(API_ENDPOINTS.GET_SESSIONS),

  getSession: (sessionId: string) =>
    apiCall<SessionSummary>(API_ENDPOINTS.GET_SESSION(sessionId)),

  getSessionDecisions: (sessionId: string) =>
    apiCall<SessionLog>(API_ENDPOINTS.GET_SESSION_DECISIONS(sessionId)),

  getSessionLabeling: (sessionId: string) =>
    apiCall<LabelingMetrics>(API_ENDPOINTS.GET_SESSION_LABELING(sessionId)),

  getSessionPerformance: (sessionId: string) =>
    apiCall<ModelPerformanceMetrics>(API_ENDPOINTS.GET_SESSION_PERFORMANCE(sessionId)),

  getSessionEffectiveness: (sessionId: string) =>
    apiCall<ALEffectivenessMetrics>(API_ENDPOINTS.GET_SESSION_EFFECTIVENESS(sessionId)),

  getSessionDistribution: (sessionId: string) =>
    apiCall<ClassDistributionMetrics>(API_ENDPOINTS.GET_SESSION_DISTRIBUTION(sessionId)),

  getSessionExport: (sessionId: string) =>
    apiCall<Record<string, unknown>>(API_ENDPOINTS.GET_SESSION_EXPORT(sessionId)),

  compareSessions: (sessionIds: string[]) =>
    apiCall<SessionComparison>(API_ENDPOINTS.COMPARE_SESSIONS, {
      method: 'POST',
      body: JSON.stringify({ session_ids: sessionIds }),
    }),

  exportSessions: (request: ExportRequest) =>
    apiCall<ExportResponse>(API_ENDPOINTS.EXPORT_SESSIONS, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
};
