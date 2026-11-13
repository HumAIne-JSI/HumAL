<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { toast } from 'vue-sonner'
import ResolutionSteps, { type ResolutionStage } from '@/components/ResolutionSteps.vue'
import ResolutionIntake from '@/components/ResolutionIntake.vue'
import ResolutionTicketSummary from '@/components/ResolutionTicketSummary.vue'
import ResolutionDraft from '@/components/ResolutionDraft.vue'
import ResolutionSimilarReplies from '@/components/ResolutionSimilarReplies.vue'
import ResolutionSent from '@/components/ResolutionSent.vue'
import type { LoadingPhaseStep } from '@/components/ui/LoadingPhase.vue'
import { useLoadingPhase } from '@/composables/useLoadingPhase'
import { useResolutionEffort } from '@/composables/useResolutionEffort'
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry'
import { useInfer } from '@/composables/api/useInference'
import {
  useAssistedResolution,
  useResolutionFeedback,
  useFeedbackStats,
  useSaveResolvedTicket,
  DEFAULT_RESOLUTION_TOP_K,
  type AssistedResolution
} from '@/composables/api/useResolution'
import { useAuthStore } from '@/stores/useAuthStore'
import { useLabeledTicketsStore, type LabeledTicket } from '@/stores/useLabeledTicketsStore'
import type { ResolutionSimilarReply, ResolutionFeedbackStatsResponse } from '@/types/api'

type VoteLabel = 0 | 1

interface DraftSnapshot {
  text: string
  reason: string
}

const authStore = useAuthStore()
const telemetry = useBenchmarkTelemetry()
const labeledStore = useLabeledTicketsStore()

const pageRef = ref<HTMLElement | null>(null)
const stage = ref<ResolutionStage>('intake')

// Ticket
const ticketTitle = ref('')
const ticketDescription = ref('')
const topK = ref(DEFAULT_RESOLUTION_TOP_K)
const selectedCategory = ref('')
const selectedSubcategory = ref('')
// Optional Active-Learning bridge: a trained instance predicts the team before
// resolving, sharpening retrieval + judging.
const selectedInstanceId = ref(0)
// A labeled ticket pulled from the queue: its human label is reused as the
// predicted-team hint, taking priority over model inference.
const presetTeam = ref('')
const selectedLabeledRef = ref('')
// A team the specialist picked via "Reassign"; it outranks every other hint so
// regenerating never silently reverts the decision.
const manualTeam = ref('')

// Draft
const result = ref<AssistedResolution | null>(null)
const editedResponse = ref('')
const undoSnapshot = ref<DraftSnapshot | null>(null)
const appliedReplyId = ref<string | null>(null)
const intakeError = ref<string | null>(null)
const draftError = ref<string | null>(null)
const phaseSteps = ref<LoadingPhaseStep[]>([])

// Per-reply feedback: retrieved_id -> submitted vote / in-flight vote / stats.
const votes = ref<Record<string, VoteLabel>>({})
const pendingVotes = ref<Record<string, VoteLabel>>({})
const stats = ref<Record<string, ResolutionFeedbackStatsResponse>>({})
// A stable id grouping all feedback from one generated resolution.
const queryId = ref('')

const { currentPhase, isLoading, startPhase, reset: resetPhase } = useLoadingPhase()
const effort = useResolutionEffort(result, editedResponse)

const assisted = useAssistedResolution({ meta: { silent: true } })
const inferMutation = useInfer(selectedInstanceId, { meta: { silent: true } })
const feedbackMutation = useResolutionFeedback({ meta: { silent: true } })
const statsMutation = useFeedbackStats({ meta: { silent: true } })
const saveMutation = useSaveResolvedTicket({ meta: { silent: true } })

