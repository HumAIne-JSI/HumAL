import { computed, ref, watch, type MaybeRef, toValue } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { apiService } from '@/services/api'
import { useTicketQueueStore, type QueueTicket, type TicketStatus } from '@/stores/useTicketQueueStore'
import { useLabeledTicketsStore } from '@/stores/useLabeledTicketsStore'
import { useMockData, generateMockTickets, getMockTeams } from '@/composables/useMockTickets'
import { activeLearningKeys } from '@/composables/api/useActiveLearning'
import type { Ticket, LabelRequest, LabelInfo, MostHelpfulFeature } from '@/types/api'

// Query keys for ticket queue
export const ticketQueueKeys = {
  all: ['ticketQueue'] as const,
  list: (instanceId: number) => [...ticketQueueKeys.all, 'list', instanceId] as const,
  detail: (instanceId: number, ticketId: string) =>
    [...ticketQueueKeys.all, 'detail', instanceId, ticketId] as const,
}

export interface UseTicketQueueOptions {
  /** Number of tickets to request per queue batch */
  initialCount?: number
  /** Instance ID for API calls */
  instanceId?: MaybeRef<number>
  /** Whether to auto-fetch on mount */
  autoFetch?: boolean
}

export interface QueueDecisionInput {
  ticketId: string
  /** Omit this only when iDontKnow is true. */
  label?: string | null
  /** Model's suggested class, for benchmark confirm/override telemetry. */
  prediction?: string | null
  /** Time the user spent on the decision, in milliseconds. */
  durationMs?: number | null
  explanation?: string | null
  mostHelpfulFeature?: MostHelpfulFeature | null
  /** Human-satisfaction signals persisted with the decision. */
  isTired?: boolean | null
  isDifficult?: boolean | null
  iDontKnow?: boolean | null
}

export type QueueRetireInput = Omit<QueueDecisionInput, 'label' | 'iDontKnow'>

export function buildQueueLabelInfo(
  input: QueueDecisionInput,
  endMs = Date.now(),
): LabelInfo {
  const isRetirement = input.iDontKnow === true
  if (!isRetirement && !input.label?.trim()) {
    throw new Error('A label is required unless I don\'t know is selected')
  }

  const startMs = input.durationMs != null ? endMs - input.durationMs : endMs
  return {
    ticket_id: input.ticketId,
    ...(input.label?.trim() ? { label: input.label } : {}),
    model_prediction: input.prediction ?? undefined,
    start_time: new Date(startMs).toISOString(),
    end_time: new Date(endMs).toISOString(),
    explanation: input.explanation ?? undefined,
    most_helpful_feature: input.mostHelpfulFeature ?? undefined,
    is_tired: input.isTired ?? undefined,
    is_difficult: input.isDifficult ?? undefined,
    i_dont_know: isRetirement ? true : undefined,
  }
}

/**
 * Convert API Ticket to QueueTicket format
 */
function apiTicketToQueueTicket(ticket: Ticket, index: number): QueueTicket {
  return {
    id: ticket.Ref || String(index),
    ref: ticket.Ref || String(index),
    title: ticket.Title_anon || 'Untitled Ticket',
    description: ticket.Description_anon || '',
    team: ticket['Team->Name'],
    category: ticket['Service->Name'],
    subcategory: ticket['Service subcategory->Name'],
    status: 'unlabeled', // Default status, will be updated based on labeling state
    timestamp: new Date(), // API doesn't provide timestamp, use current
    originalData: ticket,
  }
}

/**
 * Unified composable for fetching and managing ticket queue
 * Supports both real API and mock data fallback
 */
