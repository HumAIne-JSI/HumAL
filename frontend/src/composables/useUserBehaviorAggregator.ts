/**
 * Client-side equivalent of `backend/app/services/user_behavior_svc.py`.
 *
 * Used in Mock mode so the User Behavior dashboard reflects events the user
 * has produced locally (via useBenchmarkTelemetry → useTelemetryStore)
 * without needing a backend round-trip.
 *
 * Output shapes mirror the Pydantic models exactly so the dashboard treats
 * mock-mode and live-mode responses identically.
 */
import type {
  AIImpactMetrics,
  ConfidenceBucket,
  EventTimeline,
  EventTimelineBin,
  FunnelMetrics,
  PageEngagementMetrics,
  TicketHeatmap,
  TicketHeatmapEntry,
  UserBehaviorOverview,
  XAIEngagementMetrics,
} from '@/types/api'
import type { LocalEvent } from '@/stores/useTelemetryStore'

const DECISION_ACTIONS = new Set(['confirm_label', 'override_label', 'abstain'])
const EXPLANATION_ACTIONS = new Set(['view_explanation', 'view_nearest_ticket'])
const XAI_INFLUENCE_WINDOW_MS = 5 * 60 * 1000
const INSPECT_WINDOW_MS = 10 * 60 * 1000

const CONFIDENCE_BUCKETS = [
  { label: '<50%', lo: 0, hi: 0.5 },
  { label: '50-70%', lo: 0.5, hi: 0.7 },
  { label: '70-85%', lo: 0.7, hi: 0.85 },
  { label: '85%+', lo: 0.85, hi: 1.0001 },
] as const

function filterByInstance(events: LocalEvent[], instanceId: number | null): LocalEvent[] {
  if (instanceId == null) return events
  return events.filter((e) => e.al_instance_id === instanceId)
}

function sortedByTime(events: LocalEvent[]): LocalEvent[] {
  return [...events].sort((a, b) => a.timestamp.localeCompare(b.timestamp))
}

function ticketRef(e: LocalEvent): string | null {
  const r = e.payload?.['ticket_ref'] ?? e.payload?.['ticket_id']
  return r != null && String(r).length > 0 ? String(r) : null
}

function pageOf(e: LocalEvent): string | null {
  const p = e.payload?.['page']
  return p != null && String(p).length > 0 ? String(p) : null
}

function getConfidence(e: LocalEvent): number | null {
  const c = e.payload?.['confidence']
  if (typeof c === 'number' && Number.isFinite(c)) return c
  return null
}

function bucketFor(value: number) {
  for (const b of CONFIDENCE_BUCKETS) {
    if (value >= b.lo && value < b.hi) return b
  }
  return null
}

function mean(values: number[]): number | null {
  if (!values.length) return null
  return values.reduce((a, b) => a + b, 0) / values.length
}

function round(value: number, places = 2): number {
  const factor = 10 ** places
  return Math.round(value * factor) / factor
}

// --------------------------------------------------------------------------- //
// Overview                                                                    //
// --------------------------------------------------------------------------- //

export function aggregateOverview(
  events: LocalEvent[],
  instanceId: number | null,
): UserBehaviorOverview {
  const filtered = filterByInstance(events, instanceId)
  const byAction: Record<string, number> = {}
  const byPage: Record<string, number> = {}
  const tickets = new Set<string>()
  let activeSeconds = 0
  const decisionDurations: number[] = []

  for (const e of filtered) {
    byAction[e.action] = (byAction[e.action] || 0) + 1
    const p = pageOf(e)
    if (p) byPage[p] = (byPage[p] || 0) + 1
    const ref = ticketRef(e)
    if (ref) tickets.add(ref)
    if ((e.action === 'view_ticket_end' || e.action === 'open_page') && e.latency_ms) {
      activeSeconds += e.latency_ms / 1000
    }
    if (DECISION_ACTIONS.has(e.action) && e.latency_ms != null) {
      decisionDurations.push(e.latency_ms / 1000)
    }
  }

  const meanDecision = mean(decisionDurations)
  return {
    total_events: filtered.length,
    events_by_action: byAction,
    events_by_page: byPage,
    unique_tickets_touched: tickets.size,
    total_active_seconds: round(activeSeconds, 1),
    mean_decision_seconds: meanDecision != null ? round(meanDecision, 1) : null,
  }
}

// --------------------------------------------------------------------------- //
// AI impact                                                                   //
// --------------------------------------------------------------------------- //