const isResolving = computed(() => assisted.isPending.value || inferMutation.isPending.value)
const isSaving = computed(() => saveMutation.isPending.value)
const isBusy = computed(() => isResolving.value || isSaving.value)
// Steps the stepper may jump to; locked while a request runs, like "Edit ticket".
const reachableStages = computed<ResolutionStage[]>(() => {
  if (isBusy.value) return []
  if (stage.value === 'sent') return ['intake']
  return result.value ? ['intake', 'review'] : ['intake']
})
const nextQueuedTicket = computed<LabeledTicket | null>(() => labeledStore.tickets[0] ?? null)
const willPredictTeam = computed(
  () => !manualTeam.value && !presetTeam.value && selectedInstanceId.value > 0
)

const exportData = computed(() => {
  if (!result.value) return []
  return [
    {
      title: ticketTitle.value,
      description: ticketDescription.value,
      category: selectedCategory.value,
      subcategory: selectedSubcategory.value,
      classification: result.value.classification,
      predicted_team: result.value.predicted_team,
      team_confidence: result.value.team_confidence,
      response: editedResponse.value,
      similar_count: result.value.similar_replies.length
    }
  ]
})

const errorMessage = (error: unknown): string | undefined =>
  error instanceof Error ? error.message : undefined

// Generation: (predict team) → draft reply → load feedback stats.
function beginGeneration(): void {
  intakeError.value = null
  draftError.value = null
  phaseSteps.value = [
    ...(willPredictTeam.value ? [{ id: 'classifying', label: 'Predicting team' }] : []),
    { id: 'generating', label: 'Drafting reply' },
    { id: 'retrieving', label: 'Loading feedback' }
  ]
  startPhase(willPredictTeam.value ? 'classifying' : 'generating')
  stage.value = 'review'
}

// A regenerate may start while the previous run is still loading feedback;
// only the latest run may reset the shared progress indicator.
let generationRun = 0

async function generate(): Promise<void> {
  if (isBusy.value) return
  const run = ++generationRun
  beginGeneration()
  try {
    const data = await requestDraft(await predictTeam())
    applyResult(data)
    await loadFeedback(data.similar_replies)
  } catch (error) {
    handleGenerateError(error)
  } finally {
    if (run === generationRun) resetPhase()
  }
}

// Prefer a manual reassignment, then the human label from the queue; otherwise
// best-effort AL inference.
async function predictTeam(): Promise<string | undefined> {
  const hint = manualTeam.value || presetTeam.value
  if (hint) return hint
  if (!willPredictTeam.value) return undefined
  try {
    const inference = await inferMutation.mutateAsync({
      title_anon: ticketTitle.value,
      description_anon: ticketDescription.value
    })
    return inference.prediction != null ? String(inference.prediction) : undefined
  } catch {
    // Inference is optional; the resolution API classifies on its own.
    return undefined
  }
}

function requestDraft(predictedTeam: string | undefined): Promise<AssistedResolution> {
  startPhase('generating')
  return assisted.mutateAsync({
    title: ticketTitle.value,
    description: ticketDescription.value,
    top_k: topK.value,
    predicted_team: predictedTeam
  })
}

function applyResult(data: AssistedResolution): void {
  if (result.value) snapshotDraft('A new draft replaced your previous text.', data.response)
  result.value = data
  editedResponse.value = data.response
  votes.value = {}
  stats.value = {}
  appliedReplyId.value = null
  queryId.value = crypto.randomUUID()
  effort.start()
  telemetry.recordLab('run_prediction', 'Ticket', {
    page: 'resolution',
    classification: data.classification,
    predicted_team: data.predicted_team
  })
}

async function loadFeedback(replies: ResolutionSimilarReply[]): Promise<void> {
  if (!replies.length) return
  startPhase('retrieving')
  await Promise.all(replies.map((reply) => refreshStats(reply.retrieved_id)))
}

// Responses that arrive after the draft was replaced belong to a stale query.
async function refreshStats(retrievedId: string): Promise<void> {
  const qid = queryId.value
  try {
    const data = await statsMutation.mutateAsync({ retrievedId })
    if (queryId.value === qid) stats.value[retrievedId] = data
  } catch {
    // Feedback stats are non-critical decoration.
  }
}

