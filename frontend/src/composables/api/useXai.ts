import { useQuery, useMutation } from '@tanstack/vue-query';
import { computed, type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import type {
  InferenceData,
  ExplainLimeResponse,
  NearestTicketResponse,
} from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

// Query keys for XAI domain
export const xaiKeys = {
  all: ['xai'] as const,
  lime: (instanceId: number, queryIdx?: string[], ticketData?: InferenceData) =>
    [...xaiKeys.all, 'lime', instanceId, queryIdx, ticketData] as const,
  nearest: (instanceId: number, queryIdx?: string[], ticketData?: InferenceData) =>
    [...xaiKeys.all, 'nearest', instanceId, queryIdx, ticketData] as const,
};

export interface UseXaiOptions {
  meta?: QueryMeta;
  /** Whether to enable the query. Default: true */
  enabled?: MaybeRef<boolean>;
}

export interface ExplainLimePayload {
  ticket_data?: InferenceData;
  query_idx?: string[];
  model_id?: number;
}

export interface NearestTicketPayload {
  ticket_data?: InferenceData;
  query_idx?: string[];
  model_id?: number;
}

/**
 * Get LIME explanation for a prediction.
 * By default, errors are silent since LIME is a secondary/optional feature.
 * 
 * @example
 * ```ts
 * // Using mutation (recommended for on-demand explanations)
 * const { mutate: explainLime, data: explanation } = useExplainLimeMutation(instanceId);
 * explainLime({ ticket_data: { title_anon: '...' } });
 * 
 * // Access explanation
 * // explanation.value?.[0]?.top_words is [string, number][]
 * ```
 */
export function useExplainLimeMutation(
  instanceId: MaybeRef<number>,
  options?: {
    meta?: QueryMeta;
    onSuccess?: (data: ExplainLimeResponse) => void;
  }
) {
  return useMutation({
    mutationFn: (payload: ExplainLimePayload) => apiService.explainLime(toValue(instanceId), payload),
    onSuccess: options?.onSuccess,
    // Silent by default - LIME is a non-critical feature
    meta: {
      silent: true,
      ...options?.meta,
    },
  });
}

/**
 * Find nearest ticket in training data (for explainability).
 * By default, errors are silent since this is a secondary/optional feature.
 * 
 * @example
 * ```ts
 * const { mutate: findNearest, data: nearest } = useNearestTicketMutation(instanceId);
 * findNearest({ ticket_data: { title_anon: '...' } });
 * 
 * // Access result
 * // nearest.value?.nearest_ticket_ref, nearest.value?.similarity_score
 * ```
 */
export function useNearestTicketMutation(
  instanceId: MaybeRef<number>,
  options?: {
    meta?: QueryMeta;
    onSuccess?: (data: NearestTicketResponse) => void;
  }
) {
  return useMutation({
    mutationFn: (payload: NearestTicketPayload) =>
      apiService.findNearestTicket(toValue(instanceId), payload),
    onSuccess: options?.onSuccess,
    // Silent by default - nearest ticket is a non-critical feature
    meta: {
      silent: true,
      ...options?.meta,
    },
  });
}

/**
 * Convenience hook to get both LIME and nearest ticket explanations.
 * 
 * @example
 * ```ts
 * const { explainLime, findNearest, limeData, nearestData, isLoading } = useXai(instanceId);
 * 
 * // Trigger both
 * explainLime({ ticket_data: ticketData });
 * findNearest({ ticket_data: ticketData });
 * ```
 */
export function useXai(instanceId: MaybeRef<number>, options?: UseXaiOptions) {
  const limeMutation = useExplainLimeMutation(instanceId, { meta: options?.meta });
  const nearestMutation = useNearestTicketMutation(instanceId, { meta: options?.meta });

  return {
    explainLime: limeMutation.mutate,
    findNearest: nearestMutation.mutate,
    limeData: limeMutation.data,
    nearestData: nearestMutation.data,
    limeMutation,
    nearestMutation,
    isLoading: computed(() => limeMutation.isPending.value || nearestMutation.isPending.value),
    isError: computed(() => limeMutation.isError.value || nearestMutation.isError.value),
  };
}