export function aggregateAIImpact(
  events: LocalEvent[],
  instanceId: number | null,
): AIImpactMetrics {
  const filtered = sortedByTime(filterByInstance(events, instanceId))

  // Per-ticket last-seen prediction (so we can attribute confidence + aided-ness)
  const lastInspect: Record<string, { ts: number; confidence: number | null }> = {}

  let confirm = 0,
    override = 0,
    abstain = 0
  const aidedDurations: number[] = []
  const manualDurations: number[] = []
  const buckets: Record<string, ConfidenceBucket> = {}
  for (const b of CONFIDENCE_BUCKETS) {
    buckets[b.label] = {
      label: b.label,
      min_confidence: b.lo,
      max_confidence: b.hi,
      confirm: 0,
      override: 0,
      abstain: 0,
    }
  }

  for (const e of filtered) {
    const ts = Date.parse(e.timestamp)
    const ref = ticketRef(e)

    if (e.action === 'inspect_ticket' && ref) {
      lastInspect[ref] = { ts, confidence: getConfidence(e) }
      continue
    }

    if (!DECISION_ACTIONS.has(e.action)) continue

    if (e.action === 'confirm_label') confirm++
    else if (e.action === 'override_label') override++
    else if (e.action === 'abstain') abstain++

    const inspect = ref ? lastInspect[ref] : undefined
    const aided = inspect != null && ts - inspect.ts <= INSPECT_WINDOW_MS

    if (e.latency_ms != null) {
      const secs = e.latency_ms / 1000
      if (aided) aidedDurations.push(secs)
      else manualDurations.push(secs)
    }

    const confidence = inspect?.confidence ?? getConfidence(e)
    if (confidence != null) {
      const bucket = bucketFor(confidence)
      if (bucket) {
        if (e.action === 'confirm_label') buckets[bucket.label]!.confirm++
        else if (e.action === 'override_label') buckets[bucket.label]!.override++
        else if (e.action === 'abstain') buckets[bucket.label]!.abstain++
      }
    }
  }

  const totalDecisions = confirm + override + abstain
  const aided = mean(aidedDurations)
  const manual = mean(manualDurations)
  const delta = aided != null && manual != null ? manual - aided : null

  return {
    confirm_count: confirm,
    override_count: override,
    abstain_count: abstain,
    acceptance_rate: totalDecisions > 0 ? round(confirm / totalDecisions, 4) : null,
    mean_decision_time_aided_s: aided != null ? round(aided, 2) : null,
    mean_decision_time_manual_s: manual != null ? round(manual, 2) : null,
    decision_time_delta_s: delta != null ? round(delta, 2) : null,
    confidence_buckets: Object.values(buckets),
  }
}

// --------------------------------------------------------------------------- //
// XAI engagement                                                              //
// --------------------------------------------------------------------------- //

export function aggregateXaiEngagement(
  events: LocalEvent[],
  instanceId: number | null,
): XAIEngagementMetrics {
  const filtered = sortedByTime(filterByInstance(events, instanceId))
  const lastExplanation: Record<string, number> = {}

  let withConfirm = 0,
    withOverride = 0,
    withoutConfirm = 0,
    withoutOverride = 0
  const withDur: number[] = []
  const withoutDur: number[] = []

  for (const e of filtered) {
    const ts = Date.parse(e.timestamp)
    const ref = ticketRef(e)

    if (EXPLANATION_ACTIONS.has(e.action) && ref) {
      lastExplanation[ref] = ts
      continue
    }

    if (e.action !== 'confirm_label' && e.action !== 'override_label') continue

    const seenAt = ref ? lastExplanation[ref] : undefined
    const engaged = seenAt != null && ts - seenAt <= XAI_INFLUENCE_WINDOW_MS

    if (engaged) {
      if (e.action === 'confirm_label') withConfirm++
      else withOverride++
      if (e.latency_ms != null) withDur.push(e.latency_ms / 1000)
    } else {
      if (e.action === 'confirm_label') withoutConfirm++
      else withoutOverride++
      if (e.latency_ms != null) withoutDur.push(e.latency_ms / 1000)
    }
  }

  const withTotal = withConfirm + withOverride
  const withoutTotal = withoutConfirm + withoutOverride
  const meanWith = mean(withDur)
  const meanWithout = mean(withoutDur)

  return {
    decisions_with_xai: withTotal,
    decisions_without_xai: withoutTotal,
    acceptance_rate_with_xai: withTotal > 0 ? round(withConfirm / withTotal, 4) : null,
    acceptance_rate_without_xai: withoutTotal > 0 ? round(withoutConfirm / withoutTotal, 4) : null,
    mean_decision_time_with_xai_s: meanWith != null ? round(meanWith, 2) : null,
    mean_decision_time_without_xai_s: meanWithout != null ? round(meanWithout, 2) : null,
  }
}

// --------------------------------------------------------------------------- //
// Page engagement                                                             //
// --------------------------------------------------------------------------- //

