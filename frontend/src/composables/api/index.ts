// API Composables - Domain-based Vue Query wrappers
// These composables provide reactive data fetching with automatic error handling

// Config domain - models and strategies
export {
  useModels,
  useQueryStrategies,
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
  inferenceKeys,
} from './useInference';

// XAI domain - LIME explanations, nearest ticket
export {
  useExplainLimeMutation,
  useNearestTicketMutation,
  useXai,
  xaiKeys,
} from './useXai';

// Resolution domain - ticket resolution with RAG
export {
  useProcessResolution,
  useResolutionFeedback,
  useResolution,
  resolutionKeys,
} from './useResolution';

// Analytics domain - session logs, metrics, comparisons
export {
  useAnalyticsOverview,
  useSessions,
  useSession,
  useSessionDecisions,
  useSessionLabeling,
  useSessionPerformance,
  useSessionEffectiveness,
  useSessionDistribution,
  useCompareSessions,
  useExportSessions,
  useSessionAllMetrics,
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
export type { UseResolutionOptions } from './useResolution';
export type { UseAnalyticsOptions } from './useAnalytics';
