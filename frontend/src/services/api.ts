import {
  ApiError,
  type NewInstanceRequest,
  type LabelRequest,
  type LabelInfo,
  type InferenceData,
  type CreateInstanceResponse,
  type NextInstancesResponse,
  type LabelInstanceResponse,
  type InstanceInfo,
  type InstancesListResponse,
  type InferenceResponse,
  type InferenceTopKResponse,
  type InferProbaResponse,
  type LabelerFeedbackRequest,
  type LabelerFeedbackResponse,
  type ConfigModelsResponse,
  type ConfigStrategiesResponse,
  type TicketsResponse,
  type TeamsResponse,
  type CategoriesResponse,
  type SubcategoriesResponse,
  type ExplainLimeResponse,
  type NearestTicketResponse,
  type SimilarTicketsPerClassResponse,
  // Benchmark / analytics types
  type BenchmarkOverview,
  type BenchmarkSession,
  type BenchmarkSessionSummary,
  type TelemetryEventRequest,
  type UserBehaviorOverview,
  type AIImpactMetrics,
  type XAIEngagementMetrics,
  type PageEngagementMetrics,
  type TicketHeatmap,
  type EventTimeline,
  type FunnelMetrics,
  type XaiRequestResponse,
  type XaiJobResponse,
  type ConfigCapabilitiesResponse,
  // Auth / delegation types
  type LoginRequest,
  type UserRegisterRequest,
  type TokenResponse,
  type UserResponse,
  type DelegateRequest,
  type DelegateInfo,
} from '@/types/api';

const RAW_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
// Normalise: strip any trailing slash so `${base}${endpoint}` never doubles up.
const API_BASE_URL = RAW_API_BASE_URL.replace(/\/+$/, '');

// ---------------------------------------------------------------------------
// Auth token management
// The backend accepts `Authorization: Bearer <jwt>` on all secured routes and
// falls back to a system user when the header is absent/invalid. We keep the
// token in a module-level variable (hydrated from localStorage) so every
// request made through `apiCall` is authenticated automatically.
// ---------------------------------------------------------------------------
const AUTH_TOKEN_STORAGE_KEY = 'humal-auth-token';
let authToken: string | null =
  typeof localStorage !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) : null;

/** Set (or clear) the JWT used for all subsequent API calls. */
export function setAuthToken(token: string | null): void {
  authToken = token;
  if (typeof localStorage === 'undefined') return;
  if (token) {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  }
}

/** Current JWT, or null when unauthenticated. */
export function getAuthToken(): string | null {
  return authToken;
}

/** Optional hook invoked when the API returns 401 (e.g. to force re-login). */
let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

// API endpoints
export const API_ENDPOINTS = {
  // Auth / users
  LOGIN: '/users/login',
  REGISTER: '/users/register',
  ME: '/users/me',

  // Active Learning
  CREATE_INSTANCE: '/activelearning/new',
  GET_NEXT_INSTANCES: (id: number) => `/activelearning/${id}/next`,
  LABEL_INSTANCE: (id: number) => `/activelearning/${id}/label`,
  LABEL_WITH_INFO: (id: number) => `/activelearning/${id}/label-with-info`,
  LABELER_FEEDBACK: (id: number) => `/activelearning/${id}/feedback`,
  GET_INFO: (id: number) => `/activelearning/${id}/info`,
  SAVE_MODEL: (id: number) => `/activelearning/${id}/save`,
  GET_INSTANCES: '/activelearning/instances',
  DELETE_INSTANCE: (id: number) => `/activelearning/${id}`,

  // Instance delegation (owner only)
  DELEGATE_INSTANCE: (id: number) => `/activelearning/${id}/delegate`,
  REVOKE_DELEGATION: (id: number, username: string) =>
    `/activelearning/${id}/delegate/${encodeURIComponent(username)}`,
  LIST_DELEGATES: (id: number) => `/activelearning/${id}/delegates`,

  // Inference
  INFER: (id: number) => `/activelearning/${id}/infer`,
  INFER_PROBA: (id: number) => `/activelearning/${id}/infer_proba`,

  // XAI
  EXPLAIN_LIME: (id: number) => `/xai/${id}/explain_lime`,
  XAI_NEAREST: (id: number) => `/xai/${id}/nearest`,

  // XAI
  CREATE_XAI_REQUEST: (id: number) => `/xai/${id}/requests`,
  GET_XAI_JOB: (jobId: string) => `/xai/jobs/${jobId}`,
  
  // Config
  GET_MODELS: '/config/models',
  GET_QUERY_STRATEGIES: '/config/query-strategies',
  GET_CAPABILITIES: '/config/capabilities',
  
  // Data (branch routes are instance-agnostic: /data/tickets, /data/teams, ...)
  GET_TICKETS: '/data/tickets',
  GET_TEAMS: '/data/teams',
  GET_CATEGORIES: '/data/categories',
  GET_SUBCATEGORIES: '/data/subcategories',

  // Analytics / benchmark suite
  GET_ANALYTICS_OVERVIEW: '/analytics/overview',
  GET_SESSIONS: '/analytics/sessions',
  GET_SESSION: (simId: string) => `/analytics/sessions/${simId}`,
  GET_SESSION_SCRIPT: (simId: string) => `/analytics/sessions/${simId}/script`,
  GET_SESSION_EXPORT: (simId: string) => `/analytics/sessions/${simId}/export`,
  POST_TELEMETRY_EVENT: '/analytics/event',
  END_SESSION: (simId: string) => `/analytics/sessions/${simId}/end`,

  // User-behavior analytics
  GET_USER_BEHAVIOR_OVERVIEW: '/analytics/user-behavior/overview',
  GET_USER_BEHAVIOR_AI_IMPACT: '/analytics/user-behavior/ai-impact',
  GET_USER_BEHAVIOR_XAI: '/analytics/user-behavior/xai-engagement',
  GET_USER_BEHAVIOR_PAGE: '/analytics/user-behavior/page-engagement',
  GET_USER_BEHAVIOR_HEATMAP: '/analytics/user-behavior/ticket-heatmap',
  GET_USER_BEHAVIOR_TIMELINE: '/analytics/user-behavior/timeline',
  GET_USER_BEHAVIOR_FUNNEL: '/analytics/user-behavior/funnel',
} as const;

