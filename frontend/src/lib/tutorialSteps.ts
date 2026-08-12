import type { DriveStep } from 'driver.js'
import type { TourSegment } from '@/stores/useTutorialStore'

/** Chain order: project → manual queue → aided ticket queue. */
export const SEGMENT_ORDER: TourSegment[] = ['project', 'manualQueue', 'ticketQueue']

/** Route name each segment must run on. */
export const SEGMENT_ROUTES: Record<TourSegment, string> = {
  project: 'home',
  manualQueue: 'manual-queue',
  ticketQueue: 'ticket-queue',
}

/** How long to wait (ms) for an element that only appears after data loads. */
const ELEMENT_TIMEOUT = 15000

/**
 * Steps per segment. The tour acts as an experiment guide: it explains what
 * each part is, why it matters, and what the recorded actions mean — not just
 * where to click. Selectors target stable container elements that exist even
 * while the queues are loading, so the tour never waits on data unless a step
 * explicitly sets a waitForElement.
 */
export const TOUR_STEPS: Record<TourSegment, DriveStep[]> = {
  project: [
    {
      popover: {
        title: 'Welcome to IT Ticket Manager',
        description:
          'This is a labeling study: you classify IT support tickets, sometimes with AI assistance and sometimes on your own. ' +
          'Every decision and its timing is recorded, and your labels retrain the model. ' +
          'A short tour explains each part. Press Next.',
      },
    },
    {
      element: '.sidebar__instance',
      popover: {
        title: 'Pick a project',
        description:
          'All queues work on the selected project. Tickets only load once one is chosen. Select a project now and press Next to continue.',
        side: 'right',
      },
      waitForElement: 3000,
      skipMissingElement: true,
    },
    {
      element: '.experiment-timer',
      popover: {
        title: 'Experiment timer',
        description:
          'A 30/60/90-minute countdown sits in the bottom-right corner. Start it before your session and keep an eye on it. ' +
          'It lets you know when the session is about to end.',
        side: 'top',
      },
      skipMissingElement: true,
    },
    {
      element: '.sidebar__nav',
      popover: {
        title: 'The two queues',
        description:
          'The sidebar opens both labeling flows: the Manual Queue labels WITHOUT AI help ' +
          'and the Ticket Queue labels WITH AI help: ranked suggestions, explanations and similar tickets. We start with the Manual Queue.',
        side: 'right',
      },
    },
  ],

  manualQueue: [
    {
      element: '.ticket-queue__list-panel',
      popover: {
        title: 'Manual Queue',
        description:
          'The AI help is not present here: you label tickets purely from your own expertise. These labels form the human baseline that the assisted ' +
          'session is compared against.',
        side: 'left',
      },
      waitForElement: 3000,
      skipMissingElement: true,
    },
    {
      element: '.ticket-queue__list',
      popover: {
        title: 'The ticket pool',
        description:
          'Click the ticket to open it. We opened the first ticket for you, its details are on the right.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.ticket-queue__detail-panel',
      popover: {
        title: 'The ticket details',
        description:
          'The panel shows the full ticket: header information and the description. The labeling actions for this ticket sit below it.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.manual-detail__label',
      popover: {
        title: 'Pick a team',
        description:
          'Choose a team from the dropdown, then press Confirm. The team you assign is your label for this ticket; ' +
          'confirming moves you to thenext ticket.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '[data-testid="team-guide-trigger"]',
      popover: {
        title: 'Team guide',
        description:
          'A searchable reference of every team and what it handles. If you are unsure what a team covers, you can open it to read the ' +
          'descriptions before confirming a label.',
        side: 'bottom',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.manual-detail__feedback',
      popover: {
        title: 'Tired / Difficult / I Don\u2019t Know',
        description:
          'Three signals the study records. "Tired" and "Difficult" arm a flag that is attached to your next confirmed label. ' +
          'Press one (or both), then confirm a label to submit it; press again to clear it. "I Don\u2019t Know" skips the ticket immediately with no label ' +
          'recorded. Use them honestly: fatigue and ticket difficulty are experimental signals, and skipping is a valid answer.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      popover: {
        title: 'Next: the AI-assisted queue',
        description:
          'That is the full manual loop. Now press Done to see how the model supports labeling with ranked suggestions, explanations and similar tickets.',
      },
    },
  ],

  ticketQueue: [
    {
      element: '.ticket-queue__list-panel',
      popover: {
        title: 'Ticket Queue',
        description:
          'The AI-assisted queue: the model ranks tickets by how much your label is expected to improve it, so you spend effort where it ' +
          'teaches the most.',
        side: 'left',
      },
      waitForElement: 3000,
      skipMissingElement: true,
    },
    {
      element: '.ticket-queue__list',
      popover: {
        title: 'A ranked pool',
        description:
          'Click the ticket to open it. We opened the first ticket for you. Its detail panel now ' +
          'contains the AI help we are about to explain.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.ticket-queue__detail-panel',
      popover: {
        title: 'The aided detail panel',
        description:
          'Three parts: the ticket text on the top left, the model explanation in the top right, and the decision area below them. That is where you accept ' +
          'or override the model\u2019s suggestion. We go through each part.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.detail-panel__lime-column',
      popover: {
        title: 'Model explanation (LIME)',
        description:
          'LIME shows which words influenced the suggestion. Press "Show explanation" to color the ticket text: charcoal words support the ' +
          'predicted class, red words oppose it.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.detail-panel__prediction',
      popover: {
        title: 'The decision area',
        description:
          'This section appears once the model has a suggestion for the open ticket and holds everything you need to act: the top ' +
          'predictions, manual reassignment, feedback buttons and the Team guide.',
        side: 'bottom',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.detail-panel__model-predictions',
      popover: {
        title: 'Top predictions',
        description:
          'The model\u2019s ranked suggestions with their confidence as a percentage. Press Confirm next to the one you agree with to accept ' +
          'it as the label.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.detail-panel__reassign',
      popover: {
        title: 'Manual reassignment',
        description:
          'Disagree with the model? Pick the correct team and press Reassign. This overrides the suggestion. While a reassignment is armed, ' +
          'the model\u2019s Confirm buttons are disabled. Reassigning records where the AI went wrong so the model can learn from your correction.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '[data-testid="team-guide-trigger"]',
      popover: {
        title: 'Team guide',
        description:
          'A searchable reference of every team and what it handles. If you are unsure what a team covers, you can open it to read the ' +
          'descriptions before confirming or reassigning a label.',
        side: 'bottom',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.detail-panel__feedback',
      popover: {
        title: 'Tired / Difficult / I Don\u2019t Know',
        description:
          'The same honest signals as the manual queue: "Tired" and "Difficult" arm a flag recorded with your NEXT confirmed label (press ' +
          'again to clear); "I Don\u2019t Know" skips the ticket immediately. These tell the study when fatigue or hard tickets affect labeling.',
        side: 'left',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      element: '.side-by-side',
      popover: {
        title: 'Two views of similar tickets',
        description:
          'Once the suggestion is ready, similar tickets appear in two columns with different meanings: "Closest past tickets" are the most ' +
          'similar tickets no matter their class. "Closest predicted class tickets" are similar ' +
          'tickets that already belong to the model\u2019s suggested class. It tells us if the AI\u2019s pick fits.',
        side: 'top',
      },
      waitForElement: ELEMENT_TIMEOUT,
      skipMissingElement: true,
    },
    {
      popover: {
        title: 'You have seen the whole loop',
        description:
          'The model ranks and explains, you decide. Confirm, Reassign, or skip, every decision and timing is logged, and your labels ' +
          'retrain the model for the next round. Happy labeling!',
      },
    },
  ],
}