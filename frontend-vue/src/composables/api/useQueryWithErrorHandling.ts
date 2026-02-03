import { useQuery, type UseQueryOptions, type UseQueryReturnType } from '@tanstack/vue-query';
import { watch } from 'vue';
import { toast } from 'vue-sonner';
import { ApiError } from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

/**
 * Error message mapping for common HTTP status codes.
 */
const DEFAULT_ERROR_MESSAGES: Record<number, string> = {
  0: 'Network error. Please check your connection.',
  400: 'Invalid request. Please check your input.',
  401: 'You are not authorized. Please log in.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  409: 'Conflict. The resource may have been modified.',
  422: 'Validation error. Please check your input.',
  429: 'Too many requests. Please try again later.',
  500: 'Server error. Please try again later.',
  502: 'Bad gateway. The server is temporarily unavailable.',
  503: 'Service unavailable. Please try again later.',
};

/**
 * Known error patterns that should have specialized handling.
 */
const KNOWN_ERROR_PATTERNS: Array<{ pattern: RegExp; message: string }> = [
  { pattern: /model not trained/i, message: 'Model not trained yet. Please train the model first.' },
  { pattern: /instance not found/i, message: 'Instance not found. It may have been deleted.' },
  { pattern: /no classes/i, message: 'No classes defined. Please configure classes first.' },
];

/**
 * Handle API errors with toast notifications.
 */
export function handleQueryError(error: unknown, meta?: QueryMeta): void {
  if (meta?.silent) {
    return;
  }

  if (!(error instanceof ApiError)) {
    console.error('Unexpected error type:', error);
    toast.error('Error', { description: 'An unexpected error occurred.' });
    return;
  }

  if (meta?.onSpecificError?.(error)) {
    return;
  }

  for (const { pattern, message } of KNOWN_ERROR_PATTERNS) {
    if (pattern.test(error.detail)) {
      toast.error(meta?.errorTitle ?? 'Error', { description: message });
      return;
    }
  }

  const customMessages = meta?.errorMessages ?? {};
  const message =
    customMessages[error.statusCode] ??
    DEFAULT_ERROR_MESSAGES[error.statusCode] ??
    error.detail;

  toast.error(meta?.errorTitle ?? 'Error', { description: message });
}

/**
 * Extended query options with error handling meta.
 */
export type UseQueryWithErrorHandlingOptions<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
> = UseQueryOptions<TQueryFnData, TError, TData> & {
  meta?: QueryMeta;
};

/**
 * Wrapper around useQuery that adds global error handling via toast notifications.
 * 
 * @example
 * ```ts
 * // Basic usage - errors show toast automatically
 * const { data, isLoading } = useQueryWithErrorHandling({
 *   queryKey: ['models'],
 *   queryFn: () => apiService.getModels(),
 * });
 * 
 * // Silent mode - no toast on error
 * const { data } = useQueryWithErrorHandling({
 *   queryKey: ['models'],
 *   queryFn: () => apiService.getModels(),
 *   meta: { silent: true },
 * });
 * 
 * // Custom error message
 * const { data } = useQueryWithErrorHandling({
 *   queryKey: ['models'],
 *   queryFn: () => apiService.getModels(),
 *   meta: { errorMessages: { 404: 'No models configured yet.' } },
 * });
 * ```
 */
export function useQueryWithErrorHandling<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
>(
  options: UseQueryWithErrorHandlingOptions<TQueryFnData, TError, TData>
): UseQueryReturnType<TData, TError> {
  const query = useQuery(options);

  // Watch for errors and handle them with toast
  watch(
    () => query.error.value,
    (error) => {
      if (error) {
        handleQueryError(error, options.meta);
      }
    },
    { immediate: true }
  );

  return query;
}
