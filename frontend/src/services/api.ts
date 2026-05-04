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
  // Benchmark / analytics types
  type BenchmarkOverview,
  type BenchmarkSession,
  type BenchmarkSessionSummary,
  type TelemetryEventRequest,
  type XaiRequestResponse,
  type XaiJobResponse,
  type ConfigCapabilitiesResponse,
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

  // XAI
  CREATE_XAI_REQUEST: (id: number) => `/xai/${id}/requests`,
  GET_XAI_JOB: (jobId: string) => `/xai/jobs/${jobId}`,
  
  // Config
  GET_MODELS: '/config/models',
  GET_QUERY_STRATEGIES: '/config/query-strategies',
  GET_CAPABILITIES: '/config/capabilities',
  
  // Data
  GET_TICKETS: (id: number) => `/data/${id}/tickets`,
  GET_TEAMS: (id: number) => `/data/${id}/teams`,
  GET_CATEGORIES: (id: number) => `/data/${id}/categories`,
  GET_SUBCATEGORIES: (id: number) => `/data/${id}/subcategories`,
  
  // Resolution
  RESOLUTION_PROCESS: '/resolution/process',
  RESOLUTION_FEEDBACK: '/resolution/feedback',
  RESOLUTION_REBUILD_EMBEDDINGS: '/resolution/rebuild-embeddings',

  // Analytics / benchmark suite
  GET_ANALYTICS_OVERVIEW: '/analytics/overview',
  GET_SESSIONS: '/analytics/sessions',
  GET_SESSION: (simId: string) => `/analytics/sessions/${simId}`,
  GET_SESSION_SCRIPT: (simId: string) => `/analytics/sessions/${simId}/script`,
  GET_SESSION_EXPORT: (simId: string) => `/analytics/sessions/${simId}/export`,
  POST_TELEMETRY_EVENT: '/analytics/event',
  END_SESSION: (simId: string) => `/analytics/sessions/${simId}/end`,
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
  getTickets: (instanceId: number, indices: string[], _trainDataPath?: string) => 
    apiCall<TicketsResponse>(API_ENDPOINTS.GET_TICKETS(instanceId), {
      method: 'POST',
      body: JSON.stringify(indices),
    }),

  getTeams: (instanceId?: number, _trainDataPath?: string) => 
    apiCall<TeamsResponse>(API_ENDPOINTS.GET_TEAMS(instanceId ?? 0)),

  getCategories: (instanceId?: number, _trainDataPath?: string) => 
    apiCall<CategoriesResponse>(API_ENDPOINTS.GET_CATEGORIES(instanceId ?? 0)),

  getSubcategories: (instanceId?: number, _trainDataPath?: string) => 
    apiCall<SubcategoriesResponse>(API_ENDPOINTS.GET_SUBCATEGORIES(instanceId ?? 0)),

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

  // Analytics / benchmark suite
  getAnalyticsOverview: () =>
    apiCall<BenchmarkOverview>(API_ENDPOINTS.GET_ANALYTICS_OVERVIEW),

  getSessions: () =>
    apiCall<BenchmarkSessionSummary[]>(API_ENDPOINTS.GET_SESSIONS),

  getSession: (simId: string) =>
    apiCall<BenchmarkSession>(API_ENDPOINTS.GET_SESSION(simId)),

  getSessionScript: (simId: string) =>
    apiCall<{ sim_id: string; script: BenchmarkSession['script'] }>(
      API_ENDPOINTS.GET_SESSION_SCRIPT(simId),
    ),

  getSessionExport: (simId: string) =>
    apiCall<BenchmarkSession>(API_ENDPOINTS.GET_SESSION_EXPORT(simId)),

  postTelemetryEvent: (event: TelemetryEventRequest) =>
    apiCall<{ recorded: boolean; t?: number; sim_id?: string; reason?: string }>(
      API_ENDPOINTS.POST_TELEMETRY_EVENT,
      {
        method: 'POST',
        body: JSON.stringify(event),
      },
    ),

  endSession: (simId: string) =>
    apiCall<{ sim_id: string; file: string }>(API_ENDPOINTS.END_SESSION(simId), {
      method: 'POST',
    }),
}
