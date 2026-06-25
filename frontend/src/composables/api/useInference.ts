import { useMutation } from '@tanstack/vue-query';
import { type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import {
  ApiError,
  type InferenceData,
  type InferenceResponse,
  type InferenceTopKResponse,
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
 * 
 * @example
 * ```ts
 * const { mutate: infer, isPending, data: result } = useInfer(instanceId);
 * 
 * // Run inference
 * infer({
 *   title_anon: 'Cannot connect to VPN',
 *   description_anon: 'Getting timeout errors...',
 * });
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
    mutationFn: (data: InferenceData) => apiService.infer(toValue(instanceId), data),
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
    mutationFn: (data: InferenceData) => apiService.infer(toValue(instanceId), data),
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
 * Silent by default — this is a supplementary feature used to surface
 * additional similar-ticket candidates for the labeler.
 */
export function useInferTopK(
  instanceId: MaybeRef<number>,
  topK: MaybeRef<number> = 2,
  options?: UseInferTopKOptions
) {
  return useMutation({
    mutationFn: (data: InferenceData) =>
      apiService.inferTopK(toValue(instanceId), data, toValue(topK)),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
    meta: {
      silent: true,
      ...options?.meta,
    },
  });
}
