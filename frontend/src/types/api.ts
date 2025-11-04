// API Request Types
export interface NewInstanceRequest {
  model_name: string;
  qs_strategy: string;
  class_list: (number | string | null)[];
  train_data_path: string;
  test_data_path: string;
  al_type: "dispatch" | "resolution";
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
  query_idx: number[];
}

export interface LabelInstanceResponse {
  message: string;
}

export interface InstanceInfo {
  instance_id?: number;
  model?: string;
  model_name?: string;
  qs?: string;
  al_type?: string;
  classes?: (string | number)[];
  f1_scores?: number[];
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
export interface ApiError {
  detail: string;
  status_code: number;
}

// Common API Response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
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
  [key: string]: any; // For any additional fields
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
  [key: string]: any;
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