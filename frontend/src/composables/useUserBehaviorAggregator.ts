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
  InstanceInfo,
  ModelPerformanceSummary,
  PageEngagementMetrics,
  ProgramKpi,
  ProgramKpiStatus,
  ProgramKpiTargets,
  ResolutionEffortMetrics,
  ResourceEfficiencyMetrics,
  SatisfactionMetrics,
  TicketHeatmap,
  TicketHeatmapEntry,
  UserBehaviorOverview,
  XAIEngagementMetrics,
} from '@/types/api'
import type { LocalEvent } from '@/stores/useTelemetryStore'

const DECISION_ACTIONS = new Set(['confirm_label', 'override_label', 'abstain'])
const EXPLANATION_ACTIONS = new Set(['view_explanation', 'view_nearest_ticket'])
const AI_LATENCY_ACTIONS = new Set(['model_predict', 'model_train', 'xai_latency'])
const XAI_INFLUENCE_WINDOW_MS = 5 * 60 * 1000
const INSPECT_WINDOW_MS = 10 * 60 * 1000

/** Confidence at/above which a confirmed prediction counts as AI-managed. */
export const AUTO_CLOSE_CONFIDENCE = 0.85

/** Default AFU KPI targets (AFU: auto-solve 60%, AI-managed 30%; rest tuned). */
export const DEFAULT_KPI_TARGETS: ProgramKpiTargets = {
  auto_solve: 0.6,
  ai_managed: 0.3,
  resolution_time_reduction: 0.4,
  reopen_rate_max: 0.1,
  manual_effort_reduction: 0.5,
  trust: 0.8,
  assistance: 0.75,
  overall_satisfaction: 0.75,
}

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

// --------------------------------------------------------------------------- //
// Shared helpers for pillar metrics                                           //
// --------------------------------------------------------------------------- //

function percentile(values: number[], p: number): number | null {
  if (!values.length) return null
  const sorted = [...values].sort((a, b) => a - b)
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1))
  return sorted[idx]!
}

function isFlag(e: LocalEvent, key: string): boolean {
  return e.payload?.[key] === true
}

function samplesToTarget(
  f1Scores: number[],
  numLabeled: number[],
  target: number,
): number | null {
  for (let i = 0; i < f1Scores.length; i++) {
    if ((f1Scores[i] ?? 0) >= target) return numLabeled[i] ?? null
  }
  return null
}

// --------------------------------------------------------------------------- //
// Pillar 1 — Model performance (derived from InstanceInfo)                     //
// --------------------------------------------------------------------------- //

export function deriveModelPerformance(info?: InstanceInfo | null): ModelPerformanceSummary {
  const f1 = info?.f1_scores ?? []
  const entropies = info?.mean_entropies ?? []
  const numLabeled = info?.num_labeled ?? []
  const accuracies = info?.accuracies ?? []
  const aurocs = info?.roc_aucs_ovr_macro ?? []

  let trend: ModelPerformanceSummary['f1_trend'] = null
  if (f1.length >= 3) {
    const recent = mean(f1.slice(-3))!
    const early = mean(f1.slice(0, 3))!
    if (recent > early + 0.02) trend = 'improving'
    else if (recent < early - 0.02) trend = 'declining'
    else trend = 'stable'
  }

  let convergence: number | null = null
  for (let i = 2; i < f1.length; i++) {
    if (
      Math.abs((f1[i] ?? 0) - (f1[i - 1] ?? 0)) < 0.01 &&
      Math.abs((f1[i - 1] ?? 0) - (f1[i - 2] ?? 0)) < 0.01
    ) {
      convergence = i
      break
    }
  }

  return {
    latest_f1: f1.length ? round(f1[f1.length - 1]!, 4) : null,
    f1_improvement: f1.length > 1 ? round(f1[f1.length - 1]! - f1[0]!, 4) : null,
    latest_accuracy: accuracies.length
      ? round(accuracies[accuracies.length - 1]!, 4)
      : info?.test_accuracy != null
        ? round(info.test_accuracy, 4)
        : null,
    latest_auroc: aurocs.length ? round(aurocs[aurocs.length - 1]!, 4) : null,
    entropy_reduction:
      entropies.length > 1 ? round(entropies[0]! - entropies[entropies.length - 1]!, 4) : null,
    total_labeled: numLabeled.length ? numLabeled[numLabeled.length - 1]! : 0,
    iterations: f1.length,
    f1_trend: trend,
    convergence_iteration: convergence,
  }
}

// --------------------------------------------------------------------------- //
// Pillar 2 — Resource efficiency                                              //
// --------------------------------------------------------------------------- //