export function aggregatePageEngagement(
  events: LocalEvent[],
  instanceId: number | null,
): PageEngagementMetrics {
  const filtered = filterByInstance(events, instanceId)
  type Acc = { views: number; total: number; durations: number[] }
  const byPage = new Map<string, Acc>()

  for (const e of filtered) {
    if (e.action !== 'open_page') continue
    const target = pageOf(e)
    const prev = (e.payload?.['prev_page'] as string | null) ?? null
    const prevDuration =
      (typeof e.payload?.['prev_duration_s'] === 'number'
        ? (e.payload['prev_duration_s'] as number)
        : null) ??
      (e.latency_ms != null ? e.latency_ms / 1000 : null)
    if (target) {
      const entry = byPage.get(target) ?? { views: 0, total: 0, durations: [] }
      entry.views += 1
      byPage.set(target, entry)
    }
    if (prev && prevDuration != null && prevDuration > 0) {
      const entry = byPage.get(prev) ?? { views: 0, total: 0, durations: [] }
      entry.total += prevDuration
      entry.durations.push(prevDuration)
      byPage.set(prev, entry)
    }
  }

  const pages = [...byPage.entries()]
    .map(([page, acc]) => ({
      page,
      views: acc.views,
      mean_duration_s: acc.durations.length ? round(mean(acc.durations)!, 1) : null,
      total_duration_s: round(acc.total, 1),
    }))
    .sort((a, b) => b.total_duration_s - a.total_duration_s)

  return { pages }
}

// --------------------------------------------------------------------------- //
// Ticket heatmap                                                              //
// --------------------------------------------------------------------------- //

export function aggregateTicketHeatmap(
  events: LocalEvent[],
  instanceId: number | null,
  limit = 20,
): TicketHeatmap {
  const filtered = filterByInstance(events, instanceId)
  type Acc = { count: number; total: number; lastSeen: string | null }
  const byTicket = new Map<string, Acc>()

  for (const e of filtered) {
    const ref = ticketRef(e)
    if (!ref) continue
    const entry = byTicket.get(ref) ?? { count: 0, total: 0, lastSeen: null }
    entry.count += 1
    if (e.action === 'view_ticket_end' && e.latency_ms) {
      entry.total += e.latency_ms / 1000
    }
    if (!entry.lastSeen || e.timestamp > entry.lastSeen) {
      entry.lastSeen = e.timestamp
    }
    byTicket.set(ref, entry)
  }

  const entries: TicketHeatmapEntry[] = [...byTicket.entries()]
    .map(([ticket_ref, acc]) => ({
      ticket_ref,
      interaction_count: acc.count,
      total_seconds: round(acc.total, 1),
      last_seen_at: acc.lastSeen,
    }))
    .sort((a, b) => {
      if (b.interaction_count !== a.interaction_count) {
        return b.interaction_count - a.interaction_count
      }
      return b.total_seconds - a.total_seconds
    })
    .slice(0, limit)

  return { entries }
}

// --------------------------------------------------------------------------- //
// Event timeline                                                              //
// --------------------------------------------------------------------------- //

export function aggregateTimeline(
  events: LocalEvent[],
  instanceId: number | null,
  binSeconds = 60,
): EventTimeline {
  const filtered = filterByInstance(events, instanceId)
  const binMs = binSeconds * 1000
  const byBucket = new Map<number, { count: number; byAction: Record<string, number> }>()

  for (const e of filtered) {
    const ts = Date.parse(e.timestamp)
    if (Number.isNaN(ts)) continue
    const bucketStart = Math.floor(ts / binMs) * binMs
    const entry = byBucket.get(bucketStart) ?? { count: 0, byAction: {} }
    entry.count += 1
    entry.byAction[e.action] = (entry.byAction[e.action] || 0) + 1
    byBucket.set(bucketStart, entry)
  }

  const bins: EventTimelineBin[] = [...byBucket.entries()]
    .sort(([a], [b]) => a - b)
    .map(([bucketStart, acc]) => ({
      bucket_start: new Date(bucketStart).toISOString(),
      count: acc.count,
      by_action: acc.byAction,
    }))

  return { bin_seconds: binSeconds, bins }
}

// --------------------------------------------------------------------------- //
// Funnel                                                                      //
// --------------------------------------------------------------------------- //

export function aggregateFunnel(
  events: LocalEvent[],
  instanceId: number | null,
): FunnelMetrics {
  const filtered = filterByInstance(events, instanceId)
  const selected = new Set<string>()
  const inspected = new Set<string>()
  const labeled = new Set<string>()

  for (const e of filtered) {
    const ref = ticketRef(e)
    if (!ref) continue
    if (e.action === 'select_ticket') selected.add(ref)
    if (EXPLANATION_ACTIONS.has(e.action)) inspected.add(ref)
    if (DECISION_ACTIONS.has(e.action)) labeled.add(ref)
  }

  const selectedCount = selected.size
  const inspectedCount = inspected.size
  const labeledCount = labeled.size

  return {
    selected: selectedCount,
    inspected_explanation: inspectedCount,
    labeled: labeledCount,
    select_to_explanation_rate:
      selectedCount > 0 ? round(inspectedCount / selectedCount, 4) : null,
    explanation_to_label_rate:
      inspectedCount > 0 ? round(labeledCount / inspectedCount, 4) : null,
    select_to_label_rate: selectedCount > 0 ? round(labeledCount / selectedCount, 4) : null,
  }
}
