import { useQuery } from '@tanstack/vue-query';
import { computed } from 'vue';
import { apiService } from '@/services/api';
import type { QueryMeta } from '@/lib/queryClient';

// Query keys for config domain
export const configKeys = {
  all: ['config'] as const,
  models: () => [...configKeys.all, 'models'] as const,
  strategies: () => [...configKeys.all, 'strategies'] as const,
  capabilities: () => [...configKeys.all, 'capabilities'] as const,
};

export interface UseConfigOptions {
  meta?: QueryMeta;
}

/**
 * Fetch available ML models.
 * 
 * @example
 * ```ts
 * const { data: models, isLoading } = useModels();
 * // models.value?.models is string[]
 * ```
 */
export function useModels(options?: UseConfigOptions) {
  return useQuery({
    queryKey: configKeys.models(),
    queryFn: () => apiService.getModels(),
    // Config data rarely changes - cache for 5 minutes
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Fetch available query strategies for active learning.
 * 
 * @example
 * ```ts
 * const { data: strategies, isLoading } = useQueryStrategies();
 * // strategies.value?.strategies is string[]
 * ```
 */
export function useQueryStrategies(options?: UseConfigOptions) {
  return useQuery({
    queryKey: configKeys.strategies(),
    queryFn: () => apiService.getQueryStrategies(),
    // Config data rarely changes - cache for 5 minutes
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Fetch backend capabilities flags. Used to feature-gate UI for features
 * whose backend endpoints are not always available (e.g. top-K inference and
 * per-class similar tickets). Labeler satisfaction flags are part of the
 * label-with-info decision endpoint and are not capability-gated.
 *
 * @example
 * ```ts
 * const { data: caps } = useCapabilities();
 * const topKEnabled = computed(() => caps.value?.capabilities?.includes('top_k_inference') ?? false);
 * ```
 */
export function useCapabilities(options?: UseConfigOptions) {
  return useQuery({
    queryKey: configKeys.capabilities(),
    queryFn: () => apiService.getCapabilities(),
    // Capabilities are static for a given backend build
    staleTime: 5 * 60 * 1000,
    ...options,
    // Silent — capabilities are a non-critical, supplementary signal
    meta: {
      silent: true,
      ...options?.meta,
    },
  });
}

/**
 * Convenience hook to fetch all config data at once.
 * 
 * @example
 * ```ts
 * const { models, strategies, isLoading } = useConfig();
 * ```
 */
export function useConfig(options?: UseConfigOptions) {
  const modelsQuery = useModels(options);
  const strategiesQuery = useQueryStrategies(options);

  return {
    models: modelsQuery.data,
    strategies: strategiesQuery.data,
    modelsQuery,
    strategiesQuery,
    isLoading: computed(() => modelsQuery.isLoading.value || strategiesQuery.isLoading.value),
    isError: computed(() => modelsQuery.isError.value || strategiesQuery.isError.value),
  };
}