export function aggregateResourceEfficiency(
  events: LocalEvent[],
  instanceId: number | null,
  perf?: { f1_scores?: number[]; num_labeled?: number[] } | null,
): ResourceEfficiencyMetrics {
  const filtered = filterByInstance(events, instanceId)

  const f1 = perf?.f1_scores ?? []
  const numLabeled = perf?.num_labeled ?? []
  const labelsTotal = numLabeled.length ? numLabeled[numLabeled.length - 1]! : 0

  const f1Gain = f1.length > 1 ? f1[f1.length - 1]! - f1[0]! : null
  const f1GainPer100 =
    f1Gain != null && labelsTotal > 0 ? round((f1Gain / labelsTotal) * 100, 3) : null

  const decisionDurations: number[] = []
  const aiLatencies: number[] = []
  const predictLatencies: number[] = []
  const xaiLatencies: number[] = []

  for (const e of filtered) {
    if (DECISION_ACTIONS.has(e.action) && e.latency_ms != null) {
      decisionDurations.push(e.latency_ms / 1000)
    }
    if (AI_LATENCY_ACTIONS.has(e.action) && e.latency_ms != null) {
      aiLatencies.push(e.latency_ms)
      if (e.action === 'model_predict') predictLatencies.push(e.latency_ms)
      if (e.action === 'xai_latency') xaiLatencies.push(e.latency_ms)
    }
  }

  const totalHuman = decisionDurations.reduce((a, b) => a + b, 0)
  const meanDecision = mean(decisionDurations)
  const decisionsPerHour = meanDecision != null && meanDecision > 0 ? 3600 / meanDecision : null
  const meanAi = mean(aiLatencies)
  const meanPredict = mean(predictLatencies)
  const meanXai = mean(xaiLatencies)
  const p95Ai = percentile(aiLatencies, 95)

  return {
    samples_to_f1_70: samplesToTarget(f1, numLabeled, 0.7),
    samples_to_f1_80: samplesToTarget(f1, numLabeled, 0.8),
    samples_to_f1_90: samplesToTarget(f1, numLabeled, 0.9),
    f1_gain_per_100_labels: f1GainPer100,
    labels_total: labelsTotal,
    total_human_seconds: round(totalHuman, 1),
    mean_decision_seconds: meanDecision != null ? round(meanDecision, 1) : null,
    decisions_per_hour: decisionsPerHour != null ? round(decisionsPerHour, 1) : null,
    mean_ai_latency_ms: meanAi != null ? Math.round(meanAi) : null,
    p95_ai_latency_ms: p95Ai != null ? Math.round(p95Ai) : null,
    mean_predict_latency_ms: meanPredict != null ? Math.round(meanPredict) : null,
    mean_xai_latency_ms: meanXai != null ? Math.round(meanXai) : null,
    ai_latency_samples: aiLatencies.length,
  }
}

// --------------------------------------------------------------------------- //
// Pillar 3 — Human satisfaction                                               //
// --------------------------------------------------------------------------- //

export function aggregateSatisfaction(
  events: LocalEvent[],
  instanceId: number | null,
): SatisfactionMetrics {
  const filtered = filterByInstance(events, instanceId)

  let confirm = 0
  let override = 0
  let abstain = 0
  // Friction feedback that is NOT itself a decision (tired / difficult skips).
  let tiredFb = 0
  let difficultFb = 0
  let idkFb = 0

  for (const e of filtered) {
    if (DECISION_ACTIONS.has(e.action)) {
      if (e.action === 'confirm_label') confirm++
      else if (e.action === 'override_label') override++
      else if (e.action === 'abstain') abstain++
      // A decision may optionally carry friction flags (live label-with-info).
      if (isFlag(e, 'is_tired')) tiredFb++
      if (isFlag(e, 'is_difficult')) difficultFb++
      continue
    }
    if (e.action === 'labeler_feedback') {
      // A false selection is a toggle-off interaction, not a reported flag.
      // Missing values remain compatible with older stored telemetry events.
      if (e.payload?.['selected'] === false) continue
      const ft = String(e.payload?.['feedback_type'] ?? '')
      if (ft === 'I_AM_TIRED' || isFlag(e, 'is_tired')) tiredFb++
      else if (ft === 'DIFFICULT_TICKET' || isFlag(e, 'is_difficult')) difficultFb++
      else if (ft === 'I_DONT_KNOW' || isFlag(e, 'i_dont_know')) idkFb++
    }
  }

  const total = confirm + override + abstain
  const idkCount = abstain + idkFb
  const friction = tiredFb + difficultFb + idkCount
  // Rate over all human touchpoints (decisions + non-decision friction skips).
  const touchpoints = total + tiredFb + difficultFb + idkFb
  const flaggedRate = touchpoints > 0 ? Math.min(1, friction / touchpoints) : null
  const acceptance = total > 0 ? confirm / total : null
  const satisfactionIndex =
    acceptance != null ? round(acceptance * (1 - (flaggedRate ?? 0)), 4) : null

  return {
    confirm_count: confirm,
    override_count: override,
    abstain_count: abstain,
    total_decisions: total,
    acceptance_rate: acceptance != null ? round(acceptance, 4) : null,
    override_rate: total > 0 ? round(override / total, 4) : null,
    tired_count: tiredFb,
    difficult_count: difficultFb,
    idk_count: idkCount,
    flagged_decision_rate: flaggedRate != null ? round(flaggedRate, 4) : null,
    satisfaction_index: satisfactionIndex,
  }
}

