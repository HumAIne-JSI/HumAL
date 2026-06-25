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
import { apiService } from '@/services/api';
import { useInstanceStore } from '@/stores/useInstanceStore';
import { useMockModeStore } from '@/stores/useMockModeStore';
import { useTelemetryStore } from '@/stores/useTelemetryStore';
import type { ObjectId, TelemetryEventRequest } from '@/types/api';

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
]);

export type LabAction = (typeof LAB_AFFORDANCES extends Set<infer T> ? T : never) | string;
export type LabPage = 'queue_aided' | 'queue_manual' | 'new_instance' | string;

export function useBenchmarkTelemetry() {
  const instanceStore = useInstanceStore();
  const mockStore = useMockModeStore();
  const telemetryStore = useTelemetryStore();

  function recordLab(
    action: string,
    object: ObjectId,
    effect: Record<string, unknown> = {},
    options: { duration_s?: number; interaction_id?: string } = {},
  ): Promise<void> {
    if (!LAB_AFFORDANCES.has(action)) {
      console.warn('[telemetry] unrecognised LAB action:', action);
      return Promise.resolve();
    }
    const instanceId = instanceStore.selectedInstanceId;
    const resolvedInstanceId = instanceId && instanceId > 0 ? instanceId : null;
    const latencyMs = options.duration_s != null ? Math.round(options.duration_s * 1000) : null;

    // Mock mode: store events client-side so the User Behavior dashboard
    // reflects real interactions without a backend round-trip.
    if (mockStore.mockEnabled) {
      telemetryStore.addEvent({
        al_instance_id: resolvedInstanceId,
        action,
        latency_ms: latencyMs,
        payload: { ...effect, object },
      });
      return Promise.resolve();
    }

    const payload: TelemetryEventRequest = {
      instance_id: resolvedInstanceId,
      action,
      object,
      effect,
      duration_s: options.duration_s ?? null,
      interaction_id: options.interaction_id ?? null,
    };
    return apiService
      .postTelemetryEvent(payload)
      .then(() => undefined)
      .catch((err) => {
        // Telemetry failures must never break the UI.
        console.warn('[telemetry] failed to record event', err);
      });
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
    });
  }

  function recordLabelDecision(args: {
    action: 'confirm_label' | 'override_label';
    ticketRef: string | null;
    page: LabPage;
    label: string;
    prediction?: string | null;
    confidence?: number | null;
    durationMs?: number | null;
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
      },
      {
        duration_s: args.durationMs != null ? args.durationMs / 1000 : undefined,
      },
    );
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
    );
  }

  return { recordLab, recordClick, recordLabelDecision, recordView };
}

