import { useQuery } from '@tanstack/vue-query';
import { computed, type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import type {
  TicketsResponse,
  TeamsResponse,
  CategoriesResponse,
  SubcategoriesResponse,
} from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

// Query keys for data domain
export const dataKeys = {
  all: ['data'] as const,
  tickets: (instanceId: number, indices: string[], trainDataPath?: string) =>
    [...dataKeys.all, 'tickets', instanceId, indices, trainDataPath] as const,
  teams: (instanceId: number, trainDataPath?: string) =>
    [...dataKeys.all, 'teams', instanceId, trainDataPath] as const,
  categories: (instanceId: number, trainDataPath?: string) =>
    [...dataKeys.all, 'categories', instanceId, trainDataPath] as const,
  subcategories: (instanceId: number, trainDataPath?: string) =>
    [...dataKeys.all, 'subcategories', instanceId, trainDataPath] as const,
};

export interface UseDataOptions {
  meta?: QueryMeta;
  enabled?: MaybeRef<boolean>;
}

/**
 * Fetch tickets by indices.
 * 
 * @example
 * ```ts
 * const { data: tickets } = useTickets(instanceId, ['1', '2', '3']);
 * // tickets.value?.tickets is Ticket[]
 * ```
 */
export function useTickets(
  instanceId: MaybeRef<number>,
  indices: MaybeRef<string[]>,
  trainDataPath?: MaybeRef<string | undefined>,
  options?: UseDataOptions
) {
  return useQuery({
    queryKey: computed(() =>
      dataKeys.tickets(toValue(instanceId), toValue(indices), toValue(trainDataPath))
    ),
    queryFn: () =>
      apiService.getTickets(toValue(instanceId), toValue(indices), toValue(trainDataPath)),
    enabled: computed(() => {
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      const idx = toValue(indices);
      return enabled && idx.length > 0;
    }),
    ...options,
  });
}

/**
 * Fetch available teams.
 * 
 * @example
 * ```ts
 * const { data: teams } = useTeams(instanceId);
 * // teams.value?.teams is string[]
 * ```
 */
export function useTeams(
  instanceId: MaybeRef<number> = 0,
  trainDataPath?: MaybeRef<string | undefined>,
  options?: UseDataOptions
) {
  return useQuery({
    queryKey: computed(() => dataKeys.teams(toValue(instanceId), toValue(trainDataPath))),
    queryFn: () => apiService.getTeams(toValue(instanceId), toValue(trainDataPath)),
    // Teams rarely change - cache for 5 minutes
    staleTime: 5 * 60 * 1000,
    enabled: options?.enabled,
    ...options,
  });
}

/**
 * Fetch available categories (service names).
 * 
 * @example
 * ```ts
 * const { data: categories } = useCategories(instanceId);
 * // categories.value?.categories is string[]
 * ```
 */
export function useCategories(
  instanceId: MaybeRef<number> = 0,
  trainDataPath?: MaybeRef<string | undefined>,
  options?: UseDataOptions
) {
  return useQuery({
    queryKey: computed(() => dataKeys.categories(toValue(instanceId), toValue(trainDataPath))),
    queryFn: () => apiService.getCategories(toValue(instanceId), toValue(trainDataPath)),
    // Categories rarely change - cache for 5 minutes
    staleTime: 5 * 60 * 1000,
    enabled: options?.enabled,
    ...options,
  });
}

/**
 * Fetch available subcategories.
 * 
 * @example
 * ```ts
 * const { data: subcategories } = useSubcategories(instanceId);
 * // subcategories.value?.subcategories is string[]
 * ```
 */
export function useSubcategories(
  instanceId: MaybeRef<number> = 0,
  trainDataPath?: MaybeRef<string | undefined>,
  options?: UseDataOptions
) {
  return useQuery({
    queryKey: computed(() => dataKeys.subcategories(toValue(instanceId), toValue(trainDataPath))),
    queryFn: () => apiService.getSubcategories(toValue(instanceId), toValue(trainDataPath)),
    // Subcategories rarely change - cache for 5 minutes
    staleTime: 5 * 60 * 1000,
    enabled: options?.enabled,
    ...options,
  });
}

/**
 * Convenience hook to fetch all reference data at once.
 * 
 * @example
 * ```ts
 * const { teams, categories, subcategories, isLoading } = useReferenceData(instanceId);
 * ```
 */
export function useReferenceData(
  instanceId: MaybeRef<number> = 0,
  trainDataPath?: MaybeRef<string | undefined>,
  options?: UseDataOptions
) {
  const teamsQuery = useTeams(instanceId, trainDataPath, options);
  const categoriesQuery = useCategories(instanceId, trainDataPath, options);
  const subcategoriesQuery = useSubcategories(instanceId, trainDataPath, options);

  return {
    teams: teamsQuery.data,
    categories: categoriesQuery.data,
    subcategories: subcategoriesQuery.data,
    teamsQuery,
    categoriesQuery,
    subcategoriesQuery,
    isLoading: computed(
      () =>
        teamsQuery.isLoading.value ||
        categoriesQuery.isLoading.value ||
        subcategoriesQuery.isLoading.value
    ),
    isError: computed(
      () =>
        teamsQuery.isError.value ||
        categoriesQuery.isError.value ||
        subcategoriesQuery.isError.value
    ),
  };
}
