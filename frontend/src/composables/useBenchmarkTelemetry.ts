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
 */
import { apiService } from '@/services/api';
import { useInstanceStore } from '@/stores/useInstanceStore';
import type { ObjectId, TelemetryEventRequest } from '@/types/api';

// Allow-list mirrors backend AGENT_AFFORDANCES[AgentId.LAB].
const LAB_AFFORDANCES = new Set([
  'confirm_label',
  'override_label',
  'abstain',
  'validate_resolution',
  'select_ticket',
  'inspect_ticket',
  'filter_pool',
  'open_page',
]);

export type LabAction = (typeof LAB_AFFORDANCES extends Set<infer T> ? T : never) | string;

export function useBenchmarkTelemetry() {
  const instanceStore = useInstanceStore();

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
    if (!instanceId) {
      // No active session -> silent no-op
      return Promise.resolve();
    }
    const payload: TelemetryEventRequest = {
      instance_id: instanceId,
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

  return { recordLab };
}