// A failed first draft returns to the ticket; a failed regenerate keeps the draft.
function handleGenerateError(error: unknown): void {
  const message = errorMessage(error) ?? 'Unable to reach the resolution service.'
  if (result.value) {
    draftError.value = message
    return
  }
  intakeError.value = message
  stage.value = 'intake'
}

async function vote(reply: ResolutionSimilarReply, label: VoteLabel): Promise<void> {
  const id = reply.retrieved_id
  const current = result.value
  if (!current || id in pendingVotes.value) return
  const qid = queryId.value
  pendingVotes.value[id] = label
  try {
    await feedbackMutation.mutateAsync({
      query_id: qid,
      retrieved_id: id,
      label,
      predicted_class: current.predicted_class,
      predicted_team: current.predicted_team,
      user_id: authStore.user?.user_id
    })
    if (queryId.value !== qid) return
    votes.value[id] = label
    await refreshStats(id)
  } catch (error) {
    toast.error('Could not save feedback', { description: errorMessage(error) })
  } finally {
    delete pendingVotes.value[id]
  }
}

// Keep replaced text so "Use in draft" and regenerate are never destructive.
function snapshotDraft(reason: string, nextText: string): void {
  const current = editedResponse.value
  undoSnapshot.value = current.trim() && current !== nextText ? { text: current, reason } : null
}

function applyReply(reply: ResolutionSimilarReply): void {
  if (!reply.first_reply) return
  snapshotDraft('Draft replaced with a past reply.', reply.first_reply)
  editedResponse.value = reply.first_reply
  appliedReplyId.value = reply.retrieved_id
}

function undoReplace(): void {
  if (!undoSnapshot.value) return
  editedResponse.value = undoSnapshot.value.text
  undoSnapshot.value = null
  appliedReplyId.value = null
}

function onDraftEdited(): void {
  undoSnapshot.value = null
  appliedReplyId.value = null
}

function reassignTeam(team: string): void {
  manualTeam.value = team
  if (result.value) result.value.predicted_team = team
}

// The review stage is locked while saving; the queue ref is still captured so
// the ticket that was actually sent is the one removed from the queue.
async function sendToTeam(): Promise<void> {
  const current = result.value
  if (!current || isBusy.value) return
  const ticketRef = selectedLabeledRef.value
  try {
    await saveMutation.mutateAsync({
      title: ticketTitle.value,
      description: ticketDescription.value,
      response: editedResponse.value,
      predicted_team: current.predicted_team,
      predicted_classification: current.classification,
      service_name: selectedCategory.value || undefined,
      service_subcategory: selectedSubcategory.value || undefined
    })
    effort.record('saved')
    if (ticketRef) labeledStore.remove(ticketRef)
    stage.value = 'sent'
  } catch (error) {
    toast.error('Could not send to the team', { description: errorMessage(error) })
  }
}

function resetResult(): void {
  result.value = null
  editedResponse.value = ''
  manualTeam.value = ''
  undoSnapshot.value = null
  appliedReplyId.value = null
  votes.value = {}
  stats.value = {}
  queryId.value = ''
  intakeError.value = null
  draftError.value = null
  effort.reset()
  resetPhase()
}

// Load a labeled ticket from the queue for review (no auto-generate).
function loadTicket(ticket: LabeledTicket): void {
  ticketTitle.value = ticket.title
  ticketDescription.value = ticket.description
  selectedCategory.value = ticket.category ?? ''
  selectedSubcategory.value = ticket.subcategory ?? ''
  presetTeam.value = ticket.label
  selectedLabeledRef.value = ticket.ref
  resetResult()
}

// Detach the queue association but keep the typed text for manual resolving.
function unlinkTicket(): void {
  presetTeam.value = ''
  selectedLabeledRef.value = ''
}