/**
 * Generic API call function that throws ApiError on failure.
 * Designed to work with Vue Query - throws errors instead of returning error objects.
 */
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };
  // Attach the JWT when present. The backend falls back to a system user when
  // the header is absent, so unauthenticated calls still succeed.
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
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
      if (response.status === 401) onUnauthorized?.();
      throw new ApiError(response.status, response.statusText);
    }
    // If response was ok but not JSON, return empty object
    return {} as T;
  }

  if (!response.ok) {
    if (response.status === 401) onUnauthorized?.();
    const detail = (data as { detail?: string })?.detail || response.statusText;
    throw new ApiError(response.status, detail);
  }

  return data as T;
}

// API service functions - all throw ApiError on failure
export const apiService = {
  // Auth
  login: (data: LoginRequest) =>
    apiCall<TokenResponse>(API_ENDPOINTS.LOGIN, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  register: (data: UserRegisterRequest) =>
    apiCall<UserResponse>(API_ENDPOINTS.REGISTER, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMe: () => apiCall<UserResponse>(API_ENDPOINTS.ME),

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

  /**
   * Submit human label decisions with full context (timing, model prediction,
   * explanation). This is the primary telemetry channel on the humaine-al-api
   * backend: it persists the decision AND records the benchmark event, while
   * also retraining the model and recomputing metrics (same side effects as
   * labelInstance — never call both for the same ticket).
   */
  labelWithInfo: (id: number, data: LabelInfo[]) =>
    apiCall<{ message?: string } & Record<string, unknown>>(
      API_ENDPOINTS.LABEL_WITH_INFO(id),
      {
        method: 'POST',
        body: JSON.stringify(data),
      },
    ),

  /**
   * Submit a labeler-feedback (skip-with-reason) event for the current ticket.
   * Does NOT submit a class label — the ticket stays in the unlabeled pool.
   */
  submitLabelerFeedback: (id: number, data: LabelerFeedbackRequest) =>
    apiCall<LabelerFeedbackResponse>(API_ENDPOINTS.LABELER_FEEDBACK(id), {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getInstanceInfo: (id: number) => apiCall<InstanceInfo>(API_ENDPOINTS.GET_INFO(id)),

  saveModel: (id: number) =>
    apiCall<{ model_id?: number; message?: string }>(API_ENDPOINTS.SAVE_MODEL(id), {
      method: 'POST',
    }),

  getInstances: () => apiCall<InstancesListResponse>(API_ENDPOINTS.GET_INSTANCES),

  deleteInstance: (id: number) =>
    apiCall<{ message: string }>(API_ENDPOINTS.DELETE_INSTANCE(id), {
      method: 'DELETE',
    }),

  // Instance delegation (owner only)
  delegateInstance: (id: number, data: DelegateRequest) =>
    apiCall<{ message?: string } & Record<string, unknown>>(API_ENDPOINTS.DELEGATE_INSTANCE(id), {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  revokeDelegation: (id: number, username: string) =>
    apiCall<{ message?: string } & Record<string, unknown>>(
      API_ENDPOINTS.REVOKE_DELEGATION(id, username),
      { method: 'DELETE' },
    ),

  listDelegates: (id: number) =>
    apiCall<DelegateInfo[]>(API_ENDPOINTS.LIST_DELEGATES(id)),

  // Inference
  infer: async (id: number, data?: InferenceData | null, queryIdx?: string[]): Promise<InferenceResponse> => {
    // The API accepts EITHER an ad-hoc `data` body OR a `query_idx` query param
    // (ticket refs) — never both. Passing query_idx logs events server-side.
    const useQueryIdx = !!queryIdx?.length;
    const params = new URLSearchParams();
    if (useQueryIdx) queryIdx!.forEach((idx) => params.append('query_idx', idx));
    const endpoint = `${API_ENDPOINTS.INFER(id)}${params.toString() ? `?${params.toString()}` : ''}`;

    // Backend returns array of predictions, e.g., ["Team Name"]
    const rawResponse = await apiCall<string[] | InferenceResponse>(endpoint, {
      method: 'POST',
      body: useQueryIdx ? undefined : JSON.stringify(data ?? {}),
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

  /**
   * Raw class-probability inference.
   * Backend contract: POST /activelearning/{id}/infer_proba with EITHER a
   * `data` body OR a `query_idx` query param (ticket refs) — never both.
   * Response shape: { classes: [...], probabilities: [[...]] }
   */
  inferProba: (id: number, data?: InferenceData | null, queryIdx?: string[]) => {
    const useQueryIdx = !!queryIdx?.length;
    const params = new URLSearchParams();
    if (useQueryIdx) queryIdx!.forEach((idx) => params.append('query_idx', idx));
    const endpoint = `${API_ENDPOINTS.INFER_PROBA(id)}${params.toString() ? `?${params.toString()}` : ''}`;
    return apiCall<InferProbaResponse>(endpoint, {
      method: 'POST',
      body: useQueryIdx ? undefined : JSON.stringify(data ?? {}),
    });
  },

  /**
   * Run top-K inference. Returns the K highest-probability predicted classes.
   * The backend has no dedicated top-K route, so this is derived from
   * POST /activelearning/{id}/infer_proba by sorting the probability row.
   */
  inferTopK: async (id: number, data: InferenceData, topK: number = 2): Promise<InferenceTopKResponse> => {
    const proba = await apiService.inferProba(id, data);
    const row = proba.probabilities?.[0] ?? [];
    const predictions = proba.classes
      .map((cls, i) => ({ label: String(cls ?? ''), probability: row[i] ?? 0 }))
      .sort((a, b) => b.probability - a.probability)
      .slice(0, topK);
    return { predictions };
  },

  // XAI
  explainLime: (
    id: number,
    payload: { ticket_data?: InferenceData; query_idx?: string[]; model_id?: number; top_k?: number }
  ) => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    if (payload.top_k !== undefined) params.append('top_k', String(payload.top_k));
    if (payload.query_idx) payload.query_idx.forEach((idx) => params.append('query_idx', idx));
    const endpoint = `${API_ENDPOINTS.EXPLAIN_LIME(id)}${params.toString() ? `?${params.toString()}` : ''}`;
    return apiCall<ExplainLimeResponse>(endpoint, {
      method: 'POST',
      // Body is the ad-hoc ticket data (or null when using query_idx refs).
      body: payload.ticket_data ? JSON.stringify(payload.ticket_data) : undefined,
    });
  },

  /**
   * Get nearest historical tickets via POST /xai/{id}/nearest.
   * Returns one NearestTicketResponse per query (each with predicted-class and
   * historical neighbour lists).
   */
  getNearest: (
    id: number,
    payload: { ticket_data?: InferenceData; query_idx?: string[]; model_id?: number; top_k?: number }
  ) => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    if (payload.top_k !== undefined) params.append('top_k', String(payload.top_k));
    if (payload.query_idx) payload.query_idx.forEach((idx) => params.append('query_idx', idx));
    const endpoint = `${API_ENDPOINTS.XAI_NEAREST(id)}${params.toString() ? `?${params.toString()}` : ''}`;
    return apiCall<NearestTicketResponse[]>(endpoint, {
      method: 'POST',
      body: payload.ticket_data ? JSON.stringify(payload.ticket_data) : undefined,
    });
  },

  /**
   * Get the closest historical tickets for the given ticket.
   * The humaine-al-api backend exposes POST /xai/{id}/nearest which returns
   * predicted-class + historical neighbours. We flatten those neighbours into
   * the per-class shape the UI expects (one entry per neighbour, deduplicated
   * by label), so the "similar tickets" panel keeps working.
   */
  getNearestTicketsPerClass: async (
    id: number,
    payload: { ticket_data: InferenceData; class_labels: string[]; model_id?: number }
  ): Promise<SimilarTicketsPerClassResponse> => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    params.append('top_k', String(Math.max(payload.class_labels.length, 1)));
    const endpoint = `${API_ENDPOINTS.XAI_NEAREST(id)}?${params.toString()}`;
    const results = await apiCall<NearestTicketResponse[]>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload.ticket_data),
    });

    const first = results?.[0];
    const neighbors = [
      ...(first?.predicted_class_neighbors ?? []),
      ...(first?.historical_neighbors ?? []),
    ];

    const seen = new Set<string>();
    const items = neighbors
      .filter((n) => {
        const key = n.label ?? n.ref;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .map((n) => ({
        class_label: n.label ?? '',
        ticket_ref: n.ref,
        title: n.title ?? '',
        most_important_sentence: n.best_sentence ?? '',
        similarity_score: n.similarity,
      }));

    return { items };
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

  // Data (instance-agnostic on the branch; instanceId kept for call-site compat)
  getTickets: (_instanceId: number, indices: string[], _trainDataPath?: string) => 
    apiCall<TicketsResponse>(API_ENDPOINTS.GET_TICKETS, {
      method: 'POST',
      body: JSON.stringify(indices),
    }),

  getTeams: (_instanceId?: number, _trainDataPath?: string) => 
    apiCall<TeamsResponse>(API_ENDPOINTS.GET_TEAMS),

  getCategories: (_instanceId?: number, _trainDataPath?: string) => 
    apiCall<CategoriesResponse>(API_ENDPOINTS.GET_CATEGORIES),

  getSubcategories: (_instanceId?: number, _trainDataPath?: string, _category?: string) => 
    apiCall<SubcategoriesResponse>(API_ENDPOINTS.GET_SUBCATEGORIES),

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

  // User-behavior analytics
  getUserBehaviorOverview: (instanceId?: number | null) =>
    apiCall<UserBehaviorOverview>(
      `${API_ENDPOINTS.GET_USER_BEHAVIOR_OVERVIEW}${instanceId ? `?instance_id=${instanceId}` : ''}`,
    ),

  getUserBehaviorAIImpact: (instanceId?: number | null) =>
    apiCall<AIImpactMetrics>(
      `${API_ENDPOINTS.GET_USER_BEHAVIOR_AI_IMPACT}${instanceId ? `?instance_id=${instanceId}` : ''}`,
    ),

  getUserBehaviorXaiEngagement: (instanceId?: number | null) =>
    apiCall<XAIEngagementMetrics>(
      `${API_ENDPOINTS.GET_USER_BEHAVIOR_XAI}${instanceId ? `?instance_id=${instanceId}` : ''}`,
    ),

  getUserBehaviorPageEngagement: (instanceId?: number | null) =>
    apiCall<PageEngagementMetrics>(
      `${API_ENDPOINTS.GET_USER_BEHAVIOR_PAGE}${instanceId ? `?instance_id=${instanceId}` : ''}`,
    ),

  getUserBehaviorTicketHeatmap: (instanceId?: number | null, limit: number = 20) => {
    const params = new URLSearchParams();
    if (instanceId) params.append('instance_id', String(instanceId));
    params.append('limit', String(limit));
    return apiCall<TicketHeatmap>(
      `${API_ENDPOINTS.GET_USER_BEHAVIOR_HEATMAP}?${params.toString()}`,
    );
  },

  getUserBehaviorTimeline: (instanceId?: number | null, binSeconds: number = 60) => {
    const params = new URLSearchParams();
    if (instanceId) params.append('instance_id', String(instanceId));
    params.append('bin_seconds', String(binSeconds));
    return apiCall<EventTimeline>(
      `${API_ENDPOINTS.GET_USER_BEHAVIOR_TIMELINE}?${params.toString()}`,
    );
  },

  getUserBehaviorFunnel: (instanceId?: number | null) =>
    apiCall<FunnelMetrics>(
      `${API_ENDPOINTS.GET_USER_BEHAVIOR_FUNNEL}${instanceId ? `?instance_id=${instanceId}` : ''}`,
    ),
}
