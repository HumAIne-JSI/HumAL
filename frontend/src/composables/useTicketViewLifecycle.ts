/**
 * Emits `view_ticket_start` / `view_ticket_end` telemetry pairs as the
 * currently-selected ticket changes, the tab is hidden, or the component is
 * unmounted. Provides the duration the user spent looking at a given ticket
 * so the dashboard can compute time-on-ticket without each page wiring it
 * manually.
 */
import { onBeforeUnmount, onMounted, watch, type Ref } from 'vue';
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry';

export interface TicketViewLifecycleOptions {
  selectedTicketRef: Ref<string | null | undefined>;
  page: string;
}

export function useTicketViewLifecycle(options: TicketViewLifecycleOptions) {
  const telemetry = useBenchmarkTelemetry();
  const { selectedTicketRef, page } = options;

  let currentTicket: string | null = null;
  let startedAt: number | null = null;

  function start(ticketRef: string) {
    currentTicket = ticketRef;
    startedAt = Date.now();
    telemetry.recordView('view_ticket_start', ticketRef, page);
  }

  function end() {
    if (!currentTicket || startedAt == null) return;
    const durationS = (Date.now() - startedAt) / 1000;
    telemetry.recordView(
      'view_ticket_end',
      currentTicket,
      page,
      { duration_s: durationS },
      { duration_s: durationS },
    );
    currentTicket = null;
    startedAt = null;
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      end();
    } else if (selectedTicketRef.value) {
      start(String(selectedTicketRef.value));
    }
  }

  onMounted(() => {
    if (selectedTicketRef.value) {
      start(String(selectedTicketRef.value));
    }
    document.addEventListener('visibilitychange', handleVisibilityChange);
  });

  watch(selectedTicketRef, (next, prev) => {
    if (prev) end();
    if (next) start(String(next));
  });

  onBeforeUnmount(() => {
    end();
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  });
}
