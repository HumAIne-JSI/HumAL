/**
 * Analytics composables — Vue Query wrappers for the benchmark-suite endpoints.
 */
import { useQuery } from '@tanstack/vue-query';
import { computed, ref, type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import { useTelemetryStore } from '@/stores/useTelemetryStore';
import {
  aggregateOverview,
  aggregateAIImpact,
  aggregateXaiEngagement,
  aggregatePageEngagement,
  aggregateTicketHeatmap,
  aggregateTimeline,
  aggregateFunnel,
} from '@/composables/useUserBehaviorAggregator';
import type {
  BenchmarkOverview,
  BenchmarkSession,
  BenchmarkSessionSummary,
  UserBehaviorOverview,
  AIImpactMetrics,
  XAIEngagementMetrics,
  PageEngagementMetrics,
  TicketHeatmap,
  EventTimeline,
  FunnelMetrics,
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
  userBehavior: () => [...analyticsKeys.all, 'user-behavior'] as const,
  userBehaviorOverview: (instanceId: number | null) =>
    [...analyticsKeys.userBehavior(), 'overview', instanceId] as const,
  userBehaviorAIImpact: (instanceId: number | null) =>
    [...analyticsKeys.userBehavior(), 'ai-impact', instanceId] as const,
  userBehaviorXai: (instanceId: number | null) =>
    [...analyticsKeys.userBehavior(), 'xai-engagement', instanceId] as const,
  userBehaviorPage: (instanceId: number | null) =>
    [...analyticsKeys.userBehavior(), 'page-engagement', instanceId] as const,
  userBehaviorHeatmap: (instanceId: number | null, limit: number) =>
    [...analyticsKeys.userBehavior(), 'ticket-heatmap', instanceId, limit] as const,
  userBehaviorTimeline: (instanceId: number | null, binSeconds: number) =>
    [...analyticsKeys.userBehavior(), 'timeline', instanceId, binSeconds] as const,
  userBehaviorFunnel: (instanceId: number | null) =>
    [...analyticsKeys.userBehavior(), 'funnel', instanceId] as const,
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

// ----- User-behavior composables -----

function resolveInstanceId(instanceId?: MaybeRef<number | null>): number | null {
  const value = toValue(instanceId);
  return value && value > 0 ? value : null;
}

export function useUserBehaviorOverview(instanceId?: MaybeRef<number | null>) {
  const telemetryStore = useTelemetryStore();
  return useQuery<UserBehaviorOverview>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorOverview(resolveInstanceId(instanceId)),
      useSampleData.value ? telemetryStore.events.length : 'live',
    ]),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(
          aggregateOverview(telemetryStore.events, resolveInstanceId(instanceId)),
        );
      }
      return apiService.getUserBehaviorOverview(resolveInstanceId(instanceId));
    },
  });
}

export function useUserBehaviorAIImpact(instanceId?: MaybeRef<number | null>) {
  const telemetryStore = useTelemetryStore();
  return useQuery<AIImpactMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorAIImpact(resolveInstanceId(instanceId)),
      useSampleData.value ? telemetryStore.events.length : 'live',
    ]),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(
          aggregateAIImpact(telemetryStore.events, resolveInstanceId(instanceId)),
        );
      }
      return apiService.getUserBehaviorAIImpact(resolveInstanceId(instanceId));
    },
  });
}

export function useUserBehaviorXaiEngagement(instanceId?: MaybeRef<number | null>) {
  const telemetryStore = useTelemetryStore();
  return useQuery<XAIEngagementMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorXai(resolveInstanceId(instanceId)),
      useSampleData.value ? telemetryStore.events.length : 'live',
    ]),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(
          aggregateXaiEngagement(telemetryStore.events, resolveInstanceId(instanceId)),
        );
      }
      return apiService.getUserBehaviorXaiEngagement(resolveInstanceId(instanceId));
    },
  });
}

export function useUserBehaviorPageEngagement(instanceId?: MaybeRef<number | null>) {
  const telemetryStore = useTelemetryStore();
  return useQuery<PageEngagementMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorPage(resolveInstanceId(instanceId)),
      useSampleData.value ? telemetryStore.events.length : 'live',
    ]),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(
          aggregatePageEngagement(telemetryStore.events, resolveInstanceId(instanceId)),
        );
      }
      return apiService.getUserBehaviorPageEngagement(resolveInstanceId(instanceId));
    },
  });
}

export function useUserBehaviorTicketHeatmap(
  instanceId?: MaybeRef<number | null>,
  limit: MaybeRef<number> = 20,
) {
  const telemetryStore = useTelemetryStore();
  return useQuery<TicketHeatmap>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorHeatmap(resolveInstanceId(instanceId), toValue(limit)),
      useSampleData.value ? telemetryStore.events.length : 'live',
    ]),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(
          aggregateTicketHeatmap(
            telemetryStore.events,
            resolveInstanceId(instanceId),
            toValue(limit),
          ),
        );
      }
      return apiService.getUserBehaviorTicketHeatmap(resolveInstanceId(instanceId), toValue(limit));
    },
  });
}

export function useUserBehaviorTimeline(
  instanceId?: MaybeRef<number | null>,
  binSeconds: MaybeRef<number> = 60,
) {
  const telemetryStore = useTelemetryStore();
  return useQuery<EventTimeline>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorTimeline(resolveInstanceId(instanceId), toValue(binSeconds)),
      useSampleData.value ? telemetryStore.events.length : 'live',
    ]),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(
          aggregateTimeline(
            telemetryStore.events,
            resolveInstanceId(instanceId),
            toValue(binSeconds),
          ),
        );
      }
      return apiService.getUserBehaviorTimeline(resolveInstanceId(instanceId), toValue(binSeconds));
    },
  });
}

export function useUserBehaviorFunnel(instanceId?: MaybeRef<number | null>) {
  const telemetryStore = useTelemetryStore();
  return useQuery<FunnelMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorFunnel(resolveInstanceId(instanceId)),
      useSampleData.value ? telemetryStore.events.length : 'live',
    ]),
    queryFn: () => {
      if (useSampleData.value) {
        return Promise.resolve(
          aggregateFunnel(telemetryStore.events, resolveInstanceId(instanceId)),
        );
      }
      return apiService.getUserBehaviorFunnel(resolveInstanceId(instanceId));
    },
  });
}
