<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'
import Select from '@/components/ui/Select.vue'
import InstanceSelector from '@/components/InstanceSelector.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import LimeExplanation from '@/components/LimeExplanation.vue'
import SimilarTicketByClass from '@/components/SimilarTicketByClass.vue'
import {
  useInstanceInfo,
  useLabelWithInfo,
} from '@/composables/api/useActiveLearning'
import {
  useInferWithModelCheck,
  useInferTopK,
} from '@/composables/api/useInference'
import {
  useExplainLimeMutation,
  useNearestTicketMutation,
  useNearestTicketsPerClassMutation,
} from '@/composables/api/useXai'
import { useTeams } from '@/composables/api/useData'
import { useCapabilities } from '@/composables/api/useConfig'
import { usePendingLabelerFeedback } from '@/composables/usePendingLabelerFeedback'
import { apiService } from '@/services/api'
import { useInstanceStore } from '@/stores/useInstanceStore'
import type {
  InferenceData,
  InferenceResponse,
  ExplainLimeResponse,
  NearestTicketResponse,
  TopKPrediction,
  PerClassSimilarTicket,
  LabelerFeedbackType,
  TicketAnalysisSource,
} from '@/types/api'
import {
  Search,
  Brain,
  Target,
  FileText,
  Tag,
  Check,
  RefreshCw,
  Coffee,
  AlertTriangle,
  HelpCircle,
  Sparkles,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const instanceStore = useInstanceStore()

// Use store's instance ID with computed wrapper
const selectedInstanceId = computed({
  get: () => instanceStore.selectedInstanceId,
  set: (value: number) => instanceStore.setInstance(value)
})

// Initialize from route query
onMounted(() => {
  const instanceParam = route.query.instance
  if (instanceParam) {
    instanceStore.setInstance(Number(instanceParam))
  }
})

// Sync URL with instance selection
watch(() => instanceStore.selectedInstanceId, (newId) => {
  if (newId > 0) {
    router.replace({ query: { ...route.query, instance: String(newId) } })
  } else {
    const { instance: _, ...rest } = route.query
    router.replace({ query: rest })
  }
})

// Instance data
const { data: instanceInfo } = useInstanceInfo(selectedInstanceId, {
  enabled: computed(() => selectedInstanceId.value > 0),
})

// Mutations
const inferMutation = useInferWithModelCheck(selectedInstanceId, {
  onModelNotTrained: () => {
    toast.error('Model not trained', {
      description: 'Please train the model before running inference',
    })
  },
})

const limeMutation = useExplainLimeMutation(selectedInstanceId)
const nearestMutation = useNearestTicketMutation(selectedInstanceId)

// Top-K + per-class similar tickets (supplementary, capability-gated)
const inferTopKMutation = useInferTopK(selectedInstanceId, 2)
const perClassMutation = useNearestTicketsPerClassMutation(selectedInstanceId)

// Backend capabilities — used to feature-gate optional UI
const { data: capabilities } = useCapabilities()
const capabilitySet = computed(() => new Set(capabilities.value?.capabilities ?? []))
const topKEnabled = computed(() => capabilitySet.value.has('top_k_inference'))
const perClassSimilarEnabled = computed(() =>
  capabilitySet.value.has('similar_tickets_per_class')
)

// Labeling composables
const labelMutation = useLabelWithInfo(selectedInstanceId)
const { data: teamsData } = useTeams(selectedInstanceId, undefined, {
  enabled: computed(() => selectedInstanceId.value > 0),
})

// Labeling mode state
const currentTicketIdx = ref<string | null>(null)
const currentTicketRef = ref<string | null>(null)
const ticketShownAtMs = ref<number | null>(null)
const selectedReassignTeam = ref<string>('')
const isFetchingNextTicket = ref(false)
const { isTired, isDifficult, toggle: togglePendingFeedback, reset: resetPendingFeedback } =
  usePendingLabelerFeedback()

// Input
const ticket = ref<InferenceData>({
  title_anon: '',
  description_anon: '',
})

// Results - use correct API types
const prediction = ref<InferenceResponse | null>(null)
const explanation = ref<ExplainLimeResponse | null>(null)
const nearestResult = ref<NearestTicketResponse | null>(null)

// Top-K + per-class similar tickets (supplementary)
const topKPredictions = ref<TopKPrediction[]>([])
const similarPerClass = ref<PerClassSimilarTicket[]>([])
const isLoadingSimilarPerClass = ref(false)

// Processing states
const isRunning = ref(false)

// Computed
const hasInstance = computed(() => selectedInstanceId.value > 0)
const hasInput = computed(() => !!(ticket.value.title_anon || ticket.value.description_anon))

// Process nearest tickets response into display format
interface NearestTicketDisplay {
  ref: string
  team: string
  similarity: number
}

const nearestTickets = computed((): NearestTicketDisplay[] => {
  if (!nearestResult.value) return []
  const neighbors = [
    ...(nearestResult.value.predicted_class_neighbors ?? []),
    ...(nearestResult.value.historical_neighbors ?? []),
  ]
  return neighbors.map((n) => ({
    ref: n.ref,
    team: n.label ?? 'Unknown',
    similarity: n.similarity ?? 0,
  }))
})

// Map class label -> top-K probability, for surfacing alongside each per-class card
const probabilityByClass = computed((): Record<string, number> => {
  const out: Record<string, number> = {}
  for (const p of topKPredictions.value) {
    out[String(p.label)] = p.probability
  }
  return out
})

// Model's second-best prediction, sent as label-with-info metadata only.
// Prefers the supplementary top-K results (async + capability-gated); falls
// back to the inference probability map so it works even before top-K lands.
const secondModelPrediction = computed<string | null>(() => {
  const topK = topKPredictions.value
  if (topK.length > 0) {
    return topK[1]?.label != null ? String(topK[1].label) : null
  }
  const probabilities = prediction.value?.probabilities
  if (probabilities) {
    const ranked = Object.entries(probabilities).sort((a, b) => b[1] - a[1])
    const second = ranked[1]
    if (second) return second[0]
  }
  return null
})

// Methods
const handleInstanceSelect = (value: string) => {
  instanceStore.setInstance(Number(value) || 0)
  // Clear results on instance change
  prediction.value = null
  explanation.value = null
  nearestResult.value = null
  topKPredictions.value = []
  similarPerClass.value = []
  resetPendingFeedback()
}

const runDispatch = async () => {
  if (!hasInput.value) {
    toast.error('Empty ticket', { description: 'Please enter title or description' })
    return
  }

  isRunning.value = true
  prediction.value = null
  explanation.value = null
  nearestResult.value = null
  topKPredictions.value = []
  similarPerClass.value = []

  try {
    // Build the analysis source: prefer ticket refs when a queue ticket was
    // loaded, fall back to the free-form ticket text otherwise.
    const source: TicketAnalysisSource = currentTicketRef.value
      ? { ticketRefs: [currentTicketRef.value], ticketData: ticket.value }
      : { ticketData: ticket.value }

    // Run inference (primary)
    const inferRes = await inferMutation.mutateAsync(source)
    prediction.value = inferRes

    // Run XAI in parallel - use correct payload structure
    const [limeRes, nearestRes] = await Promise.all([
      limeMutation.mutateAsync({ query_idx: source.ticketRefs, ticket_data: source.ticketData }).catch((e) => {
        console.warn('LIME explanation failed:', e)
        return null
      }),
      nearestMutation.mutateAsync({ query_idx: source.ticketRefs, ticket_data: source.ticketData }).catch((e) => {
        console.warn('Nearest tickets failed:', e)
        return null
      }),
    ])

    explanation.value = limeRes
    nearestResult.value = nearestRes?.[0] ?? null

    // Supplementary, fire-and-forget: top-K predictions → per-class similar tickets.
    // Both are capability-gated and silent — never block the labeling flow.
    if (topKEnabled.value && perClassSimilarEnabled.value) {
      void fetchTopKAndPerClass(source)
    }

    toast.success('Dispatch analysis complete')
  } catch (e) {
    toast.error('Dispatch failed', { description: (e as Error).message })
  } finally {
    isRunning.value = false
  }
}

/**
 * Fire-and-forget: fetch top-K predictions, then their per-class nearest
 * historical tickets. Silent on failure — supplementary signal only.
 */
const fetchTopKAndPerClass = async (source: TicketAnalysisSource) => {
  try {
    const topKRes = await inferTopKMutation.mutateAsync(source)
    const preds = topKRes?.predictions ?? []
    topKPredictions.value = preds

    if (preds.length === 0) return

    isLoadingSimilarPerClass.value = true
    const classLabels = preds.map((p) => String(p.label))
    const perClassRes = await perClassMutation.mutateAsync({
      ticket_data: source.ticketData,
      ticket_refs: source.ticketRefs,
      class_labels: classLabels,
    })
    similarPerClass.value = perClassRes?.items ?? []
  } catch (e) {
    // Silent: supplementary feature
    console.warn('Top-K / per-class similar tickets failed:', e)
  } finally {
    isLoadingSimilarPerClass.value = false
  }
}

const clearAll = () => {
  ticket.value = { title_anon: '', description_anon: '' }
  prediction.value = null
  explanation.value = null
  nearestResult.value = null
  topKPredictions.value = []
  similarPerClass.value = []
  currentTicketIdx.value = null
  currentTicketRef.value = null
  selectedReassignTeam.value = ''
  resetPendingFeedback()
}

// ----- Labeling Mode Methods -----

const availableTeams = computed(() => teamsData.value?.teams ?? [])

const fetchNextTicket = async () => {
  if (!hasInstance.value) return

  isFetchingNextTicket.value = true
  clearAll()

  try {
    // Fetch next ticket index from active learning queue
    const nextData = await apiService.getNextInstances(selectedInstanceId.value, 1)
    const queryIdx = nextData.query_idx
    const rawIdx = queryIdx?.[0]
    if (rawIdx == null) {
      toast.info('No more tickets', { description: 'Active learning queue is empty' })
      return
    }
    const idx = rawIdx.toString()
    currentTicketIdx.value = idx
    ticketShownAtMs.value = Date.now()

    // Fetch ticket details using POST with indices in body
    const ticketData = await apiService.getTickets(selectedInstanceId.value, [idx])
    const t = ticketData.tickets?.[0]
    if (!t) {
      throw new Error('Ticket not found')
    }
    currentTicketRef.value = t.Ref ?? idx

    // Populate form with ticket data
    ticket.value = {
      title_anon: t.Title_anon ?? '',
      description_anon: t.Description_anon ?? '',
      service_name: t['Service->Name'] ?? undefined,
      service_subcategory_name: t['Service subcategory->Name'] ?? undefined,
    }

    toast.success('Ticket loaded', { description: `Ticket ${currentTicketRef.value} ready for labeling` })

    // Auto-run inference if model is trained
    if (hasInput.value) {
      await runDispatch()
    }
  } catch (e) {
    toast.error('Failed to fetch ticket', { description: (e as Error).message })
  } finally {
    isFetchingNextTicket.value = false
  }
}

const confirmPrediction = async () => {
  if (!prediction.value || !currentTicketIdx.value) return

  try {
    const now = Date.now()
    await labelMutation.mutateAsync([
      {
        ticket_id: currentTicketIdx.value,
        label: String(prediction.value.prediction),
        model_prediction: String(prediction.value.prediction),
        second_model_prediction: secondModelPrediction.value,
        start_time: new Date(ticketShownAtMs.value ?? now).toISOString(),
        end_time: new Date(now).toISOString(),
        is_tired: isTired.value ? true : undefined,
        is_difficult: isDifficult.value ? true : undefined,
      },
    ])
    toast.success('Label submitted', { description: 'Proceeding to next ticket' })
    // Fetch next ticket automatically
    await fetchNextTicket()
  } catch (e) {
    toast.error('Failed to confirm', { description: (e as Error).message })
  }
}

const reassignTeam = async () => {
  if (!selectedReassignTeam.value || !currentTicketIdx.value) {
    toast.error('Select a team', { description: 'Please choose a team to reassign' })
    return
  }

  try {
    const now = Date.now()
    await labelMutation.mutateAsync([
      {
        ticket_id: currentTicketIdx.value,
        label: selectedReassignTeam.value,
        model_prediction: prediction.value?.prediction != null ? String(prediction.value.prediction) : undefined,
        second_model_prediction: secondModelPrediction.value,
        start_time: new Date(ticketShownAtMs.value ?? now).toISOString(),
        end_time: new Date(now).toISOString(),
        is_tired: isTired.value ? true : undefined,
        is_difficult: isDifficult.value ? true : undefined,
      },
    ])
    toast.success('Label submitted', { description: 'Proceeding to next ticket' })
    selectedReassignTeam.value = ''
    // Fetch next ticket automatically
    await fetchNextTicket()
  } catch (e) {
    toast.error('Failed to reassign', { description: (e as Error).message })
  }
}

// ----- Labeler Feedback (skip-with-reason) -----

const FEEDBACK_COPY: Record<LabelerFeedbackType, { toast: string; description: string }> = {
  I_AM_TIRED: {
    toast: 'Tired feedback selected',
    description: 'Choose a label to submit this feedback.',
  },
  DIFFICULT_TICKET: {
    toast: 'Difficult feedback selected',
    description: 'Choose a label to submit this feedback.',
  },
  I_DONT_KNOW: {
    toast: "Skipped: don't know",
    description: 'Loading another ticket…',
  },
}

const handleLabelerFeedback = async (type: LabelerFeedbackType) => {
  if (!currentTicketIdx.value) {
    toast.error('No ticket loaded', { description: 'Fetch a ticket first' })
    return
  }

  if (type !== 'I_DONT_KNOW') {
    togglePendingFeedback(type)
    const selected = type === 'I_AM_TIRED' ? isTired.value : isDifficult.value
    const copy = FEEDBACK_COPY[type]
    toast.info(selected ? copy.toast : `${copy.toast} cleared`, {
      description: selected ? copy.description : 'The next label will not include this flag.',
    })
    return
  }

  const now = Date.now()
  try {
    await labelMutation.mutateAsync([
{
        ticket_id: currentTicketIdx.value,
        model_prediction: prediction.value?.prediction != null
          ? String(prediction.value.prediction)
          : undefined,
        second_model_prediction: secondModelPrediction.value,
        start_time: new Date(ticketShownAtMs.value ?? now).toISOString(),
        end_time: new Date(now).toISOString(),
        is_tired: isTired.value ? true : undefined,
        is_difficult: isDifficult.value ? true : undefined,
        i_dont_know: true,
      },
    ])
    const copy = FEEDBACK_COPY[type]
    toast.info(copy.toast, { description: copy.description })
    await fetchNextTicket()
  } catch (e) {
    toast.error('Failed to skip ticket', { description: (e as Error).message })
  }
}
</script>

<template>
  <div class="dispatching">
    <header class="dispatching__header">
      <div class="dispatching__header-content">
        <h1 class="dispatching__title">Dispatch Labeling</h1>
        <p class="dispatching__subtitle">
          Label tickets for active learning training
        </p>
      </div>
      <div class="dispatching__header-actions">
        <InstanceSelector
          :model-value="String(selectedInstanceId || '')"
          placeholder="Select instance..."
          @update:model-value="handleInstanceSelect"
        />
      </div>
    </header>

    <!-- Model Info -->
    <Card v-if="hasInstance && instanceInfo" class="dispatching__model-info" variant="outline" padding="sm">
      <div class="model-info">
        <div class="model-info__details">
          <Badge variant="default">{{ instanceInfo.model_name ?? instanceInfo.model }}</Badge>
          <span class="model-info__strategy">{{ instanceInfo.qs }}</span>
        </div>
        <div class="model-info__metrics">
          <Badge v-if="instanceInfo.test_accuracy !== undefined" variant="success">
            Test Accuracy: {{ (instanceInfo.test_accuracy * 100).toFixed(1) }}%
          </Badge>
        </div>
      </div>
    </Card>

    <!-- No instance selected -->
    <div v-if="!hasInstance" class="dispatching__empty">
      <Brain :size="48" class="dispatching__empty-icon" />
      <h3>No instance selected</h3>
      <p>Select an instance to start labeling tickets</p>
    </div>

    <!-- Main Content: Labeling -->
    <template v-else-if="hasInstance">
      <div class="dispatching__content">
        <!-- Get Next Ticket Section -->
        <Card class="dispatching__input">
          <template #title>
            <Tag :size="18" />
            Active Learning Labeling
          </template>
          <template #description>
            Fetch tickets from the active learning queue and confirm or correct predictions
          </template>

          <!-- Show ticket details if loaded -->
          <div v-if="currentTicketRef" class="labeling-ticket">
            <div class="labeling-ticket__header">
              <Badge variant="outline">Ticket {{ currentTicketRef }}</Badge>
            </div>
            <div class="labeling-ticket__content">
              <div class="labeling-ticket__field">
                <label>Title</label>
                <p>{{ ticket.title_anon || '(No title)' }}</p>
              </div>
              <div class="labeling-ticket__field">
                <label>Description</label>
                <p>{{ ticket.description_anon || '(No description)' }}</p>
              </div>
              <div v-if="ticket.service_name" class="labeling-ticket__field">
                <label>Service</label>
                <p>{{ ticket.service_name }}</p>
              </div>
              <div v-if="ticket.service_subcategory_name" class="labeling-ticket__field">
                <label>Subcategory</label>
                <p>{{ ticket.service_subcategory_name }}</p>
              </div>
            </div>
          </div>

          <div v-else class="labeling-empty">
            <FileText :size="32" class="labeling-empty__icon" />
            <p>Click "Get Next Ticket" to load a ticket from the active learning queue</p>
          </div>

          <template #footer>
            <div class="input-actions">
              <Button variant="ghost" size="sm" @click="clearAll" :disabled="isFetchingNextTicket || isRunning">
                Clear
              </Button>
              <Button @click="fetchNextTicket" :loading="isFetchingNextTicket" variant="outline">
                <RefreshCw :size="16" />
                Get Next Ticket
              </Button>
            </div>
          </template>
        </Card>

        <!-- Prediction & Actions Section (Labeling Mode) -->
        <div v-if="prediction || isRunning" class="dispatching__results">
          <!-- Prediction Card with Labeling Actions -->
          <Card class="results__prediction">
            <template #title>
              <Target :size="18" />
              Prediction
            </template>

            <div v-if="isRunning" class="results__loading">
              <Spinner label="Analyzing ticket..." />
            </div>

            <PredictionResult
              v-else-if="prediction"
              :prediction="prediction.prediction"
              :confidence="prediction.confidence"
              :probabilities="prediction.probabilities"
              show-details
            />

            <!-- Labeling Actions -->
            <div v-if="prediction && !isRunning" class="labeling-actions">
              <div class="labeling-actions__confirm">
                <Button @click="confirmPrediction" :loading="labelMutation.isPending.value" variant="default">
                  <Check :size="16" />
                  Confirm Prediction
                </Button>
              </div>

              <div class="labeling-actions__reassign">
                <span class="labeling-actions__label">Or reassign to:</span>
                <Select
                  v-model="selectedReassignTeam"
                  placeholder="Select team..."
                  :options="availableTeams.map(t => ({ value: t, label: t }))"
                  class="labeling-actions__select"
                />
                <Button
                  @click="reassignTeam"
                  :disabled="!selectedReassignTeam"
                  :loading="labelMutation.isPending.value"
                  variant="outline"
                >
                  Reassign
                </Button>
              </div>

              <!-- Tired/Difficult require a label; I Don't Know retires the ticket. -->
              <div
                v-if="currentTicketIdx"
                class="labeling-actions__feedback"
              >
                <span class="labeling-actions__label">Tired/Difficult feedback (label required):</span>
                <div class="labeling-actions__feedback-row">
                  <Button
                    :variant="isTired ? 'secondary' : 'ghost'"
                    size="sm"
                    :disabled="labelMutation.isPending.value"
                    :aria-pressed="isTired"
                    @click="handleLabelerFeedback('I_AM_TIRED')"
                  >
                    <Coffee :size="16" />
                    I'm Tired
                  </Button>
                  <Button
                    :variant="isDifficult ? 'secondary' : 'ghost'"
                    size="sm"
                    :disabled="labelMutation.isPending.value"
                    :aria-pressed="isDifficult"
                    @click="handleLabelerFeedback('DIFFICULT_TICKET')"
                  >
                    <AlertTriangle :size="16" />
                    Difficult Ticket
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    :loading="labelMutation.isPending.value"
                    :disabled="labelMutation.isPending.value"
                    @click="handleLabelerFeedback('I_DONT_KNOW')"
                  >
                    <HelpCircle :size="16" />
                    I Don't Know
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          <!-- Explanation Card -->
          <Card v-if="explanation || isRunning" class="results__explanation">
            <LimeExplanation
              :explanation="explanation"
              :loading="isRunning"
              collapsible
              :default-expanded="false"
            />
          </Card>

          <!-- Similar Tickets Card -->
          <Card v-if="nearestTickets.length > 0 || isRunning" class="results__similar">
            <template #title>
              <Search :size="18" />
              Similar Past Tickets
            </template>

            <div v-if="isRunning" class="results__loading">
              <Spinner label="Finding similar tickets..." />
            </div>

            <div v-else-if="nearestTickets.length > 0">
              <div
                v-for="(nearTicket, index) in nearestTickets"
                :key="index"
                class="similar-ticket"
              >
                <div class="similar-ticket__header">
                  <Badge variant="outline">{{ nearTicket.team }}</Badge>
                  <span class="similar-ticket__title">{{ nearTicket.ref }}</span>
                  <Badge variant="secondary" class="similar-ticket__similarity">
                    {{ (nearTicket.similarity * 100).toFixed(0) }}% match
                  </Badge>
                </div>
              </div>
            </div>
          </Card>

          <!-- Similar Tickets by Predicted Class (top-K, capability-gated) -->
          <Card
            v-if="perClassSimilarEnabled && topKEnabled && (similarPerClass.length > 0 || isLoadingSimilarPerClass)"
            class="results__per-class"
          >
            <template #title>
              <Sparkles :size="18" />
              Similar Tickets by Predicted Class
            </template>
            <template #description>
              The closest historical ticket for each of the model's top predictions
            </template>

            <div v-if="isLoadingSimilarPerClass && similarPerClass.length === 0" class="results__loading">
              <Spinner label="Looking up similar tickets per class..." />
            </div>

            <div v-else class="per-class-grid">
              <SimilarTicketByClass
                v-for="(item, idx) in similarPerClass"
                :key="`${item.class_label}-${item.ticket_ref}`"
                :item="item"
                :rank="idx + 1"
                :probability="probabilityByClass[item.class_label] ?? null"
              />
            </div>
          </Card>
        </div>
      </div>
    </template>

  </div>
</template>

<style scoped lang="scss">
.dispatching {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    gap: 1rem;
    flex-wrap: wrap;
  }

  &__header-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__title {
    font-size: 1.875rem;
    font-weight: 700;
    margin: 0;
  }

  &__subtitle {
    color: var(--muted-foreground);
    margin: 0;
  }

  &__header-actions {
    display: flex;
    gap: 0.75rem;
    align-items: center;
  }

  &__model-info {
    margin-bottom: 1rem;
  }

  &__warning {
    margin-bottom: 1rem;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    background: var(--muted);
    border-radius: var(--radius);

    h3 {
      margin: 1rem 0 0.5rem;
    }

    p {
      margin: 0;
      color: var(--muted-foreground);
    }
  }

  &__empty-icon {
    color: var(--muted-foreground);
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  &__results {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
}

.model-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;

  &__details {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  &__strategy {
    color: var(--muted-foreground);
    font-size: 0.875rem;
  }

  &__metrics {
    display: flex;
    gap: 0.5rem;
  }
}

.warning-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--warning);
}

