/**
 * Frontend telemetry composable.
 *
 * Emits LAB events (human interactions) into the running benchmark session.
 * No-ops when no instance is selected, so calls are always safe.
 *
 * Usage:
 *   const telemetry = useBenchmarkTelemetry();
 *   telemetry.recordLab('select_ticket', 'Ticket', { ticket_id });
 *   telemetry.recordLab('confirm_label', 'Ticket', { label }, { duration_s });
 *   telemetry.recordClick('confirm_button', 'TKT-1', 'queue_aided');
 *   telemetry.recordLabelDecision({ action: 'confirm_label', ticketRef: 'TKT-1', page: 'queue_aided', label: 'Team A', prediction: 'Team A', confidence: 0.87, durationMs: 4321 });
 */
import { useInstanceStore } from '@/stores/useInstanceStore'
import { useMockModeStore } from '@/stores/useMockModeStore'
import { useTelemetryStore } from '@/stores/useTelemetryStore'
import { useAuthStore } from '@/stores/useAuthStore'
import type { ObjectId } from '@/types/api'

// Allow-list mirrors backend AGENT_AFFORDANCES[AgentId.LAB] + UX-only events
// that the dashboard needs (view_*, run_*, change_*, create_*, tab_change, export).
const LAB_AFFORDANCES = new Set([
  'confirm_label',
  'override_label',
  'abstain',
  'validate_resolution',
  'select_ticket',
  'inspect_ticket',
  'filter_pool',
  'open_page',
  'click',
  // UX/engagement events used by the user-behavior dashboard
  'view_ticket_start',
  'view_ticket_end',
  'view_explanation',
  'dismiss_explanation',
  'view_nearest_ticket',
  'run_prediction',
  'change_model',
  'change_strategy',
  'create_instance',
  'tab_change',
  'export',
  'labeler_feedback',
  // Resource-efficiency latency probes (AI compute time)
  'model_predict',
  'model_train',
  'xai_latency',
  // Ticket-lifecycle events for programme KPIs (AI auto-close, re-open)
  'ticket_auto_closed',
  'ticket_reopened',
])

export type LabAction = (typeof LAB_AFFORDANCES extends Set<infer T> ? T : never) | string
export type LabPage = 'queue_aided' | 'queue_manual' | 'new_instance' | string

export function useBenchmarkTelemetry() {
  const instanceStore = useInstanceStore()
  const mockStore = useMockModeStore()
  const telemetryStore = useTelemetryStore()
  const authStore = useAuthStore()

  function recordLab(
    action: string,
    object: ObjectId,
    effect: Record<string, unknown> = {},
    options: { duration_s?: number; interaction_id?: string; latency_ms?: number } = {},
  ): Promise<void> {
    if (!LAB_AFFORDANCES.has(action)) {
      console.warn('[telemetry] unrecognised LAB action:', action)
      return Promise.resolve()
    }
    const instanceId = instanceStore.selectedInstanceId
    const resolvedInstanceId = instanceId && instanceId > 0 ? instanceId : null
    const latencyMs =
      options.latency_ms != null
        ? Math.round(options.latency_ms)
        : options.duration_s != null
          ? Math.round(options.duration_s * 1000)
          : null

    // Unified pipeline: every tracked interaction is recorded to the local
    // event store in BOTH mock and live mode. Events are tagged with the mode
    // they were captured in so the benchmarking suite can scope each view
    // (mock -> demo/seed data, live -> real tracked interactions) without the
    // two bleeding into each other.
    //
    // In live mode the durable server-of-record for HUMAN DECISIONS is
    // POST /activelearning/{id}/label-with-info (fired from the labelling
    // flows); the humaine-al-api backend has no generic telemetry endpoint, so
    // granular UX events live client-side only.
    telemetryStore.addEvent({
      al_instance_id: resolvedInstanceId,
      action,
      latency_ms: latencyMs,
      payload: { ...effect, object },
      user_id: authStore.user?.user_id || null,
      mock: mockStore.mockEnabled,
    })
    return Promise.resolve()
  }

  /**
   * Record an AI compute-latency probe for the Resource-efficiency pillar.
   * `action` is one of 'model_predict' | 'model_train' | 'xai_latency'.
   */
  function recordLatency(
    action: 'model_predict' | 'model_train' | 'xai_latency',
    latencyMs: number,
    effect: Record<string, unknown> = {},
  ): Promise<void> {
    return recordLab(action, 'Mdl', effect, { latency_ms: latencyMs })
  }

  /**
   * Record that a ticket was managed & closed by the AI without a human
   * decision (programme KPI: "% tickets auto-managed & closed by AI").
   */
  function recordAutoClose(
    ticketRef: string | null,
    page: LabPage,
    extra: Record<string, unknown> = {},
  ): Promise<void> {
    return recordLab('ticket_auto_closed', 'Ticket', { ticket_ref: ticketRef, page, ...extra })
  }

  /**
   * Record that a previously closed ticket was re-opened (programme KPI:
   * "reduction of re-opened tickets").
   */
  function recordReopen(
    ticketRef: string | null,
    page: LabPage,
    extra: Record<string, unknown> = {},
  ): Promise<void> {
    return recordLab('ticket_reopened', 'Ticket', { ticket_ref: ticketRef, page, ...extra })
  }

  function recordClick(
    region: string,
    ticketRef: string | null,
    page: LabPage,
    extra: Record<string, unknown> = {},
  ): Promise<void> {
    return recordLab('click', 'Ticket', {
      click_region: region,
      ticket_ref: ticketRef,
      page,
      ...extra,
    })
  }

  function recordLabelDecision(args: {
    action: 'confirm_label' | 'override_label'
    ticketRef: string | null
    page: LabPage
    label: string
    prediction?: string | null
    confidence?: number | null
    predictionRank?: number | null
    durationMs?: number | null
  }): Promise<void> {
    return recordLab(
      args.action,
      'Ticket',
      {
        ticket_ref: args.ticketRef,
        page: args.page,
        label: args.label,
        prediction: args.prediction ?? null,
        confidence: args.confidence ?? null,
        prediction_rank: args.predictionRank ?? null,
      },
      {
        duration_s: args.durationMs != null ? args.durationMs / 1000 : undefined,
      },
    )
  }

  function recordView(
    action:
      | 'view_ticket_start'
      | 'view_ticket_end'
      | 'view_explanation'
      | 'dismiss_explanation'
      | 'view_nearest_ticket'
      | 'inspect_ticket',
    ticketRef: string | null,
    page: LabPage,
    extra: Record<string, unknown> = {},
    options: { duration_s?: number; interaction_id?: string } = {},
  ): Promise<void> {
    return recordLab(
      action,
      'Ticket',
      {
        ticket_ref: ticketRef,
        page,
        ...extra,
      },
      options,
    )
  }

  return {
    recordLab,
    recordClick,
    recordLabelDecision,
    recordView,
    recordLatency,
    recordAutoClose,
    recordReopen,
  }
}
