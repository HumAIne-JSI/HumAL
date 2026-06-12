/**
 * Client-side event log used in Mock mode so the User Behavior dashboard
 * can reflect what the user actually did, without a backend.
 *
 * Events are stored in-memory and mirrored to localStorage so they survive
 * page reloads. The shape matches the backend `al_events` row contract used
 * by the UserBehaviorService aggregator.
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface LocalEvent {
  al_instance_id: number | null
  timestamp: string // ISO-8601
  user_id: string | null
  action: string
  latency_ms: number | null
  payload: Record<string, unknown>
}

const STORAGE_KEY = 'humal-mock-telemetry-events'
const MAX_EVENTS = 5000

function loadFromStorage(): LocalEvent[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return seedEvents()
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return seedEvents()
    return parsed as LocalEvent[]
  } catch {
    return seedEvents()
  }
}

/**
 * Synthetic "yesterday" history so the dashboard is never blank on first
 * visit. Spread across a few hours, mixes confirm/override/abstain with
 * XAI views before some decisions so the AI-impact and XAI-lift cards
 * have non-zero numbers right away.
 */
function seedEvents(): LocalEvent[] {
  const out: LocalEvent[] = []
  const baseTs = Date.now() - 6 * 60 * 60 * 1000 // 6h ago
  const tickets = ['TKT-1042', 'TKT-1043', 'TKT-1044', 'TKT-1045', 'TKT-1046', 'TKT-1047', 'TKT-1048', 'TKT-1049']
  const teams = ['Team A', 'Team B', 'Team C']

  function push(offsetMs: number, ev: Omit<LocalEvent, 'timestamp' | 'user_id'>) {
    out.push({
      ...ev,
      timestamp: new Date(baseTs + offsetMs).toISOString(),
      user_id: null,
    })
  }

  // 8 ticket sessions, alternating between AI-aided (with XAI) and manual
  tickets.forEach((ref, idx) => {
    const sessionStart = idx * 12 * 60 * 1000 // every 12 minutes
    const isAided = idx % 2 === 0
    const prediction = teams[idx % teams.length]
    const confidence = isAided ? 0.6 + 0.08 * (idx % 4) : 0.45 + 0.05 * (idx % 3)

    push(sessionStart, {
      al_instance_id: null,
      action: 'open_page',
      latency_ms: 8000 + (idx % 5) * 1000,
      payload: { page: 'queue_aided', prev_page: 'home', prev_duration_s: 8 + (idx % 5) },
    })
    push(sessionStart + 1000, {
      al_instance_id: null,
      action: 'select_ticket',
      latency_ms: null,
      payload: { ticket_ref: ref, page: 'queue_aided' },
    })
    push(sessionStart + 1100, {
      al_instance_id: null,
      action: 'view_ticket_start',
      latency_ms: null,
      payload: { ticket_ref: ref, page: 'queue_aided' },
    })
    push(sessionStart + 1500, {
      al_instance_id: null,
      action: 'inspect_ticket',
      latency_ms: null,
      payload: { ticket_ref: ref, page: 'queue_aided', prediction, confidence },
    })
    if (isAided) {
      push(sessionStart + 2000, {
        al_instance_id: null,
        action: 'view_explanation',
        latency_ms: null,
        payload: { ticket_ref: ref, page: 'queue_aided', explanation_type: 'lime' },
      })
      push(sessionStart + 2500, {
        al_instance_id: null,
        action: 'view_nearest_ticket',
        latency_ms: null,
        payload: { ticket_ref: ref, page: 'queue_aided', nearest_ref: `TKT-${900 + idx}` },
      })
    }

    const decisionLatency = isAided ? 12000 + (idx % 3) * 4000 : 35000 + (idx % 3) * 6000
    const action = isAided
      ? (idx % 4 === 3 ? 'override_label' : 'confirm_label')
      : (idx % 5 === 4 ? 'abstain' : 'confirm_label')

    push(sessionStart + 3000 + decisionLatency, {
      al_instance_id: null,
      action,
      latency_ms: decisionLatency,
      payload: { ticket_ref: ref, page: 'queue_aided', label: prediction, prediction, confidence },
    })
    push(sessionStart + 3500 + decisionLatency, {
      al_instance_id: null,
      action: 'view_ticket_end',
      latency_ms: 2000 + decisionLatency,
      payload: { ticket_ref: ref, page: 'queue_aided', duration_s: (2000 + decisionLatency) / 1000 },
    })
  })

  return out
}

export const useTelemetryStore = defineStore('telemetry', () => {
  const events = ref<LocalEvent[]>(loadFromStorage())

  function persist() {
    try {
      if (events.value.length > MAX_EVENTS) {
        events.value = events.value.slice(-MAX_EVENTS)
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(events.value))
    } catch (err) {
      console.warn('[telemetry] failed to persist events', err)
    }
  }

  function addEvent(event: Omit<LocalEvent, 'timestamp' | 'user_id'> & {
    timestamp?: string
    user_id?: string | null
  }) {
    events.value.push({
      timestamp: event.timestamp ?? new Date().toISOString(),
      user_id: event.user_id ?? null,
      al_instance_id: event.al_instance_id,
      action: event.action,
      latency_ms: event.latency_ms,
      payload: event.payload,
    })
    persist()
  }

  function clear() {
    events.value = []
    persist()
  }

  function reseed() {
    events.value = seedEvents()
    persist()
  }

  // Save when the user closes the tab; debounce to avoid hammering on rapid bursts.
  let saveTimer: ReturnType<typeof setTimeout> | null = null
  watch(
    events,
    () => {
      if (saveTimer) clearTimeout(saveTimer)
      saveTimer = setTimeout(persist, 500)
    },
    { deep: true },
  )

  return { events, addEvent, clear, reseed }
})
