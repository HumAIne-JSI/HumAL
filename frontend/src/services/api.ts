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
  TicketsResponse,
  TeamsResponse,
  CategoriesResponse,
  SubcategoriesResponse,
  ExplainLimeResponse,
  NearestTicketResponse,
  ResolutionProcessRequest,
  ResolutionProcessResponse,
  ResolutionFeedbackRequest,
  ResolutionFeedbackResponse
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
  
  // Config
  GET_MODELS: '/config/models',
  GET_QUERY_STRATEGIES: '/config/query-strategies',
  
  // Data
  GET_TICKETS: (id: number) => `/data/${id}/tickets`,
  GET_TEAMS: (id: number) => `/data/${id}/teams`,
  GET_CATEGORIES: (id: number) => `/data/${id}/categories`,
  GET_SUBCATEGORIES: (id: number) => `/data/${id}/subcategories`,
  
  // Resolution
  RESOLUTION_PROCESS: '/resolution/process',
  RESOLUTION_FEEDBACK: '/resolution/feedback',
};

// Enhanced error handling
class ApiError extends Error {
  constructor(public status: number, public statusText: string, public detail?: string) {
    super(`API Error: ${status} ${statusText}${detail ? ` - ${detail}` : ''}`);
    this.name = 'ApiError';
  }
}

// Generic API call function with enhanced error handling
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: {
          status_code: response.status,
          detail: data.detail || response.statusText
        }
      };
    }

    return {
      success: true,
      data
    };
  } catch (error) {
    return {
      success: false,
      error: {
        status_code: 0,
        detail: error instanceof Error ? error.message : 'Network error'
      }
    };
  }
}

// API service functions
export const apiService = {
  // Active Learning
  createInstance: (data: NewInstanceRequest) => 
    apiCall<CreateInstanceResponse>(API_ENDPOINTS.CREATE_INSTANCE, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getNextInstances: (id: number, batchSize: number = 1) => 
    apiCall<NextInstancesResponse>(API_ENDPOINTS.GET_NEXT_INSTANCES(id) + `?batch_size=${batchSize}`),

  labelInstance: (id: number, data: LabelRequest) => 
    apiCall<LabelInstanceResponse>(API_ENDPOINTS.LABEL_INSTANCE(id), {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  getInstanceInfo: (id: number) => 
    apiCall<InstanceInfo>(API_ENDPOINTS.GET_INFO(id)),
  
  saveModel: (id: number) => 
    apiCall<{ message: string }>(API_ENDPOINTS.SAVE_MODEL(id), {
      method: 'POST',
    }),

  getInstances: () => 
    apiCall<InstancesListResponse>(API_ENDPOINTS.GET_INSTANCES),
  
  deleteInstance: (id: number) => 
    apiCall<{ message: string }>(API_ENDPOINTS.DELETE_INSTANCE(id), {
      method: 'DELETE',
    }),

  // Inference
  infer: (id: number, data: InferenceData) => 
    apiCall<InferenceResponse>(API_ENDPOINTS.INFER(id), {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // XAI
  explainLime: (id: number, payload: { ticket_data?: InferenceData; query_idx?: string[]; model_id?: number }) => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    const endpoint = `${API_ENDPOINTS.EXPLAIN_LIME(id)}${params.toString() ? `?${params.toString()}` : ''}`;
    return apiCall<ExplainLimeResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload.ticket_data ? payload.ticket_data : payload.query_idx),
      headers: {
        'Content-Type': 'application/json'
      }
    });
  },

  findNearestTicket: (id: number, payload: { ticket_data?: InferenceData; query_idx?: string[]; model_id?: number }) => {
    const params = new URLSearchParams();
    if (payload.model_id !== undefined) params.append('model_id', String(payload.model_id));
    
    // If using query_idx, add it as query parameters
    if (payload.query_idx) {
      payload.query_idx.forEach(idx => params.append('query_idx', idx));
    }
    
    const endpoint = `${API_ENDPOINTS.NEAREST_TICKET(id)}${params.toString() ? `?${params.toString()}` : ''}`;
    return apiCall<NearestTicketResponse>(endpoint, {
      method: 'POST',
      body: payload.ticket_data ? JSON.stringify(payload.ticket_data) : undefined,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  },

  // Config
  getModels: () => 
    apiCall<ConfigModelsResponse>(API_ENDPOINTS.GET_MODELS),

  getQueryStrategies: () => 
    apiCall<ConfigStrategiesResponse>(API_ENDPOINTS.GET_QUERY_STRATEGIES),

  // Data
  getTickets: (instanceId: number, indices: string[], trainDataPath?: string) => {
    const url = trainDataPath 
      ? `${API_ENDPOINTS.GET_TICKETS(instanceId)}?train_data_path=${encodeURIComponent(trainDataPath)}`
      : API_ENDPOINTS.GET_TICKETS(instanceId);
    return apiCall<TicketsResponse>(url, {
      method: 'POST',
      body: JSON.stringify(indices),
    });
  },

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

  getSubcategories: (instanceId: number = 0, trainDataPath?: string) => {
    const url = trainDataPath 
      ? `${API_ENDPOINTS.GET_SUBCATEGORIES(instanceId)}?train_data_path=${encodeURIComponent(trainDataPath)}`
      : API_ENDPOINTS.GET_SUBCATEGORIES(instanceId);
    return apiCall<SubcategoriesResponse>(url);
  },

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
};