// --------------------------------------------------------------------------- //
// Resolution assistance — operator effort on AI-suggested resolutions          //
// --------------------------------------------------------------------------- //

/**
 * Estimate how much manual effort AI-suggested resolutions saved, from
 * `validate_resolution` events emitted by the Resolution tab when an operator
 * accepts (copies or saves) a suggested reply. `edit_ratio` is the normalised
 * character edit distance between the generated reply and the final text, so
 * `effort_saved` = 1 − mean edit ratio.
 */
export function aggregateResolutionEffort(
  events: LocalEvent[],
  instanceId: number | null,
): ResolutionEffortMetrics {
  const filtered = filterByInstance(events, instanceId)

  const editRatios: number[] = []
  const reviewSeconds: number[] = []
  let used = 0
  let verbatim = 0

  for (const e of filtered) {
    if (e.action !== 'validate_resolution' || pageOf(e) !== 'resolution') continue
    used++
    const ratio = e.payload?.['edit_ratio']
    if (typeof ratio === 'number' && Number.isFinite(ratio)) {
      editRatios.push(Math.max(0, Math.min(1, ratio)))
    }
    if (e.payload?.['edited'] === false) verbatim++
    if (e.latency_ms != null) reviewSeconds.push(e.latency_ms / 1000)
  }

  const meanEdit = mean(editRatios)
  const meanReview = mean(reviewSeconds)

  return {
    resolutions_used: used,
    verbatim_count: verbatim,
    verbatim_rate: used > 0 ? round(verbatim / used, 4) : null,
    mean_edit_ratio: meanEdit != null ? round(meanEdit, 4) : null,
    effort_saved: meanEdit != null ? round(1 - meanEdit, 4) : null,
    mean_review_seconds: meanReview != null ? round(meanReview, 1) : null,
  }
}

// --------------------------------------------------------------------------- //
// Programme KPIs (AFU objectives vs targets)                                  //
// --------------------------------------------------------------------------- //

function kpiStatus(
  value: number | null,
  target: number | null,
  higherIsBetter: boolean,
): ProgramKpiStatus {
  if (value == null || target == null) return 'no_data'
  if (higherIsBetter) {
    if (value >= target) return 'on_track'
    if (value >= 0.8 * target) return 'at_risk'
    return 'off_track'
  }
  if (value <= target) return 'on_track'
  if (value <= 2 * target) return 'at_risk'
  return 'off_track'
}

/**
 * Map the AFU programme KPIs onto values derived from the pillars + lifecycle
 * telemetry (`ticket_auto_closed` / `ticket_reopened`).
 *
 * Auto-closed tickets are a subset (tag) of confirmed decisions, so they never
 * inflate the decision denominators.
 */
