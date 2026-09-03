import { useMutation } from '@tanstack/vue-query';
import { type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import {
  ApiError,
  type InferenceData,
  type InferenceResponse,
  type InferenceTopKResponse,
  type TicketAnalysisSource,
} from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

// Query keys for inference domain
export const inferenceKeys = {
  all: ['inference'] as const,
};

export interface UseInferenceOptions {
  meta?: QueryMeta;
  onSuccess?: (data: InferenceResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * Run inference on a ticket using a trained model.
 * Accepts either ad-hoc ticket data (InferenceData) or a ticket ref source.
 *
 * @example
 * ```ts
 * const { mutate: infer, isPending, data: result } = useInfer(instanceId);
 *
 * // Inference by ticket ref
 * infer({ ticketRefs: ['R-1234'] });
 *
 * // Inference by ad-hoc data
 * infer({ ticketData: { title_anon: 'Cannot connect to VPN' } });
 *
 * // Access result
 * // result.value?.prediction, result.value?.confidence
 * ```
 */
export function useInfer(
  instanceId: MaybeRef<number>,
  options?: UseInferenceOptions
) {
  return useMutation({
    mutationFn: (source: InferenceData | TicketAnalysisSource) => {
      if (source && 'ticketData' in source) {
        const { ticketRefs, ticketData } = source as TicketAnalysisSource;
        return apiService.infer(toValue(instanceId), ticketData, ticketRefs);
      }
      return apiService.infer(toValue(instanceId), source as InferenceData);
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
    meta: options?.meta,
  });
}

/**
 * Inference hook with custom error handling for "model not trained" case.
 *
 * @example
 * ```ts
 * const { mutate: infer, isPending } = useInferWithModelCheck(instanceId, {
 *   onModelNotTrained: () => router.push('/training'),
 * });
 * ```
 */
export function useInferWithModelCheck(
  instanceId: MaybeRef<number>,
  options?: UseInferenceOptions & {
    onModelNotTrained?: () => void;
  }
) {
  return useMutation({
    mutationFn: (source: InferenceData | TicketAnalysisSource) => {
      if (source && 'ticketData' in source) {
        const { ticketRefs, ticketData } = source as TicketAnalysisSource;
        return apiService.infer(toValue(instanceId), ticketData, ticketRefs);
      }
      return apiService.infer(toValue(instanceId), source as InferenceData);
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
    meta: {
      ...options?.meta,
      onSpecificError: (error: Error) => {
        if (error instanceof ApiError && /model not trained/i.test(error.detail)) {
          options?.onModelNotTrained?.();
          return true; // Prevent default error handling
        }
        return false;
      },
    },
  });
}

export interface UseInferTopKOptions {
  meta?: QueryMeta;
  onSuccess?: (data: InferenceTopKResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * Run top-K inference: returns the K highest-probability predicted classes.
 * Accepts either ad-hoc ticket data or a ticket ref source.
 * Silent by default — this is a supplementary feature used to surface
 * additional similar-ticket candidates for the labeler.
 */
export function useInferTopK(
  instanceId: MaybeRef<number>,
  topK: MaybeRef<number> = 2,
  options?: UseInferTopKOptions
) {
  return useMutation({
    mutationFn: (source: InferenceData | TicketAnalysisSource) => {
      if (source && 'ticketData' in source) {
        return apiService.inferTopK(toValue(instanceId), source, toValue(topK));
      }
      return apiService.inferTopK(toValue(instanceId), { ticketData: source as InferenceData }, toValue(topK));
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
    meta: {
      silent: true,
      ...options?.meta,
    },
  });
}