.input-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.results__loading {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.results__prediction,
.results__explanation,
.results__similar {
  :deep(.card__title) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
}

.no-similar {
  padding: 1rem;
  text-align: center;
  color: var(--muted-foreground);
  font-size: 0.875rem;
}

.similar-ticket {
  padding: 1rem;
  background: var(--muted);
  border-radius: var(--radius);
  margin-bottom: 0.75rem;

  &:last-child {
    margin-bottom: 0;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  &__title {
    flex: 1;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__similarity {
    font-size: 0.75rem;
  }

  &__description {
    margin: 0.75rem 0 0;
    font-size: 0.875rem;
    color: var(--muted-foreground);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

// Labeling styles
.labeling-ticket {
  &__header {
    margin-bottom: 1rem;
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__field {
    label {
      display: block;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--muted-foreground);
      margin-bottom: 0.25rem;
    }

    p {
      margin: 0;
      font-size: 0.875rem;
      line-height: 1.5;
      color: var(--foreground);
    }
  }
}

.labeling-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: var(--muted-foreground);

  &__icon {
    margin-bottom: 0.75rem;
    opacity: 0.5;
  }

  p {
    margin: 0;
    font-size: 0.875rem;
  }
}

.labeling-actions {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 1rem;

  &__confirm {
    display: flex;
    justify-content: center;
  }

  &__reassign {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  &__label {
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }

  &__select {
    min-width: 200px;
  }

  &__feedback {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding-top: 0.75rem;
    border-top: 1px dashed var(--border);
  }

  &__feedback-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }
}

.per-class-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

</style>
