import { useMutation } from '@tanstack/vue-query';
import { apiService } from '@/services/api';
import type {
  ResolutionProcessRequest,
  ResolutionProcessResponse,
  ResolutionFeedbackRequest,
  ResolutionFeedbackResponse,
} from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

// Query keys for resolution domain
export const resolutionKeys = {
  all: ['resolution'] as const,
};

export interface UseResolutionOptions {
  meta?: QueryMeta;
}

/**
 * Process a ticket to get resolution suggestions (RAG-based).
 * 
 * @example
 * ```ts
 * const { mutate: processResolution, data: result, isPending } = useProcessResolution();
 * 
 * processResolution({
 *   ticket_title: 'Cannot access email',
 *   ticket_description: 'Outlook shows error...',
 *   service_category: 'Email',
 * });
 * 
 * // Access result
 * // result.value?.classification, result.value?.predicted_team
 * // result.value?.response, result.value?.similar_replies
 * ```
 */
export function useProcessResolution(
  options?: UseResolutionOptions & {
    onSuccess?: (data: ResolutionProcessResponse) => void;
  }
) {
  return useMutation({
    mutationFn: (data: ResolutionProcessRequest) => apiService.processResolution(data),
    onSuccess: options?.onSuccess,
    meta: options?.meta,
  });
}

/**
 * Send feedback on a resolution (adds to knowledge base).
 * 
 * @example
 * ```ts
 * const { mutate: sendFeedback, isPending } = useResolutionFeedback({
 *   onSuccess: (data) => {
 *     toast.success('Feedback saved', { description: data.message });
 *   },
 * });
 * 
 * sendFeedback({
 *   ticket_title: 'Cannot access email',
 *   ticket_description: 'Outlook shows error...',
 *   edited_response: 'The user-edited resolution text...',
 * });
 * ```
 */
export function useResolutionFeedback(
  options?: UseResolutionOptions & {
    onSuccess?: (data: ResolutionFeedbackResponse) => void;
  }
) {
  return useMutation({
    mutationFn: (data: ResolutionFeedbackRequest) => apiService.sendResolutionFeedback(data),
    onSuccess: options?.onSuccess,
    meta: options?.meta,
  });
}

/**
 * Convenience hook combining resolution process and feedback.
 * 
 * @example
 * ```ts
 * const { processResolution, sendFeedback, result, isProcessing, isSendingFeedback } = useResolution();
 * ```
 */
export function useResolution(options?: UseResolutionOptions) {
  const processQuery = useProcessResolution({ meta: options?.meta });
  const feedbackMutation = useResolutionFeedback({ meta: options?.meta });

  return {
    processResolution: processQuery.mutate,
    processResolutionAsync: processQuery.mutateAsync,
    sendFeedback: feedbackMutation.mutate,
    sendFeedbackAsync: feedbackMutation.mutateAsync,
    result: processQuery.data,
    feedbackResult: feedbackMutation.data,
    isProcessing: processQuery.isPending,
    isSendingFeedback: feedbackMutation.isPending,
    processError: processQuery.error,
    feedbackError: feedbackMutation.error,
  };
}
