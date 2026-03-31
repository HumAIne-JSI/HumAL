/**
 * Analytics API composable - Vue Query wrappers for analytics endpoints.
 * Provides reactive data fetching with automatic error handling.
 * Includes sample data fallback for prototyping.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { computed, ref, type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import type {
  AnalyticsOverview,
  SessionSummary,
  SessionLog,
  LabelingMetrics,
  ModelPerformanceMetrics,
  ALEffectivenessMetrics,
  ClassDistributionMetrics,
  SessionComparison,
  ExportRequest,
  ExportResponse,
} from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

// Sample data imports for prototyping mode
import {
  sampleAnalyticsOverview,
  sampleSessionSummary,
  sampleSessionLog,
  sampleLabelingMetrics,
  sampleModelPerformanceMetrics,
  sampleALEffectivenessMetrics,
  sampleClassDistributionMetrics,
} from '@/data/sampleAnalytics';

// ============================================================================
// Configuration
// ============================================================================

/** Toggle to use sample data instead of API calls */
export const useSampleData = ref(true);

/** Set whether to use sample data or API */
export function setUseSampleData(value: boolean) {
  useSampleData.value = value;
}

// ============================================================================
// Query Keys
// ============================================================================

export const analyticsKeys = {
  all: ['analytics'] as const,
  overview: () => [...analyticsKeys.all, 'overview'] as const,
  sessions: () => [...analyticsKeys.all, 'sessions'] as const,
  session: (id: string) => [...analyticsKeys.all, 'session', id] as const,
  decisions: (id: string) => [...analyticsKeys.session(id), 'decisions'] as const,
  labeling: (id: string) => [...analyticsKeys.session(id), 'labeling'] as const,
  performance: (id: string) => [...analyticsKeys.session(id), 'performance'] as const,
  effectiveness: (id: string) => [...analyticsKeys.session(id), 'effectiveness'] as const,
  distribution: (id: string) => [...analyticsKeys.session(id), 'distribution'] as const,
  comparison: (ids: string[]) => [...analyticsKeys.all, 'comparison', ids.join(',')] as const,
};

// ============================================================================
// Query Options Interface
// ============================================================================

export interface UseAnalyticsOptions {
  meta?: QueryMeta;
  enabled?: MaybeRef<boolean>;
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch analytics overview (aggregated stats across all sessions).
 * 
 * @example
 * ```ts
 * const { data: overview, isLoading } = useAnalyticsOverview();
 * ```
 */
export function useAnalyticsOverview(options?: UseAnalyticsOptions) {
  return useQuery({
    queryKey: analyticsKeys.overview(),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(sampleAnalyticsOverview);
      }
      return apiService.getAnalyticsOverview();
    },
    ...options,
  });
}

/**
 * Fetch list of all sessions with summary stats.
 * 
 * @example
 * ```ts
 * const { data: sessions, isLoading } = useSessions();
 * ```
 */
export function useSessions(options?: UseAnalyticsOptions) {
  return useQuery({
    queryKey: analyticsKeys.sessions(),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve([sampleSessionSummary]);
      }
      return apiService.getSessions();
    },
    ...options,
  });
}

/**
 * Fetch session summary by ID.
 * 
 * @example
 * ```ts
 * const { data: session } = useSession(sessionId);
 * ```
 */
export function useSession(
  sessionId: MaybeRef<string>,
  options?: UseAnalyticsOptions
) {
  return useQuery({
    queryKey: computed(() => analyticsKeys.session(toValue(sessionId))),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(sampleSessionSummary);
      }
      return apiService.getSession(toValue(sessionId));
    },
    enabled: computed(() => {
      const id = toValue(sessionId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && !!id;
    }),
    ...options,
  });
}

/**
 * Fetch full decision log for a session.
 * 
 * @example
 * ```ts
 * const { data: log } = useSessionDecisions(sessionId);
 * // log.value?.decisions is Decision[]
 * ```
 */
export function useSessionDecisions(
  sessionId: MaybeRef<string>,
  options?: UseAnalyticsOptions
) {
  return useQuery({
    queryKey: computed(() => analyticsKeys.decisions(toValue(sessionId))),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(sampleSessionLog);
      }
      return apiService.getSessionDecisions(toValue(sessionId));
    },
    enabled: computed(() => {
      const id = toValue(sessionId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && !!id;
    }),
    ...options,
  });
}

/**
 * Fetch labeling metrics for a session.
 */
export function useSessionLabeling(
  sessionId: MaybeRef<string>,
  options?: UseAnalyticsOptions
) {
  return useQuery({
    queryKey: computed(() => analyticsKeys.labeling(toValue(sessionId))),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(sampleLabelingMetrics);
      }
      return apiService.getSessionLabeling(toValue(sessionId));
    },
    enabled: computed(() => {
      const id = toValue(sessionId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && !!id;
    }),
    ...options,
  });
}

