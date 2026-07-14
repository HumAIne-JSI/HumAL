/**
 * Analytics composables — the data layer behind the holistic Benchmarking
 * Suite (Analytics page).
 *
 * The suite evaluates three pillars (AFU):
 *   1. Model performance   — real metrics from GET /activelearning/{id}/info.
 *   2. Resource efficiency — AI latency + label budget + human effort.
 *   3. Human satisfaction  — acceptance / override / friction from telemetry.
 *
 * Pillars 2 & 3 (and all engagement views) are derived client-side from the
 * tracked telemetry event stream (useTelemetryStore). Events are scoped to the
 * current mode via `eventsForMode`, so mock shows demo/seed data and live shows
 * only real tracked interactions — the same aggregation pipeline in both.
 */
import { useQuery } from '@tanstack/vue-query';
import { computed, ref, type MaybeRef, toValue } from 'vue';
import { useTelemetryStore } from '@/stores/useTelemetryStore';
import { useMockModeStore } from '@/stores/useMockModeStore';
import { useInstanceInfo } from '@/composables/api/useActiveLearning';
import {
  aggregateOverview,
  aggregateAIImpact,
  aggregateXaiEngagement,
  aggregatePageEngagement,
  aggregateTicketHeatmap,
  aggregateTimeline,
  aggregateFunnel,
  deriveModelPerformance,
} from '@/composables/useUserBehaviorAggregator';
import type {
  InstanceInfo,
  UserBehaviorOverview,
  AIImpactMetrics,
  XAIEngagementMetrics,
  PageEngagementMetrics,
  TicketHeatmap,
  EventTimeline,
  FunnelMetrics,
} from '@/types/api';
import { sampleInstanceInfo } from '@/data/sampleAnalytics';

// ----- Mock/sample-data flag -----
// Mirrors the global Mock toggle (kept in sync by useMockModeStore). Retained
// as a named export because useMockModeStore imports setUseSampleData.
export const useSampleData = ref(true);
export function setUseSampleData(value: boolean) {
  useSampleData.value = value;
}

// ----- Query keys -----
export const analyticsKeys = {
  all: ['analytics'] as const,
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

function resolveInstanceId(instanceId?: MaybeRef<number | null>): number | null {
  const value = toValue(instanceId);
  return value && value > 0 ? value : null;
}

/** Telemetry events scoped to the current mode (mock demo vs live tracked). */
function useModeEvents() {
  const telemetryStore = useTelemetryStore();
  const mockStore = useMockModeStore();
  return computed(() => telemetryStore.eventsForMode(mockStore.mockEnabled));
}

// ----- Pillar 1: Model performance -----

/**
 * Model-performance data for the current instance.
 * Live: real metrics from GET /activelearning/{id}/info.
 * Mock: a representative sample so the pillar renders without a backend.
 */
export function useModelPerformance(instanceId: MaybeRef<number>) {
  const mockStore = useMockModeStore();
  const live = useInstanceInfo(instanceId, {
    enabled: computed(() => !mockStore.mockEnabled && toValue(instanceId) > 0),
  });

  const info = computed<InstanceInfo | undefined>(() =>
    mockStore.mockEnabled ? sampleInstanceInfo : live.data.value,
  );
  const summary = computed(() => deriveModelPerformance(info.value));
  const isLoading = computed(() => !mockStore.mockEnabled && live.isLoading.value);

  return { info, summary, isLoading };
}

// ----- Pillars 2 & 3 + engagement: telemetry-derived -----

export function useUserBehaviorOverview(instanceId?: MaybeRef<number | null>) {
  const events = useModeEvents();
  return useQuery<UserBehaviorOverview>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorOverview(resolveInstanceId(instanceId)),
      events.value.length,
    ]),
    queryFn: () =>
      Promise.resolve(aggregateOverview(events.value, resolveInstanceId(instanceId))),
  });
}

export function useUserBehaviorAIImpact(instanceId?: MaybeRef<number | null>) {
  const events = useModeEvents();
  return useQuery<AIImpactMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorAIImpact(resolveInstanceId(instanceId)),
      events.value.length,
    ]),
    queryFn: () =>
      Promise.resolve(aggregateAIImpact(events.value, resolveInstanceId(instanceId))),
  });
}

export function useUserBehaviorXaiEngagement(instanceId?: MaybeRef<number | null>) {
  const events = useModeEvents();
  return useQuery<XAIEngagementMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorXai(resolveInstanceId(instanceId)),
      events.value.length,
    ]),
    queryFn: () =>
      Promise.resolve(aggregateXaiEngagement(events.value, resolveInstanceId(instanceId))),
  });
}

export function useUserBehaviorPageEngagement(instanceId?: MaybeRef<number | null>) {
  const events = useModeEvents();
  return useQuery<PageEngagementMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorPage(resolveInstanceId(instanceId)),
      events.value.length,
    ]),
    queryFn: () =>
      Promise.resolve(aggregatePageEngagement(events.value, resolveInstanceId(instanceId))),
  });
}

export function useUserBehaviorTicketHeatmap(
  instanceId?: MaybeRef<number | null>,
  limit: MaybeRef<number> = 20,
) {
  const events = useModeEvents();
  return useQuery<TicketHeatmap>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorHeatmap(resolveInstanceId(instanceId), toValue(limit)),
      events.value.length,
    ]),
    queryFn: () =>
      Promise.resolve(
        aggregateTicketHeatmap(events.value, resolveInstanceId(instanceId), toValue(limit)),
      ),
  });
}

export function useUserBehaviorTimeline(
  instanceId?: MaybeRef<number | null>,
  binSeconds: MaybeRef<number> = 60,
) {
  const events = useModeEvents();
  return useQuery<EventTimeline>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorTimeline(resolveInstanceId(instanceId), toValue(binSeconds)),
      events.value.length,
    ]),
    queryFn: () =>
      Promise.resolve(
        aggregateTimeline(events.value, resolveInstanceId(instanceId), toValue(binSeconds)),
      ),
  });
}

export function useUserBehaviorFunnel(instanceId?: MaybeRef<number | null>) {
  const events = useModeEvents();
  return useQuery<FunnelMetrics>({
    queryKey: computed(() => [
      ...analyticsKeys.userBehaviorFunnel(resolveInstanceId(instanceId)),
      events.value.length,
    ]),
    queryFn: () =>
      Promise.resolve(aggregateFunnel(events.value, resolveInstanceId(instanceId))),
  });
}