function clearForm(): void {
  ticketTitle.value = ''
  ticketDescription.value = ''
  selectedCategory.value = ''
  selectedSubcategory.value = ''
  topK.value = DEFAULT_RESOLUTION_TOP_K
  unlinkTicket()
  resetResult()
}

function resolveNextTicket(): void {
  if (nextQueuedTicket.value) loadTicket(nextQueuedTicket.value)
  stage.value = 'intake'
}

function startNewTicket(): void {
  clearForm()
  stage.value = 'intake'
}

// A sent draft is already saved, so going back to step 1 afterwards starts a fresh ticket.
function goToStage(target: ResolutionStage): void {
  if (!reachableStages.value.includes(target)) return
  if (stage.value === 'sent') startNewTicket()
  else stage.value = target
}

// Move focus to the new step's heading, and bring the page top into view.
function onStageEntered(el: Element): void {
  el.querySelector<HTMLElement>('[data-stage-heading]')?.focus({ preventScroll: true })
  const page = pageRef.value
  if (!page || page.getBoundingClientRect().top >= 0) return
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  page.scrollIntoView({ block: 'start', behavior: reduceMotion ? 'auto' : 'smooth' })
}

onMounted(() => {
  telemetry.recordLab('open_page', 'Ticket', { page: 'resolution' })
})
</script>

<template>
  <div ref="pageRef" class="resolution">
    <header class="resolution__header">
      <div class="resolution__intro">
        <h1 class="resolution__title">Specialist Resolution Workspace</h1>
        <p class="resolution__subtitle">
          After a ticket is routed to a team, Tier 2 Support gets a suggested first reply based on
          similar past tickets.
        </p>
      </div>
      <ResolutionSteps :current="stage" :reachable="reachableStages" @select="goToStage" />
    </header>

    <Transition name="stage" mode="out-in" @after-enter="onStageEntered">
      <div v-if="stage === 'intake'" key="intake" class="stage stage--intake">
        <ResolutionIntake
          v-model:title="ticketTitle"
          v-model:description="ticketDescription"
          v-model:instance-id="selectedInstanceId"
          v-model:top-k="topK"
          v-model:category="selectedCategory"
          v-model:subcategory="selectedSubcategory"
          :disabled="isResolving"
          :has-draft="!!result"
          :error="intakeError"
          :queue-ref="selectedLabeledRef"
          :queue-team="presetTeam"
          @generate="generate"
          @clear="clearForm"
          @pick-ticket="loadTicket"
          @unlink-ticket="unlinkTicket"
          @back-to-draft="stage = 'review'"
        />

        <aside class="guide" aria-labelledby="resolution-guide-title">
          <h2 id="resolution-guide-title" class="guide__title">How it works</h2>
          <ol class="guide__list">
            <li>
              <strong>Choose a ticket.</strong>
              Pick a labeled one from the queue, or describe a new one.
            </li>
            <li>
              <strong>Review the draft.</strong>
              Edit the suggested reply and compare it with similar past replies.
            </li>
            <li>
              <strong>Send it to the team.</strong>
              The final reply is saved to the knowledge base to improve future suggestions.
            </li>
          </ol>
        </aside>
      </div>

      <div v-else-if="stage === 'review'" key="review" class="stage stage--review">
        <ResolutionTicketSummary
          class="stage__summary"
          :title="ticketTitle"
          :description="ticketDescription"
          :ticket-ref="selectedLabeledRef"
          :category="selectedCategory"
          :subcategory="selectedSubcategory"
          :disabled="isBusy"
          @edit="stage = 'intake'"
        />

        <ResolutionDraft
          v-model:response="editedResponse"
          class="stage__draft"
          :result="result"
          :drafting="isResolving"
          :show-progress="isLoading"
          :phase="currentPhase"
          :phases="phaseSteps"
          :saving="isSaving"
          :undo-reason="undoSnapshot?.reason ?? null"
          :error="draftError"
          :export-data="exportData"
          @edit="onDraftEdited"
          @copied="effort.record('copied')"
          @regenerate="generate"
          @undo="undoReplace"
          @dismiss-undo="undoSnapshot = null"
          @dismiss-error="draftError = null"
          @send="sendToTeam"
          @reassign="reassignTeam"
        />

        <ResolutionSimilarReplies
          class="stage__evidence"
          :replies="result?.similar_replies ?? []"
          :loading="!result"
          :disabled="isBusy"
          :votes="votes"
          :pending-votes="pendingVotes"
          :stats="stats"
          :applied-id="appliedReplyId"
          @use-reply="applyReply"
          @vote="vote"
        />
      </div>

      <div v-else key="sent" class="stage stage--sent">
        <ResolutionSent
          :team="result?.predicted_team ?? 'the team'"
          :title="ticketTitle"
          :ticket-ref="selectedLabeledRef"
          :response="editedResponse"
          :next-ticket="nextQueuedTicket"
          :remaining="labeledStore.tickets.length"
          @next="resolveNextTicket"
          @new-ticket="startNewTicket"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.resolution {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.resolution__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem 2rem;
  margin-bottom: 1.75rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
}

