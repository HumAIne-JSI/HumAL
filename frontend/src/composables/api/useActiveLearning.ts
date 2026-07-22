import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { computed, type MaybeRef, toValue } from 'vue';
import { apiService } from '@/services/api';
import { useMockModeStore } from '@/stores/useMockModeStore';
import type {
  NewInstanceRequest,
  LabelRequest,
  LabelInfo,
  CreateInstanceResponse,
  LabelInstanceResponse,
  LabelerFeedbackRequest,
  LabelerFeedbackResponse,
  InstanceInfo,
  InstancesListResponse,
} from '@/types/api';
import type { QueryMeta } from '@/lib/queryClient';

// Query keys for active learning domain
export const activeLearningKeys = {
  all: ['activelearning'] as const,
  instances: () => [...activeLearningKeys.all, 'instances'] as const,
  instance: (id: number) => [...activeLearningKeys.all, 'instance', id] as const,
  info: (id: number) => [...activeLearningKeys.instance(id), 'info'] as const,
  next: (id: number, batchSize: number) => [...activeLearningKeys.instance(id), 'next', batchSize] as const,
};

export interface UseActiveLearningOptions {
  meta?: QueryMeta;
}

/**
 * Fetch all active learning instances.
 * 
 * @example
 * ```ts
 * const { data, isLoading } = useInstances();
 * // data.value?.instances is Record<string, InstanceInfo>
 * ```
 */
export function useInstances(options?: UseActiveLearningOptions) {
  return useQuery({
    queryKey: activeLearningKeys.instances(),
    queryFn: () => apiService.getInstances(),
    ...options,
  });
}

/**
 * Fetch info for a specific instance.
 * 
 * @example
 * ```ts
 * const { data: info, isLoading } = useInstanceInfo(instanceId);
 * ```
 */
export function useInstanceInfo(
  instanceId: MaybeRef<number>,
  options?: UseActiveLearningOptions & { enabled?: MaybeRef<boolean> }
) {
  return useQuery({
    queryKey: computed(() => activeLearningKeys.info(toValue(instanceId))),
    queryFn: () => apiService.getInstanceInfo(toValue(instanceId)),
    enabled: computed(() => {
      const id = toValue(instanceId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && id > 0;
    }),
    ...options,
  });
}

/**
 * Fetch next instances to label (active learning query).
 * 
 * @example
 * ```ts
 * const { data, refetch } = useNextInstances(instanceId, 5);
 * // data.value?.query_idx is number[]
 * ```
 */
export function useNextInstances(
  instanceId: MaybeRef<number>,
  batchSize: MaybeRef<number> = 1,
  options?: UseActiveLearningOptions & { enabled?: MaybeRef<boolean> }
) {
  return useQuery({
    queryKey: computed(() => activeLearningKeys.next(toValue(instanceId), toValue(batchSize))),
    queryFn: () => apiService.getNextInstances(toValue(instanceId), toValue(batchSize)),
    enabled: computed(() => {
      const id = toValue(instanceId);
      const enabled = options?.enabled !== undefined ? toValue(options.enabled) : true;
      return enabled && id > 0;
    }),
    // Don't cache next instances - always fetch fresh
    staleTime: 0,
    ...options,
  });
}

/**
 * Create a new active learning instance.
 * 
 * @example
 * ```ts
 * const { mutate: createInstance, isPending } = useCreateInstance();
 * createInstance({ model_name: 'bert', ... });
 * ```
 */
export function useCreateInstance(options?: { meta?: QueryMeta; onSuccess?: (data: CreateInstanceResponse) => void }) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: NewInstanceRequest) => apiService.createInstance(data),
    onSuccess: (data) => {
      // Invalidate instances list to refetch
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.instances() });
      options?.onSuccess?.(data);
    },
    meta: options?.meta,
  });
}

/**
 * Label instances in the active learning loop.
 * 
 * @example
 * ```ts
 * const { mutate: label } = useLabelInstance(instanceId);
 * label({ query_idx: [1, 2], labels: ['TeamA', 'TeamB'] });
 * ```
 */
