/**
 * Click-tracking composable.
 *
 * Mounts a single delegated `click` listener on the page root that walks up
 * the DOM tree from the event target until it finds an element with a
 * `[data-track-region]` attribute. The region name + an optional ticket ref
 * (derived from a sibling `[data-track-ticket-ref]` attribute, or read from
 * the supplied getter) are forwarded to `recordClick`.
 *
 * Usage in a page component:
 *   useClickTracking('queue_aided', () => selectedTicket.value?.ref ?? null)
 *
 * Buttons/sections that participate in tracking only need an attribute:
 *   <div data-track-region="filter_bar">...</div>
 */
import { onBeforeUnmount, onMounted } from 'vue'
import { useBenchmarkTelemetry, type LabPage } from '@/composables/useBenchmarkTelemetry'

const TRACK_ATTR = 'data-track-region'
const TICKET_REF_ATTR = 'data-track-ticket-ref'

export function useClickTracking(
  page: LabPage,
  getTicketRef?: () => string | null | undefined,
) {
  const telemetry = useBenchmarkTelemetry()

  function handleClick(event: MouseEvent) {
    const target = event.target as Element | null
    if (!target || !(target instanceof Element)) return

    const regionEl = target.closest(`[${TRACK_ATTR}]`) as HTMLElement | null
    if (!regionEl) return

    const region = regionEl.getAttribute(TRACK_ATTR) ?? 'unknown'
    const ownRef = regionEl.getAttribute(TICKET_REF_ATTR)
    const ticketRef = ownRef ?? getTicketRef?.() ?? null

    void telemetry.recordClick(region, ticketRef, page)
  }

  onMounted(() => {
    document.body.addEventListener('click', handleClick, { capture: true })
  })

  onBeforeUnmount(() => {
    document.body.removeEventListener('click', handleClick, { capture: true })
  })
}