export function aggregateProgramKpis(
  events: LocalEvent[],
  instanceId: number | null,
  modelSummary: ModelPerformanceSummary,
  targets: ProgramKpiTargets = DEFAULT_KPI_TARGETS,
): ProgramKpi[] {
  const filtered = filterByInstance(events, instanceId)
  const ai = aggregateAIImpact(events, instanceId)
  const xai = aggregateXaiEngagement(events, instanceId)
  const sat = aggregateSatisfaction(events, instanceId)
  const resEffort = aggregateResolutionEffort(events, instanceId)

  let autoClosed = 0
  let reopened = 0
  for (const e of filtered) {
    if (e.action === 'ticket_auto_closed') autoClosed++
    else if (e.action === 'ticket_reopened') reopened++
  }

  const confirm = sat.confirm_count
  const override = sat.override_count
  const decisions = sat.total_decisions
  const closedTickets = autoClosed + confirm + override

  // 1 — auto-solve rate ≈ model accuracy after a limited label budget.
  const autoSolve = modelSummary.latest_accuracy

  // 2 — AI-managed & closed (auto-closed as a share of all handled tickets).
  const aiManaged = decisions > 0 ? round(autoClosed / decisions, 4) : null

  // 3 — resolution-time reduction (aided vs manual decision time).
  const manual = ai.mean_decision_time_manual_s
  const aided = ai.mean_decision_time_aided_s
  const resTime =
    manual != null && aided != null && manual > 0 ? round((manual - aided) / manual, 4) : null

  // 4 — re-open rate (lower is better).
  const reopenRate = closedTickets > 0 ? round(reopened / closedTickets, 4) : null

  // 5 — manual-effort reduction = share handled without manual correction.
  const effort = decisions > 0 ? round((autoClosed + confirm) / decisions, 4) : null

  // 6 — trust: acceptance rate when an explanation was surfaced.
  const trust = xai.acceptance_rate_with_xai ?? sat.acceptance_rate

  // 7 — assistance satisfaction: XAI engagement blended with explained-acceptance.
  const withX = xai.decisions_with_xai
  const woX = xai.decisions_without_xai
  const engagement = withX + woX > 0 ? withX / (withX + woX) : null
  const assistanceVals = [engagement, xai.acceptance_rate_with_xai].filter(
    (v): v is number => v != null,
  )
  const assistance = assistanceVals.length
    ? round(assistanceVals.reduce((a, b) => a + b, 0) / assistanceVals.length, 4)
    : null

  // 8 — overall satisfaction index.
  const overall = sat.satisfaction_index

  return [
    {
      id: 'auto_solve',
      label: 'Tickets auto-solved after limited examples',
      value: autoSolve,
      target: targets.auto_solve,
      higher_is_better: true,
      status: kpiStatus(autoSolve, targets.auto_solve, true),
      hint: `Model accuracy after ${modelSummary.total_labeled} labelled examples`,
      source: 'Model performance',
      instrumented: autoSolve != null,
    },
    {
      id: 'ai_managed',
      label: 'Tickets auto-managed & closed by AI',
      value: aiManaged,
      target: targets.ai_managed,
      higher_is_better: true,
      status: kpiStatus(aiManaged, targets.ai_managed, true),
      hint: `${autoClosed} of ${decisions} tickets AI-managed (confidence ≥ ${Math.round(AUTO_CLOSE_CONFIDENCE * 100)}%)`,
      source: 'Lifecycle telemetry',
      instrumented: true,
    },
    {
      id: 'resolution_time',
      label: 'Reduction in avg resolution time',
      value: resTime,
      target: targets.resolution_time_reduction,
      higher_is_better: true,
      status: kpiStatus(resTime, targets.resolution_time_reduction, true),
      hint: 'AI-aided vs manual decision time',
      source: 'AI-impact',
      instrumented: resTime != null,
    },
    {
      id: 'reopen_rate',
      label: 'Re-opened tickets (rate)',
      value: reopenRate,
      target: targets.reopen_rate_max,
      higher_is_better: false,
      status: kpiStatus(reopenRate, targets.reopen_rate_max, false),
      hint:
        closedTickets > 0
          ? `${reopened} of ${closedTickets} closed tickets re-opened`
          : 'No closed tickets yet',
      source: 'Lifecycle telemetry',
      instrumented: true,
    },
    {
      id: 'manual_effort',
      label: 'Reduction in manual operator effort',
      value: effort,
      target: targets.manual_effort_reduction,
      higher_is_better: true,
      status: kpiStatus(effort, targets.manual_effort_reduction, true),
      hint: 'Share handled without manual correction',
      source: 'Resource / Satisfaction',
      instrumented: effort != null,
    },
    {
      id: 'resolution_effort',
      label: 'Effort saved on suggested resolutions',
      value: resEffort.effort_saved,
      target: targets.manual_effort_reduction,
      higher_is_better: true,
      status: kpiStatus(resEffort.effort_saved, targets.manual_effort_reduction, true),
      hint:
        resEffort.resolutions_used > 0
          ? `${resEffort.resolutions_used} suggestions used · ${Math.round((resEffort.verbatim_rate ?? 0) * 100)}% used verbatim`
          : 'No resolutions validated yet',
      source: 'Resolution editing',
      instrumented: resEffort.resolutions_used > 0,
    },
    {
      id: 'trust',
      label: 'User trust in the information',
      value: trust != null ? round(trust, 4) : null,
      target: targets.trust,
      higher_is_better: true,
      status: kpiStatus(trust, targets.trust, true),
      hint: 'Acceptance rate when an explanation was seen',
      source: 'XAI engagement',
      instrumented: trust != null,
    },
    {
      id: 'assistance',
      label: 'Satisfaction with the assistance',
      value: assistance,
      target: targets.assistance,
      higher_is_better: true,
      status: kpiStatus(assistance, targets.assistance, true),
      hint: 'XAI engagement blended with explained-acceptance',
      source: 'XAI engagement',
      instrumented: assistance != null,
    },
    {
      id: 'overall',
      label: 'Overall user satisfaction',
      value: overall,
      target: targets.overall_satisfaction,
      higher_is_better: true,
      status: kpiStatus(overall, targets.overall_satisfaction, true),
      hint: 'Acceptance weighted down by reported friction',
      source: 'Satisfaction',
      instrumented: overall != null,
    },
  ]
}
