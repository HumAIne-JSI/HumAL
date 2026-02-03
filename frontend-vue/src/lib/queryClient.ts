import { QueryClient, type QueryClientConfig } from '@tanstack/vue-query';
import { toast } from 'vue-sonner';
import { ApiError } from '@/types/api';

/**
 * Error message mapping for common HTTP status codes.
 * Can be overridden per-query using meta.errorMessages.
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
 * Maps error detail patterns to user-friendly messages.
 */
const KNOWN_ERROR_PATTERNS: Array<{ pattern: RegExp; message: string }> = [
  { pattern: /model not trained/i, message: 'Model not trained yet. Please train the model first.' },
  { pattern: /instance not found/i, message: 'Instance not found. It may have been deleted.' },
  { pattern: /no classes/i, message: 'No classes defined. Please configure classes first.' },
];

/**
 * Custom meta options for error handling.
 * Uses index signature to be compatible with Vue Query's Record<string, unknown> requirement.
 */
export interface QueryMeta extends Record<string, unknown> {
  /** Skip global error handler for this query/mutation */
  silent?: boolean;
  /** Custom error messages by status code */
  errorMessages?: Record<number, string>;
  /** Custom error title (default: "Error") */
  errorTitle?: string;
  /** Custom handler for specific error patterns. Return true to prevent default handling. */
  onSpecificError?: (error: ApiError) => boolean;
}

/**
 * Global error handler for Vue Query.
 * Shows toast notifications for errors unless suppressed via meta.
 */
function handleError(error: unknown, meta?: QueryMeta): void {
  // If silent mode is enabled, skip error handling
  if (meta?.silent) {
    return;
  }

  // Only handle ApiError instances
  if (!(error instanceof ApiError)) {
    console.error('Unexpected error type:', error);
    toast.error('Error', { description: 'An unexpected error occurred.' });
    return;
  }

  // Allow custom handler to intercept specific errors
  if (meta?.onSpecificError?.(error)) {
    return; // Custom handler took care of it
  }

  // Check for known error patterns
  for (const { pattern, message } of KNOWN_ERROR_PATTERNS) {
    if (pattern.test(error.detail)) {
      toast.error(meta?.errorTitle ?? 'Error', { description: message });
      return;
    }
  }

  // Get error message from custom mapping, default mapping, or error detail
  const customMessages = meta?.errorMessages ?? {};
  const message =
    customMessages[error.statusCode] ??
    DEFAULT_ERROR_MESSAGES[error.statusCode] ??
    error.detail;

  toast.error(meta?.errorTitle ?? 'Error', { description: message });
}

/**
 * Creates the Vue Query client with global error handling.
 */
export function createQueryClient(config?: Partial<QueryClientConfig>): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Don't retry on 4xx errors (client errors)
        retry: (failureCount, error) => {
          if (error instanceof ApiError && error.isClientError()) {
            return false;
          }
          return failureCount < 3;
        },
        // Stale time of 30 seconds by default
        staleTime: 30 * 1000,
        // Don't refetch on window focus by default (can be overridden per-query)
        refetchOnWindowFocus: false,
      },
      mutations: {
        // Never retry mutations
        retry: false,
        // Global error handler for mutations
        onError: (error, _variables, _context, mutation) => {
          handleError(error, mutation.meta as QueryMeta);
        },
      },
    },
    ...config,
  });
}

/**
 * Default query client instance.
 * The global error handler for queries must be set up in each composable
 * using the onError option, since Vue Query doesn't support global query error handlers
 * in the same way as mutations.
 */
export const queryClient = createQueryClient();

/**
 * Helper to create query options with error handling.
 * Use this when you want the global error handler to apply to queries.
 */
export function withErrorHandling<T>(
  options: T & { meta?: QueryMeta }
): T & { meta: QueryMeta } {
  return {
    ...options,
    meta: {
      ...options.meta,
    },
  };
}

// Re-export for convenience
export { ApiError };
export type { QueryMeta as ErrorHandlingMeta };