.resolution__intro {
  flex: 1 1 26rem;
  min-width: 0;
}

.resolution__title {
  margin: 0;
  font-size: 1.875rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.resolution__subtitle {
  max-width: 40rem;
  margin: 0.375rem 0 0;
  color: var(--muted-foreground);
}

.stage--intake {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 16rem;
  align-items: start;
  gap: 1.5rem;
}

.guide {
  padding: 0.25rem 0 0;
}

.guide__title {
  margin: 0 0 0.875rem;
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted-foreground);
}

.guide__list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
  counter-reset: guide;

  li {
    position: relative;
    padding-left: 2rem;
    font-size: 0.8125rem;
    line-height: 1.5;
    color: var(--muted-foreground);
    counter-increment: guide;

    &::before {
      content: counter(guide);
      position: absolute;
      top: 0;
      left: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 1.375rem;
      height: 1.375rem;
      border: 1px solid var(--border);
      border-radius: 999px;
      font-size: 0.6875rem;
      font-weight: 600;
      color: var(--foreground);
    }
  }

  strong {
    display: block;
    color: var(--foreground);
    font-weight: 600;
  }
}

.stage--review {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 380px);
  grid-template-rows: auto 1fr;
  grid-template-areas:
    'draft summary'
    'draft evidence';
  align-items: start;
  gap: 1.25rem 1.5rem;
}

.stage__summary {
  grid-area: summary;
}

.stage__draft {
  grid-area: draft;
}

.stage__evidence {
  grid-area: evidence;
}

// Keep the draft in view while scanning evidence, only where it fits the screen.
@media (min-width: 1100px) and (min-height: 820px) {
  .stage__draft {
    position: sticky;
    top: 1rem;
    --draft-editor-max: calc(100vh - 34rem);
  }
}

.stage-enter-active {
  transition:
    opacity 0.2s ease-out,
    transform 0.2s ease-out;
}

.stage-leave-active {
  transition: opacity 0.12s ease-in;
}

.stage-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.stage-leave-to {
  opacity: 0;
}

@media (max-width: 1023px) {
  .stage--review {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: none;
    grid-template-areas:
      'summary'
      'draft'
      'evidence';
  }
}

@media (max-width: 900px) {
  .stage--intake {
    grid-template-columns: minmax(0, 1fr);
  }

  .guide {
    padding: 0 0.25rem;
  }
}

@media (max-width: 640px) {
  .resolution {
    padding: 0.5rem 0 1.5rem;
  }

  .resolution__header {
    margin-bottom: 1.25rem;
  }

  .resolution__title {
    font-size: 1.5rem;
  }

  .resolution__subtitle {
    font-size: 0.875rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .stage-enter-active,
  .stage-leave-active {
    transition: none;
  }

  .stage-enter-from {
    transform: none;
  }
}
</style>