export function useLabelInstance(
  instanceId: MaybeRef<number>,
  options?: { meta?: QueryMeta; onSuccess?: (data: LabelInstanceResponse) => void; batchSize?: MaybeRef<number> }
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LabelRequest) => apiService.labelInstance(toValue(instanceId), data),
    onSuccess: (data) => {
      const id = toValue(instanceId);
      // Invalidate instance info and next instances
      // Use specific keys to avoid duplicate refetches from prefix matching
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.info(id) });
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.next(id, toValue(options?.batchSize ?? 1)) });
      // Refresh the instances list so dashboard counters (labeled count) update.
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.instances() });
      options?.onSuccess?.(data);
    },
    meta: options?.meta,
  });
}

/**
 * Label instances with full decision context (timing, model prediction,
 * explanation) via POST /activelearning/{id}/label-with-info. This is the
 * benchmark telemetry channel: it persists the label AND records the event.
 * It retrains + recomputes metrics, so do NOT also call useLabelInstance for
 * the same ticket. No-ops in mock mode (no backend round-trip).
 */
export function useLabelWithInfo(
  instanceId: MaybeRef<number>,
  options?: { meta?: QueryMeta; onSuccess?: () => void; batchSize?: MaybeRef<number> }
) {
  const queryClient = useQueryClient();
  const mockStore = useMockModeStore();

  return useMutation({
    mutationFn: (data: LabelInfo[]) => {
      const id = toValue(instanceId);
      if (mockStore.mockEnabled || id <= 0) {
        return Promise.resolve({ message: 'Mock label applied' });
      }
      return apiService.labelWithInfo(id, data);
    },
    onSuccess: () => {
      const id = toValue(instanceId);
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.info(id) });
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.next(id, toValue(options?.batchSize ?? 1)) });
      // Refresh the instances list so dashboard counters (labeled count) update.
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.instances() });
      options?.onSuccess?.();
    },
    meta: options?.meta,
  });
}

/**
 * 
 * @example
 * ```ts
 * const { mutate: saveModel } = useSaveModel(instanceId);
 * saveModel();
 * ```
 */
export function useSaveModel(
  instanceId: MaybeRef<number>,
  options?: { meta?: QueryMeta; onSuccess?: (data: { model_id?: number; message?: string }) => void }
) {
  return useMutation({
    mutationFn: () => apiService.saveModel(toValue(instanceId)),
    onSuccess: options?.onSuccess,
    meta: options?.meta,
  });
}

/**
 * Submit a labeler-feedback (skip-with-reason) event for the current ticket.
 * Does NOT submit a class label — the ticket remains in the unlabeled pool;
 * the backend records the reason for telemetry / future scheduling.
 *
 * @example
 * ```ts
 * const { mutate: sendFeedback } = useLabelerFeedbackMutation(instanceId);
 * sendFeedback({ query_idx: ticketIdx, feedback_type: 'I_DONT_KNOW' });
 * ```
 */
export function useLabelerFeedbackMutation(
  _instanceId: MaybeRef<number>,
  options?: { meta?: QueryMeta; onSuccess?: (data: LabelerFeedbackResponse) => void }
) {
  return useMutation({
    // The humaine-al-api backend has no labeler-feedback endpoint. Keep the
    // mutation so the UI (skip-with-reason) works and mock telemetry still
    // fires at the call site, but resolve locally instead of hitting a 404.
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    mutationFn: (_data: LabelerFeedbackRequest) =>
      Promise.resolve({ status: 'ok' } as unknown as LabelerFeedbackResponse),
    onSuccess: options?.onSuccess,
    meta: options?.meta,
  });
}

/**
 * Delete an active learning instance.
 * 
 * @example
 * ```ts
 * const { mutate: deleteInstance } = useDeleteInstance();
 * deleteInstance(instanceId);
 * ```
 */
export function useDeleteInstance(options?: { meta?: QueryMeta; onSuccess?: () => void }) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (instanceId: number) => apiService.deleteInstance(instanceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: activeLearningKeys.instances() });
      options?.onSuccess?.();
    },
    meta: options?.meta,
  });
}
