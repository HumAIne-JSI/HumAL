/**
 * Analytics composables — Vue Query wrappers for the benchmark-suite endpoints.
 */
import { useQuery } from '@tanstack/vue-query';
import { computed, ref, type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import type {
  BenchmarkOverview,
  BenchmarkSession,
  BenchmarkSessionSummary,
} from '@/types/api';
import {
  sampleBenchmarkSession,
  sampleSessionSummary,
  sampleOverview,
} from '@/data/sampleAnalytics';

// ----- Sample-data toggle -----
export const useSampleData = ref(true);
export function setUseSampleData(value: boolean) {
  useSampleData.value = value;
}

// ----- Query keys -----
export const analyticsKeys = {
  all: ['analytics'] as const,
  overview: () => [...analyticsKeys.all, 'overview'] as const,
  sessions: () => [...analyticsKeys.all, 'sessions'] as const,
  session: (simId: string) => [...analyticsKeys.all, 'session', simId] as const,
};

interface Options {
  enabled?: MaybeRef<boolean>;
}

export function useAnalyticsOverview(options?: Options) {
  return useQuery<BenchmarkOverview>({
    queryKey: analyticsKeys.overview(),
    queryFn: () => {
      if (useSampleData.value) return Promise.resolve(sampleOverview);
      return apiService.getAnalyticsOverview();
    },
    ...options,
  });
}

export function useSessions(options?: Options) {
  return useQuery<BenchmarkSessionSummary[]>({
    queryKey: analyticsKeys.sessions(),
    queryFn: () => {
      if (useSampleData.value) return Promise.resolve([sampleSessionSummary]);
      return apiService.getSessions();
    },
    ...options,
  });
}

export function useSession(simId: MaybeRef<string>, options?: Options) {
  return useQuery<BenchmarkSession>({
    queryKey: computed(() => analyticsKeys.session(toValue(simId))),
    queryFn: () => {
      if (useSampleData.value) return Promise.resolve(sampleBenchmarkSession);
      return apiService.getSession(toValue(simId));
    },
    enabled: computed(() => {
      const id = toValue(simId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && !!id;
    }),
  });
}
