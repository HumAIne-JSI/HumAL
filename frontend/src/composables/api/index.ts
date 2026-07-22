// API Composables - Domain-based Vue Query wrappers
// These composables provide reactive data fetching with automatic error handling

// Config domain - models and strategies
export {
  useModels,
  useQueryStrategies,
  useCapabilities,
  useConfig,
  configKeys,
} from './useConfig';

// Active Learning domain - instances, labeling, model management
export {
  useInstances,
  useInstanceInfo,
  useNextInstances,
  useCreateInstance,
  useLabelInstance,
  useLabelerFeedbackMutation,
  useSaveModel,
  useDeleteInstance,
  activeLearningKeys,
} from './useActiveLearning';

// Data domain - tickets, teams, categories
export {
  useTickets,
  useTeams,
  useCategories,
  useSubcategories,
  useReferenceData,
  dataKeys,
} from './useData';

// Ticket Queue domain - unified queue management
export {
  useTicketQueue,
  ticketQueueKeys,
} from './useTicketQueue';

// Inference domain - predictions
export {
  useInfer,
  useInferWithModelCheck,
  useInferTopK,
  inferenceKeys,
} from './useInference';

// XAI domain - LIME explanations, nearest ticket
export {
  useExplainLimeMutation,
  useNearestTicketMutation,
  useNearestTicketsPerClassMutation,
  useXai,
  xaiKeys,
} from './useXai';

// Resolution domain - assisted Ticket Evolution via the external al-fr-api
export {
  useAssistedResolution,
  useResolutionFeedback,
  useFeedbackStats,
  useSaveResolvedTicket,
  useResolution,
  resolutionKeys,
  DEFAULT_RESOLUTION_TOP_K,
} from './useResolution';

// Analytics domain - benchmarking suite (model performance, resource efficiency,
// human satisfaction) + user-behavior engagement views
export {
  useModelPerformance,
  useUserBehaviorOverview,
  useUserBehaviorAIImpact,
  useUserBehaviorXaiEngagement,
  useUserBehaviorPageEngagement,
  useUserBehaviorTicketHeatmap,
  useUserBehaviorTimeline,
  useUserBehaviorFunnel,
  useSampleData,
  setUseSampleData,
  analyticsKeys,
} from './useAnalytics';

// Re-export types
export type { UseConfigOptions } from './useConfig';
export type { UseActiveLearningOptions } from './useActiveLearning';
export type { UseDataOptions } from './useData';
export type { UseInferenceOptions } from './useInference';
export type { UseXaiOptions, ExplainLimePayload, NearestTicketPayload } from './useXai';
export type { UseResolutionOptions, AssistedResolution, AssistedResolutionInput } from './useResolution';

