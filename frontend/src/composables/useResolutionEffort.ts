import { ref, watch, type Ref } from 'vue'
import type { AssistedResolution } from '@/composables/api/useResolution'
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry'

export type EffortOutcome = 'saved' | 'copied'

const MAX_EXACT_LENGTH = 4000

/**
 * Character-level edit distance (bounded) between the generated reply and the
 * operator's final text — the basis of the "effort saved" estimate.
 */
export function editDistance(a: string, b: string): number {
  if (a === b) return 0
  if (a.length > MAX_EXACT_LENGTH || b.length > MAX_EXACT_LENGTH) {
    return Math.abs(a.length - b.length)
  }
  if (a.length === 0) return b.length
  if (b.length === 0) return a.length
  const prev = Array.from({ length: b.length + 1 }, (_, i) => i)
  const curr = new Array<number>(b.length + 1)
  for (let i = 1; i <= a.length; i++) {
    curr[0] = i
    for (let j = 1; j <= b.length; j++) {
      const cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1
      curr[j] = Math.min(prev[j]! + 1, curr[j - 1]! + 1, prev[j - 1]! + cost)
    }
    for (let j = 0; j <= b.length; j++) prev[j] = curr[j]!
  }
  return prev[b.length]!
}

/**
 * Manual-effort telemetry for the resolution workspace: how much and how long
 * the operator edits a suggested reply before using it (copy or send), so
 * Analytics can estimate the operator effort saved.
 */
export function useResolutionEffort(
  result: Ref<AssistedResolution | null>,
  response: Ref<string>
) {
  const telemetry = useBenchmarkTelemetry()
  const generatedAtMs = ref<number | null>(null)
  const firstEditMs = ref<number | null>(null)
  const recorded = ref(false)

  watch(response, (value) => {
    if (result.value && firstEditMs.value == null && value !== result.value.response) {
      firstEditMs.value = Date.now()
    }
  })

  function start(): void {
    generatedAtMs.value = Date.now()
    firstEditMs.value = null
    recorded.value = false
  }

  function reset(): void {
    generatedAtMs.value = null
    firstEditMs.value = null
    recorded.value = false
  }

  function buildEffect(current: AssistedResolution, outcome: EffortOutcome, now: number) {
    const generated = current.response ?? ''
    const final = response.value ?? ''
    const changed = editDistance(generated, final)
    const editRatio = Math.min(1, changed / Math.max(generated.length, final.length, 1))
    return {
      page: 'resolution',
      outcome,
      edited: final !== generated,
      edit_ratio: Number(editRatio.toFixed(3)),
      chars_generated: generated.length,
      chars_final: final.length,
      chars_changed: changed,
      edit_duration_ms: firstEditMs.value != null ? now - firstEditMs.value : 0,
      predicted_team: current.predicted_team,
      classification: current.classification
    }
  }

  /** Emit a one-time event when the operator accepts the suggestion. */
  function record(outcome: EffortOutcome): void {
    if (!result.value || recorded.value) return
    recorded.value = true
    const now = Date.now()
    const reviewMs = generatedAtMs.value != null ? now - generatedAtMs.value : 0
    telemetry.recordLab('validate_resolution', 'Ticket', buildEffect(result.value, outcome, now), {
      latency_ms: reviewMs
    })
  }

  return { start, reset, record }
}
