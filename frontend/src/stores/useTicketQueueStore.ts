import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

// Ticket status for queue filtering
export type TicketStatus = 'unlabeled' | 'pending-review' | 'auto-classified' | 'resolved'

// Sort options for queue
export type SortOrder = 'newest' | 'oldest' | 'confidence-high' | 'confidence-low'

// Queue ticket with enriched data
export interface QueueTicket {
  id: string
  ref: string
  title: string
  description: string
  team?: string
  category?: string
  subcategory?: string
  status: TicketStatus
  confidence?: number
  prediction?: string
  timestamp: Date
  // Original ticket data for API calls
  originalData?: Record<string, unknown>
}

// Filter configuration
export interface QueueFilters {
  status: TicketStatus | 'all'
  search: string
  team: string | null
  sortOrder: SortOrder
}

const STORAGE_KEY_FILTERS = 'humal-queue-filters'

const defaultFilters: QueueFilters = {
  status: 'all',
  search: '',
  team: null,
  sortOrder: 'newest',
}

export const useTicketQueueStore = defineStore('ticketQueue', () => {
  // State
  const tickets = ref<QueueTicket[]>([])
  const selectedTicketId = ref<string | null>(null)
  const bulkSelection = ref<Set<string>>(new Set())
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Load filters from localStorage
  const storedFilters = localStorage.getItem(STORAGE_KEY_FILTERS)
  const filters = ref<QueueFilters>(
    storedFilters ? { ...defaultFilters, ...JSON.parse(storedFilters) } : { ...defaultFilters }
  )

  // Computed
  const selectedTicket = computed(() =>
    tickets.value.find((t) => t.id === selectedTicketId.value) ?? null
  )

  const filteredTickets = computed(() => {
    let result = [...tickets.value]

    // Filter by status
    if (filters.value.status !== 'all') {
      result = result.filter((t) => t.status === filters.value.status)
    }

    // Filter by team
    if (filters.value.team) {
      result = result.filter((t) => t.team === filters.value.team)
    }

    // Filter by search
    if (filters.value.search.trim()) {
      const searchLower = filters.value.search.toLowerCase()
      result = result.filter(
        (t) =>
          t.title.toLowerCase().includes(searchLower) ||
          t.description.toLowerCase().includes(searchLower) ||
          t.ref.toLowerCase().includes(searchLower)
      )
    }

    // Sort
    switch (filters.value.sortOrder) {
      case 'newest':
        result.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
        break
      case 'oldest':
        result.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
        break
      case 'confidence-high':
        result.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
        break
      case 'confidence-low':
        result.sort((a, b) => (a.confidence ?? 0) - (b.confidence ?? 0))
        break
    }

    return result
  })

  const statusCounts = computed(() => {
    const counts: Record<TicketStatus | 'all', number> = {
      all: tickets.value.length,
      unlabeled: 0,
      'pending-review': 0,
      'auto-classified': 0,
      resolved: 0,
    }
    for (const ticket of tickets.value) {
      counts[ticket.status]++
    }
    return counts
  })

  const selectedIndex = computed(() => {
    if (!selectedTicketId.value) return -1
    return filteredTickets.value.findIndex((t) => t.id === selectedTicketId.value)
  })

  const hasBulkSelection = computed(() => bulkSelection.value.size > 0)

  const bulkSelectedTickets = computed(() =>
    tickets.value.filter((t) => bulkSelection.value.has(t.id))
  )

  // Actions
  function setTickets(newTickets: QueueTicket[]) {
    tickets.value = newTickets
    // Clear selection if selected ticket no longer exists
    if (selectedTicketId.value && !newTickets.find((t) => t.id === selectedTicketId.value)) {
      selectedTicketId.value = null
    }
    // Clean bulk selection
    const ticketIds = new Set(newTickets.map((t) => t.id))
    bulkSelection.value = new Set([...bulkSelection.value].filter((id) => ticketIds.has(id)))
  }

  function selectTicket(id: string | null) {
    selectedTicketId.value = id
  }

  function selectNext(): boolean {
    const filtered = filteredTickets.value
    if (filtered.length === 0) return false

    const currentIndex = selectedIndex.value
    if (currentIndex === -1) {
      const first = filtered[0]
      if (first) selectedTicketId.value = first.id
    } else if (currentIndex < filtered.length - 1) {
      const next = filtered[currentIndex + 1]
      if (next) selectedTicketId.value = next.id
    } else {
      return false // At end of list
    }
    return true
  }

  function selectPrevious(): boolean {
    const filtered = filteredTickets.value
    if (filtered.length === 0) return false

    const currentIndex = selectedIndex.value
    if (currentIndex === -1) {
      const last = filtered[filtered.length - 1]
      if (last) selectedTicketId.value = last.id
    } else if (currentIndex > 0) {
      const prev = filtered[currentIndex - 1]
      if (prev) selectedTicketId.value = prev.id
    } else {
      return false // At start of list
    }
    return true
  }

  function toggleBulkSelect(id: string) {
    if (bulkSelection.value.has(id)) {
      bulkSelection.value.delete(id)
    } else {
      bulkSelection.value.add(id)
    }
    // Trigger reactivity
    bulkSelection.value = new Set(bulkSelection.value)
  }

  function selectAllVisible() {
    for (const ticket of filteredTickets.value) {
      bulkSelection.value.add(ticket.id)
    }
    bulkSelection.value = new Set(bulkSelection.value)
  }

  function clearBulkSelection() {
    bulkSelection.value = new Set()
  }

  function updateTicketStatus(id: string, status: TicketStatus) {
    const ticket = tickets.value.find((t) => t.id === id)
    if (ticket) {
      ticket.status = status
    }
  }

  function updateTicketPrediction(id: string, prediction: string, confidence: number) {
    const ticket = tickets.value.find((t) => t.id === id)
    if (ticket) {
      ticket.prediction = prediction
      ticket.confidence = confidence
      // Auto-classified if confidence is high
      if (confidence >= 0.8 && ticket.status === 'unlabeled') {
        ticket.status = 'auto-classified'
      }
    }
  }

  function setFilter<K extends keyof QueueFilters>(key: K, value: QueueFilters[K]) {
    filters.value[key] = value
    persistFilters()
  }

  function resetFilters() {
    filters.value = { ...defaultFilters }
    persistFilters()
  }

  function persistFilters() {
    localStorage.setItem(STORAGE_KEY_FILTERS, JSON.stringify(filters.value))
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function setError(err: string | null) {
    error.value = err
  }

  return {
    // State
    tickets,
    selectedTicketId,
    bulkSelection,
    filters,
    isLoading,
    error,

    // Computed
    selectedTicket,
    filteredTickets,
    statusCounts,
    selectedIndex,
    hasBulkSelection,
    bulkSelectedTickets,

    // Actions
    setTickets,
    selectTicket,
    selectNext,
    selectPrevious,
    toggleBulkSelect,
    selectAllVisible,
    clearBulkSelection,
    updateTicketStatus,
    updateTicketPrediction,
    setFilter,
    resetFilters,
    setLoading,
    setError,
  }
})
