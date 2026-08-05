// Auth Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface UserRegisterRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  user_id: string;
  username: string;
}

// API Request Types
export interface NewInstanceRequest {
  model_name: string;
  qs_strategy: string;
  class_list: (number | string | null)[];
  /** Optional on the live API — defaults are resolved server-side. */
  train_data_path?: string;
  test_data_path?: string;
}

export interface LabelRequest {
  query_idx: (number | string)[];
  labels: (string | number | null)[];
}

/**
 * Strict literal for the feature the labeler found most helpful.
 * Rendered as a dropdown / segmented control — no free text.
 */
export type MostHelpfulFeature =
  | 'lime'
  | 'predicted_class_neighbors'
  | 'historical_neighbors'
  | 'model_prediction';

/**
 * Rich labelling payload for POST /activelearning/{id}/label-with-info.
 * This is the telemetry channel: it persists the human decision together
 * with timing, the model's prediction and any explanation surfaced to the user.
 */
export interface LabelInfo {
  ticket_id: string;
  /** Optional: omitted when i_dont_know retires the ticket. */
  label?: string | null;
  model_prediction?: string | null;
  /** ISO-8601 timestamp when the ticket was presented to the user. */
  start_time: string;
  /** ISO-8601 timestamp when the user submitted the decision. */
  end_time: string;
  explanation?: string | null;
  most_helpful_feature?: MostHelpfulFeature | null;
  /** Analytics-only: labeler reported fatigue. */
  is_tired?: boolean | null;
  /** Analytics-only: labeler found the ticket difficult. */
  is_difficult?: boolean | null;
  /** When true: retires the ticket from the pool; label becomes optional. */
  i_dont_know?: boolean | null;
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

export interface TicketAnalysisSource {
  ticketData?: InferenceData;
  ticketRefs?: string[];
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
  // Additional per-iteration metric lists (parallel to f1_scores / num_labeled)
  accuracies?: number[];
  precisions_macro?: number[];
  precisions_weighted?: number[];
  recalls_macro?: number[];
  recalls_weighted?: number[];
  f1_per_class?: number[][];
  confusion_matrices?: number[][][];
  roc_aucs_ovr_macro?: number[];
}

// Instance delegation (owner-only)
export interface DelegateRequest {
  username: string;
}

export interface DelegateInfo {
  username: string;
  delegate_user_id: string;
  granted_by: string;
  granted_at: string;
}

export interface InstancesListResponse {
  instances: Record<string, InstanceInfo>;
}

export interface InferenceResponse {
  prediction: string | number;
  confidence?: number;
  probabilities?: Record<string, number>;
}

export interface TopKPrediction {
  label: string;
  probability: number;
}

export interface InferenceTopKResponse {
  predictions: TopKPrediction[];
}

/** Raw response of POST /activelearning/{id}/infer_proba */
export interface InferProbaResponse {
  classes: (string | number | null)[];
  probabilities: number[][];
}

// Labeler feedback controls; only I_DONT_KNOW retires the ticket.
export type LabelerFeedbackType = 'I_AM_TIRED' | 'DIFFICULT_TICKET' | 'I_DONT_KNOW';


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
/** A LIME word/weight pair from the new XaiResultFile shape. */
export interface XaiWordWeight {
  word: string;
  weight: number;
}

export interface XaiHighlightedToken {
  token: string;
  direction: 'support' | 'oppose' | 'neutral' | 'positive' | 'negative';
  intensity: number;
  weight?: number;
}

export interface XaiPrediction {
  label: string;
  probabilities: Record<string, number>;
}

/**
 * Response item of POST /xai/{id}/explain_lime (new shape).
 * Replaces the old { class, top_words, error } parsing.
 */
export interface XaiResultFile {
  text: string;
  prediction: XaiPrediction;
  /**
   * Word weights for the top-1 class only. The backend returns tuples
   * ([word, weight]); legacy/mocked data used objects. Consumers must
   * handle both shapes.
   */
  word_weights: (XaiWordWeight | [string, number])[];
  highlighted_tokens?: XaiHighlightedToken[];
  /** Ticket reference string (e.g. "R-523890"), or empty for ad-hoc requests. */
  index?: string | null;
  error?: string | null;
  /** Per-class breakdowns. */
  class_explanations?: unknown[];
}

export type ExplainLimeResponse = XaiResultFile[];

/** Single neighbour entry returned by POST /xai/{id}/nearest */
export interface Neighbor {
  ref: string;
  label?: string | null;
  similarity: number;
  title?: string | null;
  description?: string | null;
  best_sentence?: string | null;
  best_sentence_score?: number | null;
  sentence_score_components?: Record<string, number> | null;
  xai_result?: unknown;
  similar_tickets?: unknown;
  model_prediction?: string | null;
  explanation?: string | null;
  most_helpful_feature?: MostHelpfulFeature | null;
}

/** Response item of POST /xai/{id}/nearest (one entry per query / top-k class). */
export interface NearestTicketResponse {
  query_idx?: string | null;
  predicted_class_neighbors: Neighbor[];
  historical_neighbors: Neighbor[];
}

export interface PerClassSimilarTicket {
  class_label: string;
  ticket_ref: string;
  title: string;
  most_important_sentence: string;
  similarity_score: number;
}

export interface SimilarTicketsPerClassResponse {
  items: PerClassSimilarTicket[];
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

// ======
// Resolution Task API types (external al-fr-api; see services/resolutionApi.ts).
// Shapes verified against the live server via scripts/probe-resolution.ts.
// ======

/** A retrieved similar historical reply from the resolution knowledge base. */
export interface ResolutionSimilarReply {
  retrieved_id: string;
  first_reply: string;
  Title_anon: string;
  Description_anon: string;
  enhanced_score: number;
  feedback_lift: number;
  confidence_gated: boolean;
  al_weight: number;
  [key: string]: unknown;
}

/** Common ticket input shared by /retrieve, /generate, /judge, /judge_and_retrieve. */
export interface ResolutionTicketInput {
  title: string;
  description: string;
  top_k?: number;
  knowledge_base_path?: string;
}

/** POST /retrieve request (accepts optional AL-predicted class/team hints). */
export interface ResolutionRetrieveRequest extends ResolutionTicketInput {
  predicted_class?: string;
  predicted_team?: string;
}

/** POST /retrieve response, and the `retrieved` block of /judge_and_retrieve. */
export interface ResolutionRetrieveResponse {
  predicted_class: string;
  predicted_team: string;
  team_confidence: number | null;
  similar_replies: ResolutionSimilarReply[];
  retrieval_k: number;
}

/** POST /generate request. NOTE: the API does NOT accept predicted_class/team here. */
export type ResolutionGenerateRequest = ResolutionTicketInput;

/** POST /generate response — a complete proposed-solution view. */
export interface ResolutionGenerateResponse {
  classification: string;
  predicted_class: string;
  predicted_team: string;
  team_confidence: number;
  response: string;
  similar_replies: ResolutionSimilarReply[];
  retrieval_k: number;
}

/** POST /judge and /judge_and_retrieve request. */
export interface ResolutionJudgeRequest extends ResolutionRetrieveRequest {
  similar_replies: ResolutionSimilarReply[];
}

/** A per-reply judge score. The API does not formally specify the shape. */
export type ResolutionJudgeScore = Record<string, unknown>;

/** POST /judge response. */
export interface ResolutionJudgeResponse {
  scores: ResolutionJudgeScore[];
  used: string;
}

/** POST /judge_and_retrieve response. */
export interface ResolutionJudgeAndRetrieveResponse {
  scores: ResolutionJudgeScore[];
  votes_applied: number;
  retrieved: ResolutionRetrieveResponse;
}

/** POST /feedback request. `label`: 1 = helpful (👍), 0 = not helpful (👎). */
export interface ResolutionFeedbackRequest {
  query_id: string;
  retrieved_id: string;
  label: number;
  predicted_class?: string;
  predicted_team?: string;
  user_id?: string;
}

/** POST /feedback response. */
export interface ResolutionFeedbackResponse {
  ok: boolean;
}

/** One aggregated feedback row: [scope_key, upvotes, downvotes]. */
export type ResolutionFeedbackAgg = [string, number, number];

/** GET /feedback_stats response. */
export interface ResolutionFeedbackStatsResponse {
  db: string;
  retrieved_id: string;
  raw_count: number;
  agg: ResolutionFeedbackAgg[];
}

/** POST /save_ticket request — persist an approved resolution into the KB. */
export interface ResolutionSaveTicketRequest {
  title: string;
  description: string;
  response: string;
  predicted_team?: string;
  predicted_classification?: string;
  service_name?: string;
  service_subcategory?: string;
  knowledge_base_path?: string;
}

/** POST /save_ticket response. The API does not formally specify the shape. */
export interface ResolutionSaveTicketResponse {
  ok?: boolean;
  [key: string]: unknown;
}

/** GET /config response. */
export interface ResolutionConfigResponse {
  FEEDBACK_DB_PATH: string;
  KNOWLEDGE_BASE_PATH: string;
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

// ======
// User-behavior analytics types
// (matches backend/app/data_models/analytics_dm.py user-behavior models)
// ======

export interface UserBehaviorOverview {
  total_events: number;
  events_by_action: Record<string, number>;
  events_by_page: Record<string, number>;
  unique_tickets_touched: number;
  total_active_seconds: number;
  mean_decision_seconds: number | null;
}

export interface ConfidenceBucket {
  label: string;
  min_confidence: number;
  max_confidence: number;
  confirm: number;
  override: number;
  abstain: number;
}

export interface AIImpactMetrics {
  confirm_count: number;
  override_count: number;
  abstain_count: number;
  acceptance_rate: number | null;
  mean_decision_time_aided_s: number | null;
  mean_decision_time_manual_s: number | null;
  decision_time_delta_s: number | null;
  confidence_buckets: ConfidenceBucket[];
}

export interface XAIEngagementMetrics {
  decisions_with_xai: number;
  decisions_without_xai: number;
  acceptance_rate_with_xai: number | null;
  acceptance_rate_without_xai: number | null;
  mean_decision_time_with_xai_s: number | null;
  mean_decision_time_without_xai_s: number | null;
}

export interface PageEngagementEntry {
  page: string;
  views: number;
  mean_duration_s: number | null;
  total_duration_s: number;
}

export interface PageEngagementMetrics {
  pages: PageEngagementEntry[];
}

export interface TicketHeatmapEntry {
  ticket_ref: string;
  interaction_count: number;
  total_seconds: number;
  last_seen_at: string | null;
}

export interface TicketHeatmap {
  entries: TicketHeatmapEntry[];
}

export interface EventTimelineBin {
  bucket_start: string;
  count: number;
  by_action: Record<string, number>;
}

export interface EventTimeline {
  bin_seconds: number;
  bins: EventTimelineBin[];
}

export interface FunnelMetrics {
  selected: number;
  inspected_explanation: number;
  labeled: number;
  select_to_explanation_rate: number | null;
  explanation_to_label_rate: number | null;
  select_to_label_rate: number | null;
}

// ======
// Benchmarking-suite pillar metrics (AFU: model performance, resource
// efficiency, human satisfaction). Derived client-side from real model info
// (/activelearning/{id}/info) + the tracked telemetry event stream.
// ======

/** Pillar 1 — Model performance summary derived from InstanceInfo. */
export interface ModelPerformanceSummary {
  latest_f1: number | null;
  f1_improvement: number | null;
  latest_accuracy: number | null;
  latest_auroc: number | null;
  entropy_reduction: number | null;
  total_labeled: number;
  iterations: number;
  f1_trend: 'improving' | 'stable' | 'declining' | null;
  convergence_iteration: number | null;
}

/** Pillar 2 — Resource utilisation / efficiency. */
export interface ResourceEfficiencyMetrics {
  // Label-budget efficiency (from model info arrays)
  samples_to_f1_70: number | null;
  samples_to_f1_80: number | null;
  samples_to_f1_90: number | null;
  f1_gain_per_100_labels: number | null;
  labels_total: number;
  // Human effort (from telemetry decision events)
  total_human_seconds: number;
  mean_decision_seconds: number | null;
  decisions_per_hour: number | null;
  // AI compute latency (from telemetry latency probes)
  mean_ai_latency_ms: number | null;
  p95_ai_latency_ms: number | null;
  mean_predict_latency_ms: number | null;
  mean_xai_latency_ms: number | null;
  ai_latency_samples: number;
}

/** Pillar 3 — Human satisfaction / friction. */
export interface SatisfactionMetrics {
  confirm_count: number;
  override_count: number;
  abstain_count: number;
  total_decisions: number;
  acceptance_rate: number | null;
  override_rate: number | null;
  tired_count: number;
  difficult_count: number;
  idk_count: number;
  flagged_decision_rate: number | null;
  /** Composite 0..1 index: acceptance weighted down by reported friction. */
  satisfaction_index: number | null;
}

/**
 * Programme KPIs (AFU objectives) surfaced against their targets on the
 * Benchmarking Suite. Each maps an AFU KPI to a value derived from the
 * pillars + lifecycle telemetry.
 */
export type ProgramKpiStatus = 'on_track' | 'at_risk' | 'off_track' | 'no_data';

export interface ProgramKpi {
  id: string;
  label: string;
  /** 0..1 fraction (all current KPIs are ratios) or null when no data. */
  value: number | null;
  target: number | null;
  higher_is_better: boolean;
  status: ProgramKpiStatus;
  hint: string;
  source: string;
  /** False = surfaced as a proxy / not yet backed by a real event stream. */
  instrumented: boolean;
}

export interface ProgramKpiTargets {
  auto_solve: number;
  ai_managed: number;
  resolution_time_reduction: number;
  reopen_rate_max: number;
  manual_effort_reduction: number;
  trust: number;
  assistance: number;
  overall_satisfaction: number;
}

/**
 * Operator effort on AI-suggested resolutions, derived from `validate_resolution`
 * events emitted by the Resolution tab when a suggestion is accepted. `edit_ratio`
 * is the normalised character edit distance between the generated reply and the
 * operator's final text; `effort_saved` = 1 − mean edit ratio.
 */
export interface ResolutionEffortMetrics {
  resolutions_used: number;
  verbatim_count: number;
  verbatim_rate: number | null;
  mean_edit_ratio: number | null;
  effort_saved: number | null;
  mean_review_seconds: number | null;
}