export function useTicketQueue(options: UseTicketQueueOptions = {}) {
  const { initialCount = 1, autoFetch = true } = options
  const instanceId = options.instanceId ?? ref(0)
  const store = useTicketQueueStore()
  const labeledStore = useLabeledTicketsStore()
  const queryClient = useQueryClient()

  // Use mock data flag
  const isMockMode = computed(() => useMockData.value || toValue(instanceId) === 0)

  // Mock data state
  const mockTickets = ref<QueueTicket[]>([])
  const mockLoaded = ref(false)

  // Load mock tickets
  function loadMockTickets() {
    if (!mockLoaded.value) {
      mockTickets.value = generateMockTickets(initialCount)
      mockLoaded.value = true
    }
    store.setTickets(mockTickets.value)
    return mockTickets.value
  }

  // Real API query - fetch ticket indices from active learning
  const ticketIndicesQuery = useQuery({
    queryKey: computed(() => ticketQueueKeys.list(toValue(instanceId))),
    queryFn: async () => {
      const id = toValue(instanceId)
      if (id <= 0) return { tickets: [] as QueueTicket[] }

      // First, get next instances to label (unlabeled tickets)
      const nextResponse = await apiService.getNextInstances(id, initialCount)
      const indices = nextResponse.query_idx.map(String)

      if (indices.length === 0) {
        return { tickets: [] as QueueTicket[] }
      }

      // Fetch ticket details
      const ticketsResponse = await apiService.getTickets(id, indices)
      const queueTickets = ticketsResponse.tickets.map((t, i) => apiTicketToQueueTicket(t, i))

      return { tickets: queueTickets }
    },
    enabled: computed(() => autoFetch && !isMockMode.value && toValue(instanceId) > 0),
    staleTime: 30 * 1000, // 30 seconds
  })

  // Sync API data to store
  watch(
    () => ticketIndicesQuery.data.value,
    (data) => {
      if (data?.tickets && !isMockMode.value) {
        store.setTickets(data.tickets)
      }
    },
    { immediate: true }
  )

  // Initialize mock data if in mock mode
  watch(
    isMockMode,
    (mock) => {
      if (mock && autoFetch) {
        loadMockTickets()
      }
    },
    { immediate: true }
  )

  // Record a labeled ticket into the persistent (cross-tab) store so the
  // Resolution feature can pull it in as the basis for a proposed solution.
  function recordLabeledTicket(ticketId: string, label: string, prediction: string | null) {
    const src = store.tickets.find((t) => t.id === ticketId)
    if (!src) return
    labeledStore.record({
      ref: src.ref,
      title: src.title,
      description: src.description,
      label,
      category: src.category,
      subcategory: src.subcategory,
      instanceId: toValue(instanceId) || null,
      prediction,
      mock: isMockMode.value,
    })
  }

  // Label-with-info mutation. It also handles label-less i-don't-know
  // retirements so both paths share timing, persistence, and invalidation.
  const labelMutation = useMutation({
    mutationFn: async (input: QueueDecisionInput) => {
      const info = buildQueueLabelInfo(input)
      const id = toValue(instanceId)
      if (id <= 0 || isMockMode.value) {
        // Mock mode - just update local state through onSuccess below.
        return { message: input.iDontKnow === true ? 'Mock ticket retired' : 'Mock label applied' }
      }

      // Live mode: submit via label-with-info so the human decision is captured
      // as a benchmark telemetry event (timing + model prediction + satisfaction
      // signals) in addition to persisting the label. This retrains + recomputes
      // metrics, so we must NOT also call labelInstance for the same ticket.
      return apiService.labelWithInfo(id, [info])
    },
    onSuccess: (_, variables) => {
      // A retired ticket has no user label and must not become a Resolution
      // source ticket. Normal labels retain the existing behavior.
      if (!variables.iDontKnow && variables.label) {
        recordLabeledTicket(variables.ticketId, variables.label, variables.prediction ?? null)
      }
      // Update ticket status in store
      store.updateTicketStatus(variables.ticketId, 'resolved')
      // Invalidate queries to refetch
      if (!isMockMode.value) {
        queryClient.invalidateQueries({ queryKey: ticketQueueKeys.list(toValue(instanceId)) })
        // Refresh dashboard instance counters (labeled count).
        queryClient.invalidateQueries({ queryKey: activeLearningKeys.instances() })
      }
    },
  })

  function retireTicket(input: QueueRetireInput): void {
    labelMutation.mutate({ ...input, iDontKnow: true })
  }

  function retireTicketAsync(input: QueueRetireInput) {
    return labelMutation.mutateAsync({ ...input, iDontKnow: true })
  }

  // Bulk label mutation
  const bulkLabelMutation = useMutation({
    mutationFn: async ({
      ticketIds,
      label,
    }: {
      ticketIds: string[]
      label: string
    }) => {
      const id = toValue(instanceId)
      if (id <= 0 || isMockMode.value) {
        // Mock mode - just update local state
        return { message: 'Mock bulk label applied', count: ticketIds.length }
      }

      const request: LabelRequest = {
        query_idx: ticketIds,
        labels: ticketIds.map(() => label),
      }
      return apiService.labelInstance(id, request)
    },
    onSuccess: (_, variables) => {
      // Update all ticket statuses in store
      for (const ticketId of variables.ticketIds) {
        recordLabeledTicket(ticketId, variables.label, null)
        store.updateTicketStatus(ticketId, 'resolved')
      }
      store.clearBulkSelection()
      // Invalidate queries to refetch
      if (!isMockMode.value) {
        queryClient.invalidateQueries({ queryKey: ticketQueueKeys.list(toValue(instanceId)) })
        // Refresh dashboard instance counters (labeled count).
        queryClient.invalidateQueries({ queryKey: activeLearningKeys.instances() })
      }
    },
  })

  // Refresh tickets
  async function refresh() {
    if (isMockMode.value) {
      mockLoaded.value = false
      loadMockTickets()
    } else {
      await ticketIndicesQuery.refetch()
    }
  }

  // Get teams (with mock fallback)
  const teamsQuery = useQuery({
    queryKey: ['teams', toValue(instanceId)],
    queryFn: async () => {
      const id = toValue(instanceId)
      if (id <= 0 || isMockMode.value) {
        return { teams: getMockTeams() }
      }
      return apiService.getTeams(id)
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  return {
    // Store access
    store,

    // Query state
    isLoading: computed(
      () => ticketIndicesQuery.isLoading.value || (isMockMode.value && !mockLoaded.value)
    ),
    isError: computed(() => ticketIndicesQuery.isError.value),
    error: computed(() => ticketIndicesQuery.error.value),
    isMockMode,

    // Data
    tickets: computed(() => store.filteredTickets),
    allTickets: computed(() => store.tickets),
    selectedTicket: computed(() => store.selectedTicket),
    teams: computed(() => teamsQuery.data.value?.teams ?? []),

    // Actions
    refresh,
    selectTicket: store.selectTicket,
    selectNext: store.selectNext,
    selectPrevious: store.selectPrevious,
    toggleBulkSelect: store.toggleBulkSelect,
    selectAllVisible: store.selectAllVisible,
    clearBulkSelection: store.clearBulkSelection,
    setFilter: store.setFilter,
    resetFilters: store.resetFilters,

    // Mutations
    labelTicket: labelMutation.mutate,
    labelTicketAsync: labelMutation.mutateAsync,
    retireTicket,
    retireTicketAsync,
    isLabeling: computed(() => labelMutation.isPending.value),

    bulkLabel: bulkLabelMutation.mutate,
    bulkLabelAsync: bulkLabelMutation.mutateAsync,
    isBulkLabeling: computed(() => bulkLabelMutation.isPending.value),

    // Filters
    filters: computed(() => store.filters),
    bulkSelection: computed(() => store.bulkSelection),
    hasBulkSelection: computed(() => store.hasBulkSelection),
    bulkSelectedTickets: computed(() => store.bulkSelectedTickets),
  }
}
