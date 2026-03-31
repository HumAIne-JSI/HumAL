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

// ============================================================================
// Analytics Types (matching backend/app/data_models/analytics_dm.py)
// ============================================================================

/** Actor types for decision logging */
export type ActorType = 'system' | 'ai' | 'human';

/** Single decision/event in an active learning session */
export interface Decision {
  t: number;                          // Timestamp in seconds from session start
  actor_type: ActorType;
  action: string;
  payload: Record<string, unknown>;
  interaction_id?: string;
  latency_ms?: number;
  duration_s?: number;
}

/** Metadata for an active learning session */
export interface SessionMeta {
  task_parameters: Record<string, unknown>;
}

/** Complete decision log for an active learning session */
export interface SessionLog {
  sim_id: string;
  session_id: string;
  pilot_tag?: string;
  user_id?: string;
  app_version?: string;
  ai_model_version?: string;
  meta: SessionMeta;
  decisions: Decision[];
}

/** Aggregated summary statistics for a session */
export interface SessionSummary {
  session_id: string;
  instance_id: number;
  model_name: string;
  qs_strategy: string;
  
  // Labeling metrics
  total_labeled: number;
  labeling_iterations: number;
  avg_labeling_duration_s?: number;
  
  // Model performance
  latest_f1?: number;
  f1_improvement?: number;
  latest_accuracy?: number;
  
  // AL effectiveness
  latest_mean_entropy?: number;
  entropy_reduction?: number;
  
  // Timestamps
  created_at: string;
  last_updated: string;
}

/** Detailed labeling efficiency metrics */
export interface LabelingMetrics {
  total_labels: number;
  labels_per_iteration: number[];
  avg_duration_per_label_s?: number;
  min_duration_s?: number;
  max_duration_s?: number;
  throughput_per_hour?: number;
}

/** Model performance trend metrics */
export interface ModelPerformanceMetrics {
  f1_scores: number[];
  mean_entropies: number[];
  num_labeled: number[];
  f1_trend?: 'improving' | 'stable' | 'declining';
  convergence_iteration?: number;
}

/** Active learning strategy effectiveness metrics */
export interface ALEffectivenessMetrics {
  strategy: string;
  uncertainty_reduction_rate?: number;
  samples_to_target_f1?: number;
  efficiency_score?: number;
}

/** Class distribution and balance metrics */
export interface ClassDistributionMetrics {
  class_counts: Record<string, number>;
  class_percentages: Record<string, number>;
  imbalance_ratio?: number;
  majority_class?: string;
  minority_class?: string;
}

/** Aggregated analytics across all sessions */
export interface AnalyticsOverview {
  total_sessions: number;
  total_instances: number;
  total_labels: number;
  total_iterations: number;
  
  // Averages across sessions
  avg_f1_score?: number;
  avg_labels_per_session?: number;
  avg_labeling_duration_s?: number;
  
  // Best performers
  best_f1_instance_id?: number;
  best_f1_score?: number;
  most_efficient_strategy?: string;
  
  // Strategy breakdown
  strategy_performance: Record<string, number>;
}

/** Side-by-side comparison of multiple sessions */
export interface SessionComparison {
  session_ids: string[];
  instance_ids: number[];
  
  // Comparative metrics
  f1_scores: Record<number, number[]>;
  num_labeled: Record<number, number[]>;
  strategies: Record<number, string>;
  
  // Rankings
  f1_ranking: number[];
  efficiency_ranking: number[];
}

/** Request model for exporting session data */
export interface ExportRequest {
  instance_ids: number[];
  include_decisions?: boolean;
  include_metrics?: boolean;
  format?: 'json' | 'csv';
}

/** Export response */
export interface ExportResponse {
  data: Record<string, unknown>;
  format: string;
}

// ============================================================================
// Simulation Environment Types (for JSON import)
// ============================================================================

/** Agent definition in simulation environment */
export interface SimAgent {
  id: string;
  class: string;
  model: 'system' | 'ai' | 'human';
  affordances: string[];
}

/** Object definition in simulation environment */
export interface SimObject {
  id: string;
  class: string;
  attributes: Record<string, unknown>;
  affordances: string[];
}

/** Script event in simulation */
export interface ScriptEvent {
  t: number;
  agent: string;
  action: string;
  object: string;
  effect: Record<string, unknown>;
  latency_ms?: number;
  duration_s?: number;
}

/** Simulation environment definition */
export interface SimulationEnvironment {
  sim_id: string;
  environment: {
    id: string;
    class: string;
    attributes: Record<string, unknown>;
  };
  agents: SimAgent[];
  objects: SimObject[];
  script: ScriptEvent[];
}

/** Wrapper for logs array from sample JSON */
export interface SessionLogsFile {
  logs: SessionLog[];
}
