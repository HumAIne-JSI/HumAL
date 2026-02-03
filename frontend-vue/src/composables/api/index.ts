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

// Re-export types
export type { UseConfigOptions } from './useConfig';
export type { UseActiveLearningOptions } from './useActiveLearning';
export type { UseDataOptions } from './useData';
export type { UseInferenceOptions } from './useInference';
export type { UseXaiOptions, ExplainLimePayload, NearestTicketPayload } from './useXai';
export type { UseResolutionOptions } from './useResolution';