/**
 * Fetch model performance metrics for a session.
 */
export function useSessionPerformance(
  sessionId: MaybeRef<string>,
  options?: UseAnalyticsOptions
) {
  return useQuery({
    queryKey: computed(() => analyticsKeys.performance(toValue(sessionId))),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(sampleModelPerformanceMetrics);
      }
      return apiService.getSessionPerformance(toValue(sessionId));
    },
    enabled: computed(() => {
      const id = toValue(sessionId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && !!id;
    }),
    ...options,
  });
}

/**
 * Fetch AL effectiveness metrics for a session.
 */
export function useSessionEffectiveness(
  sessionId: MaybeRef<string>,
  options?: UseAnalyticsOptions
) {
  return useQuery({
    queryKey: computed(() => analyticsKeys.effectiveness(toValue(sessionId))),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(sampleALEffectivenessMetrics);
      }
      return apiService.getSessionEffectiveness(toValue(sessionId));
    },
    enabled: computed(() => {
      const id = toValue(sessionId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && !!id;
    }),
    ...options,
  });
}

/**
 * Fetch class distribution metrics for a session.
 */
export function useSessionDistribution(
  sessionId: MaybeRef<string>,
  options?: UseAnalyticsOptions
) {
  return useQuery({
    queryKey: computed(() => analyticsKeys.distribution(toValue(sessionId))),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(sampleClassDistributionMetrics);
      }
      return apiService.getSessionDistribution(toValue(sessionId));
    },
    enabled: computed(() => {
      const id = toValue(sessionId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && !!id;
    }),
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Compare multiple sessions.
 * 
 * @example
 * ```ts
 * const { mutate: compare } = useCompareSessions();
 * compare(['session-1', 'session-2']);
 * ```
 */
export function useCompareSessions(options?: {
  onSuccess?: (data: SessionComparison) => void;
  onError?: (error: Error) => void;
}) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionIds: string[]) => {
      if (useSampleData.value) {
        // Return mock comparison for sample mode
        return Promise.resolve({
          session_ids: sessionIds,
          instance_ids: [1],
          f1_scores: { 1: [0.782] },
          num_labeled: { 1: [5] },
          strategies: { 1: 'entropy' },
          f1_ranking: [1],
          efficiency_ranking: [1],
        } as SessionComparison);
      }
      return apiService.compareSessions(sessionIds);
    },
    onSuccess: (data, variables) => {
      queryClient.setQueryData(analyticsKeys.comparison(variables), data);
      options?.onSuccess?.(data);
    },
    onError: options?.onError,
  });
}

/**
 * Export sessions data.
 * 
 * @example
 * ```ts
 * const { mutate: exportData } = useExportSessions();
 * exportData({ instance_ids: [1, 2], format: 'json' });
 * ```
 */
export function useExportSessions(options?: {
  onSuccess?: (data: ExportResponse) => void;
  onError?: (error: Error) => void;
}) {
  return useMutation({
    mutationFn: (request: ExportRequest) => {
      if (useSampleData.value) {
        // Return mock export for sample mode
        return Promise.resolve({
          data: { sessions: [sampleSessionLog] },
          format: request.format ?? 'json',
        } as ExportResponse);
      }
      return apiService.exportSessions(request);
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

// ============================================================================
// Convenience Hook - All Session Data
// ============================================================================

/**
 * Fetch all metrics for a session at once.
 * Useful for session detail views.
 */
export function useSessionAllMetrics(
  sessionId: MaybeRef<string>,
  options?: UseAnalyticsOptions
) {
  const enabled = computed(() => {
    const id = toValue(sessionId);
    const optEnabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
    return optEnabled && !!id;
  });

  const summary = useSession(sessionId, { ...options, enabled });
  const decisions = useSessionDecisions(sessionId, { ...options, enabled });
  const labeling = useSessionLabeling(sessionId, { ...options, enabled });
  const performance = useSessionPerformance(sessionId, { ...options, enabled });
  const effectiveness = useSessionEffectiveness(sessionId, { ...options, enabled });
  const distribution = useSessionDistribution(sessionId, { ...options, enabled });

  const isLoading = computed(() =>
    summary.isLoading.value ||
    decisions.isLoading.value ||
    labeling.isLoading.value ||
    performance.isLoading.value ||
    effectiveness.isLoading.value ||
    distribution.isLoading.value
  );

  return {
    summary,
    decisions,
    labeling,
    performance,
    effectiveness,
    distribution,
    isLoading,
  };
}
