import { ref } from 'vue'
import { defineStore } from 'pinia'

/**
 * A ticket that has been labeled (team assigned) in the queue, captured so the
 * (separate) Resolution tab can pull it in as the basis for a proposed solution.
 *
 * Persisted to localStorage so it survives reloads AND is shared across browser
 * tabs of the same origin — the Resolution feature opens in its own browser tab
 * with a fresh Pinia instance, so in-memory queue state is not available there.
 */
export interface LabeledTicket {
  ref: string
  title: string
  description: string
  /** The team the human assigned (the label). */
  label: string
  category?: string
  subcategory?: string
  instanceId: number | null
  /** The model's suggested class at labeling time, if any. */
  prediction?: string | null
  /** Whether this was labeled against mock data. */
  mock: boolean
  /** ISO timestamp of when the label was applied. */
  timestamp: string
}

const STORAGE_KEY = 'humal-labeled-tickets'
const MAX_ITEMS = 200

function load(): LabeledTicket[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as LabeledTicket[]) : []
  } catch {
    return []
  }
}

export const useLabeledTicketsStore = defineStore('labeledTickets', () => {
  const tickets = ref<LabeledTicket[]>(load())

  function persist(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tickets.value))
    } catch {
      // localStorage may be full or disabled — non-critical.
    }
  }

  /** Record (or refresh) a labeled ticket, most-recent first, de-duped by ref. */
  function record(entry: Omit<LabeledTicket, 'timestamp'> & { timestamp?: string }): void {
    const item: LabeledTicket = { ...entry, timestamp: entry.timestamp ?? new Date().toISOString() }
    tickets.value = [item, ...tickets.value.filter((t) => t.ref !== item.ref)].slice(0, MAX_ITEMS)
    persist()
  }

  function remove(ref: string): void {
    tickets.value = tickets.value.filter((t) => t.ref !== ref)
    persist()
  }

  function clear(): void {
    tickets.value = []
    persist()
  }

  /** Re-read from localStorage (e.g. after another tab updates the list). */
  function reload(): void {
    tickets.value = load()
  }

  // Cross-tab sync: refresh when another browser tab mutates the list.
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', (event) => {
      if (event.key === STORAGE_KEY) reload()
    })
  }

  return { tickets, record, remove, clear, reload }
})
