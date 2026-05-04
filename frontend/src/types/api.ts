// API Request Types
export interface NewInstanceRequest {
  model_name: string;
  qs_strategy: string;
  class_list: (number | string | null)[];
  train_data_path: string;
  test_data_path: string;
}

export interface LabelRequest {
  query_idx: (number | string)[];
  labels: (string | number | null)[];
}

export interface InferenceData {
  service_subcategory_name?: string;
  team_name?: string;
  service_name?: string;
  last_team_id_name?: string;
  title_anon?: string;
  description_anon?: string;
  public_log_anon?: string;
}

// API Response Types
export interface CreateInstanceResponse {
  instance_id: number;
}

export interface NextInstancesResponse {
  query_idx: (number | string)[];
}

export interface LabelInstanceResponse {
  message: string;
}

export interface InstanceInfo {
  instance_id?: number;
  model?: string;
  model_name?: string;
  qs?: string;
  classes?: (string | number)[];
  f1_scores?: number[];
  num_labeled?: number[];
  mean_entropies?: number[];
  training_accuracy?: number;
  test_accuracy?: number;
  labeled_count?: number;
  total_count?: number;
}

export interface InstancesListResponse {
  instances: Record<string, InstanceInfo>;
}

export interface InferenceResponse {
  prediction: string | number;
  confidence?: number;
  probabilities?: Record<string, number>;
}

// Error Types
export interface ApiErrorData {
  detail: string;
  status_code: number;
}

// Custom error class for API errors (thrown by apiService for Vue Query to catch)
export class ApiError extends Error {
  public readonly statusCode: number;
  public readonly detail: string;

  constructor(statusCode: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.detail = detail;
  }

  /** Check if error is a specific HTTP status */
  is(status: number): boolean {
    return this.statusCode === status;
  }

  /** Check if error is a network/connection error */
  isNetworkError(): boolean {
    return this.statusCode === 0;
  }

  /** Check if error is a client error (4xx) */
  isClientError(): boolean {
    return this.statusCode >= 400 && this.statusCode < 500;
  }

  /** Check if error is a server error (5xx) */
  isServerError(): boolean {
    return this.statusCode >= 500;
  }
}

// Config Response Types
export interface ConfigModelsResponse {
  models: string[];
}

export interface ConfigStrategiesResponse {
  strategies: string[];
}

export interface ConfigCapabilitiesResponse {
  capabilities: string[];
}

// Data Response Types
export interface Ticket {
  Ref: string;
  'Service subcategory->Name'?: string;
  'Team->Name'?: string;
  'Service->Name'?: string;
  'Last team ID->Name'?: string;
  Title_anon?: string;
  Description_anon?: string;
  Public_log_anon?: string;
  [key: string]: unknown;
}

export interface TicketsResponse {
  tickets: Ticket[];
}

export interface TeamsResponse {
  teams: string[];
}

export interface CategoriesResponse {
  categories: string[];
}

export interface SubcategoriesResponse {
  subcategories: string[];
}

// XAI Response Types
export interface ExplainLimeItem {
  top_words: [string, number][];
  error?: string | null;
}

export type ExplainLimeResponse = ExplainLimeItem[];

export interface NearestTicketResponse {
  nearest_ticket_ref: string | string[];
  nearest_ticket_label: string | string[];
  similarity_score: number | number[];
}

export interface XaiRequestResponse {
  job_id: string;
}

export interface XaiResultPayload {
  nearest_ticket_ref?: string | string[];
  nearest_ticket_label?: string | string[];
  similarity_score?: number | number[];
  top_words?: [string, number][];
  error?: string | null;
}

export interface XaiJobResponse {
  status: string;
  result: XaiResultPayload | null;
  result_location?: string | null;
}

// Resolution Types
export interface ResolutionProcessRequest {
  ticket_title?: string;
  ticket_description?: string;
  service_category?: string;
  service_subcategory?: string;
}

export interface SimilarReply {
  Title_anon?: string;
  Description_anon?: string;
  first_reply?: string;
  enhanced_score?: number;
  similarity?: number;
  'Service->Name'?: string;
  'Service subcategory->Name'?: string;
  [key: string]: unknown;
}

export interface ResolutionProcessResponse {
  classification: string;
  predicted_team: string;
  team_confidence: number;
  response: string;
  similar_replies: SimilarReply[];
  retrieval_k: number;
}

export interface ResolutionFeedbackRequest {
  ticket_title: string;
  ticket_description: string;
  edited_response: string;
  predicted_team?: string;
  predicted_classification?: string;
  service_name?: string;
  service_subcategory?: string;
}

export interface ResolutionFeedbackResponse {
  success: boolean;
  message: string;
  ticket_ref?: string;
  new_kb_size?: number;
  embedding_added_incrementally: boolean;
  embedding_invalidated: boolean;
}

export interface EmbeddingsRebuildResponse {
  rebuilt: boolean;
  records: number;
  embedding_dim: number | null;
  cache_file: string | null;
  cache_saved: boolean;
}

// ======
// Benchmark Suite Types (matching backend/app/data_models/benchmark_dm.py)
// ======

/** The five canonical agent kinds */
export type AgentId = 'ORCH' | 'AL' | 'LAB' | 'MOD' | 'XAI';

/** Agent execution model */
export type AgentModel = 'system' | 'ai' | 'human';

/** The canonical object registry */
export type ObjectId = 'Pool' | 'Sel' | 'Ticket' | 'Lbl' | 'Mdl' | 'Snap' | 'KB';

/** Environment block */
export interface Environment {
  id: string;
  class: string;
  attributes: Record<string, unknown>;
}

/** Agent definition */
export interface AgentSpec {
  id: AgentId;
  class: string;
  model: AgentModel;
  affordances: string[];
}

/** Object definition */
export interface ObjectSpec {
  id: ObjectId;
  class: string;
  attributes: Record<string, unknown>;
  affordances: string[];
}

/** A single timestamped script entry */
export interface ScriptEntry {
  t: number;
  agent: AgentId;
  action: string;
  object: ObjectId;
  effect: Record<string, unknown>;
  latency_ms?: number | null;
  duration_s?: number | null;
  interaction_id?: string | null;
}

/** Full benchmark session matching benchmarking_suite/*.json */
export interface BenchmarkSession {
  sim_id: string;
  environment: Environment;
  agents: AgentSpec[];
  objects: ObjectSpec[];
  script: ScriptEntry[];
}

/** Lightweight summary used in /analytics/sessions list */
export interface BenchmarkSessionSummary {
  sim_id: string;
  instance_id?: number | null;
  started_at?: number | null;
  ended_at?: number | null;
  num_events: number;
  agents_used: AgentId[];
  is_active: boolean;
}

/** Aggregated overview across all sessions */
export interface BenchmarkOverview {
  total_sessions: number;
  active_sessions: number;
  total_events: number;
  events_by_agent: Record<string, number>;
  avg_events_per_session: number;
}

/** Frontend telemetry event payload */
export interface TelemetryEventRequest {
  instance_id?: number | null;
  sim_id?: string | null;
  action: string;
  object: ObjectId;
  effect?: Record<string, unknown>;
  duration_s?: number | null;
  interaction_id?: string | null;
}
