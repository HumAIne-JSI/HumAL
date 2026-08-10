<template>
  <span class="tutorial-host" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { driver } from 'driver.js'
import type { Config, DriveStep } from 'driver.js'
import 'driver.js/dist/driver.css'
import { useTutorialStore } from '@/stores/useTutorialStore'
import type { TourSegment } from '@/stores/useTutorialStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { useInstanceStore } from '@/stores/useInstanceStore'
import { SEGMENT_ORDER, SEGMENT_ROUTES, TOUR_STEPS } from '@/lib/tutorialSteps'

const tutorial = useTutorialStore()
const auth = useAuthStore()
const instanceStore = useInstanceStore()
const route = useRoute()
const router = useRouter()

let driverInstance: ReturnType<typeof driver> | null = null
let finished = false
let stepBatch: DriveStep[] = []
let instanceWatcher: (() => void) | null = null
let everStarted = false

const EXPAND_EVENT = 'humal:tutorial-expand-sidebar'
const OPEN_FIRST_TICKET_EVENT = 'humal:tutorial-open-first-ticket'

function expandSidebar() {
  window.dispatchEvent(new CustomEvent(EXPAND_EVENT))
}

/** Ask the queue page to open its first ticket so the detail-panel steps
 * (label actions, LIME, predictions, similar tickets) have targets. */
function openFirstTicket() {
  window.dispatchEvent(new CustomEvent(OPEN_FIRST_TICKET_EVENT))
}

function disarmInstanceWatcher() {
  instanceWatcher?.()
  instanceWatcher = null
}

/** Watch the instance picker: completing the "pick a project" step auto-advances. */
function armInstanceWatcher() {
  disarmInstanceWatcher()
  // Disposed when the tour advances; `stop` closes over the watcher handle.
  let stop: (() => void) | null = null
  stop = watch(
    () => instanceStore.selectedInstanceId,
    (id) => {
      if (id > 0) {
        stop?.()
        instanceWatcher = null
        driverInstance?.moveNext()
      }
    },
  )
  instanceWatcher = () => {
    stop?.()
    stop = null
  }
}

/** Clone the static steps, wiring in per-step hooks for auto-advance. */
function buildSteps(segment: TourSegment): DriveStep[] {
  const steps = TOUR_STEPS[segment]
  const indexOfPick = segment === 'project' ? 1 : -1
  return steps.map((step, index) => {
    if (index !== indexOfPick) return step
    return {
      ...step,
      onHighlighted: () => armInstanceWatcher(),
      onDeselected: () => disarmInstanceWatcher(),
    }
  })
}

const driverConfig: Config = {
  animate: true,
  smoothScroll: true,
  showProgress: true,
  allowClose: true,
  overlayColor: '#0f172a',
  overlayOpacity: 0.6,
  skipMissingElement: true,
  waitForElement: 3000,
  popoverClass: 'humal-tour-popover',
  nextBtnText: 'Next',
  prevBtnText: 'Back',
  doneBtnText: 'Done',
  // Clicking outside the highlighted area must NOT dismiss the tour (the
  // user repeatedly opens dropdowns outside the popover). The ✕ button and
  // the Esc key remain available via allowClose.
  overlayClickBehavior: () => {},
  // driver.js does not auto-close when onDoneClick is provided: it calls the
  // hook and stops. Destroy here so "Done" actually closes and chains on.
  onDoneClick: () => {
    finished = true
    driverInstance?.destroy()
  },
  onDestroyed: () => {
    const exitIndex = driverInstance?.getActiveIndex()
    const lastIndex = stepBatch.length - 1
    const completed = finished || (exitIndex != null && exitIndex === lastIndex)
    disarmInstanceWatcher()
    driverInstance = null
    finished = false
    if (completed) {
      advanceChain()
    } else {
      // Aborted: stop the chain, do not mark the intro as seen.
      tutorial.activeTour = null
    }
  },
}

function advanceChain() {
  if (!tutorial.activeTour) return
  const index = SEGMENT_ORDER.indexOf(tutorial.activeTour)
  const next = SEGMENT_ORDER[index + 1]
  if (next) {
    tutorial.activeTour = next
  } else {
    tutorial.markIntroChainSeen()
    tutorial.activeTour = null
  }
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

async function runSegment(segment: TourSegment) {
  if (driverInstance?.isActive()) driverInstance.destroy()
  if (segment === 'project') expandSidebar()

  const routeName = SEGMENT_ROUTES[segment]
  if (route.name !== routeName) {
    await router.push({ name: routeName })
    // Let the page render its container elements before driving.
    await wait(400)
  }

  if (segment === 'manualQueue' || segment === 'ticketQueue') {
    // The queue page selects the first ticket once its list has loaded.
    await wait(200)
    openFirstTicket()
    await wait(600)
  }

  stepBatch = buildSteps(segment)
  finished = false
  driverInstance = driver({ ...driverConfig, steps: stepBatch })
  driverInstance.drive(0)
}

watch(
  () => tutorial.activeTour,
  (segment) => {
    if (segment) void runSegment(segment)
  },
)

// First-run intro: as soon as a signed-in user lands in the app shell and has
// never completed the chain, walk them through it once.
watch(
  () => auth.isAuthenticated,
  (authed) => {
    if (authed && !tutorial.introChainSeen && !everStarted && !route.meta?.standalone) {
      everStarted = true
      setTimeout(() => tutorial.runChain(), 800)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  disarmInstanceWatcher()
  if (driverInstance?.isActive()) driverInstance.destroy()
  driverInstance = null
})
</script>

<style lang="scss">
.tutorial-host {
  display: none;
}

.humal-tour-popover {
  font-family: inherit;

  .driver-popover-title {
    color: var(--foreground, #111827);
  }

  .driver-popover-description {
    color: var(--muted-foreground, #4b5563);
  }

  .driver-popover-close-btn:hover,
  .driver-popover-close-btn:focus {
    color: var(--foreground, #111827);
  }

  .driver-popover-progress-text {
    color: var(--muted-foreground, #6b7280);
  }

  .driver-popover-footer-btn {
    color: var(--foreground, #111827);
    border-color: var(--border, #e5e7eb);
    border-radius: var(--radius, 8px);
  }

  .driver-popover-navigation-btns .driver-popover-footer-btn:last-child {
    background-color: var(--primary, #1d4ed8);
    border-color: var(--primary, #1d4ed8);
    color: white;
  }
}
</style>