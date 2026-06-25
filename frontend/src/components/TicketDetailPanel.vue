<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import Select from '@/components/ui/Select.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import SideBySideExplanation from '@/components/SideBySideExplanation.vue'
import SimilarTicketByClass from '@/components/SimilarTicketByClass.vue'
import { useInferWithModelCheck, useInferTopK } from '@/composables/api/useInference'
import {
  useExplainLimeMutation,
  useNearestTicketMutation,
  useNearestTicketsPerClassMutation,
} from '@/composables/api/useXai'
import { useCapabilities } from '@/composables/api/useConfig'
import { useMockModeStore } from '@/stores/useMockModeStore'
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry'
import { apiService } from '@/services/api'
import type { QueueTicket } from '@/stores/useTicketQueueStore'
import type {
  InferenceData,
  InferenceResponse,
  ExplainLimeResponse,
  NearestTicketResponse,
  TopKPrediction,
  PerClassSimilarTicket,
  LabelerFeedbackType,
} from '@/types/api'
import {
  X,
  FileText,
  Check,
  CheckCircle,
  ChevronRight,
  RefreshCw,
  Coffee,
  AlertTriangle,
  HelpCircle,
  Sparkles,
} from 'lucide-vue-next'

export interface TicketDetailPanelProps {
  ticket: QueueTicket | null
  instanceId: number
  teams?: string[]
  showXai?: boolean
  feedbackPending?: boolean
}

const props = withDefaults(defineProps<TicketDetailPanelProps>(), {
  showXai: true,
  feedbackPending: false,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', team: string, meta: { prediction?: string | null; confidence?: number | null }): void
  (e: 'reassign', team: string, meta: { prediction?: string | null; confidence?: number | null }): void
  (e: 'next'): void
  (e: 'labeled'): void
  (e: 'feedback', type: LabelerFeedbackType): void
}>()

const mockStore = useMockModeStore()
const telemetry = useBenchmarkTelemetry()

// Prediction state
const prediction = ref<InferenceResponse | null>(null)
const explanation = ref<ExplainLimeResponse | null>(null)
const nearestTickets = ref<NearestTicketResponse | null>(null)
const similarTicketBody = ref<{ title?: string; description?: string } | null>(null)
const loadingSimilarBody = ref(false)
const selectedReassignTeam = ref<string>('')
const showLabeledFlash = ref(false)
const labeledTeamName = ref('')
const mockInferring = ref(false)
const mockExplaining = ref(false)
const mockFindingNearest = ref(false)

// Top-K + per-class similar tickets (supplementary, capability-gated)
const topKPredictions = ref<TopKPrediction[]>([])
const similarPerClass = ref<PerClassSimilarTicket[]>([])
const isLoadingSimilarPerClass = ref(false)

// Backend capabilities — feature-gate optional UI. Mock mode bypasses the
// gate so the UX is exercised end-to-end without backend support for the
// new top-K / per-class endpoints.
const { data: capabilities } = useCapabilities()
const capabilitySet = computed(() => new Set(capabilities.value?.capabilities ?? []))
const topKEnabled = computed(() =>
  mockStore.mockEnabled || capabilitySet.value.has('top_k_inference'),
)
const perClassSimilarEnabled = computed(() =>
  mockStore.mockEnabled || capabilitySet.value.has('similar_tickets_per_class'),
)

// ---------------------------------------------------------------------------
// Mock-mode generators. When the user has the global Mock toggle on, the
// real inference / XAI endpoints aren't available, so we fabricate plausible
// (deterministic) data here so the panel — and the labeling-context insights —
// still render end-to-end.
// ---------------------------------------------------------------------------
function hashString(input: string): number {
  let h = 2166136261 >>> 0
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i)
    h = Math.imul(h, 16777619) >>> 0
  }
  return h >>> 0
}
function mulberry32(seed: number) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const MOCK_STOP = new Set([
  'the','and','for','with','that','this','from','have','has','are','was','were',
  'but','not','can','cannot','all','any','will','when','where','what','which',
  'into','about','been','because','just','only','over','under','after','before',
  'their','there','they','them','then','than','these','those','your','please',
  'thanks','need','needs','tried','using','use','get','got','make','made',
])
function mockTokens(text: string): string[] {
  if (!text) return []
  const seen = new Set<string>()
  const out: string[] = []
  for (const w of text.toLowerCase().replace(/[^a-z0-9\s\-]/g, ' ').split(/\s+/)) {
    if (w.length >= 4 && !MOCK_STOP.has(w) && !seen.has(w)) {
      seen.add(w)
      out.push(w)
    }
  }
  return out
}
function mockClassPool(): string[] {
  const pool = (props.teams ?? []).filter((t) => t && t.length > 0)
  if (pool.length >= 2) return pool
  return ['Help Desk L1', 'Help Desk L2', 'Network Team', 'Desktop Support', 'Application Support']
}
function mockSeed(): number {
  const t = props.ticket
  if (!t) return 1
  return hashString(`${t.id}|${t.ref}|${t.title}`)
}
function generateMockPrediction(): InferenceResponse {
  const rng = mulberry32(mockSeed())
  const classes = mockClassPool()
  const i1 = Math.floor(rng() * classes.length)
  let i2 = Math.floor(rng() * classes.length)
  if (i2 === i1) i2 = (i1 + 1) % classes.length
  const p1 = 0.45 + rng() * 0.4
  const remaining = 1 - p1
  const p2 = Math.min(remaining * (0.55 + rng() * 0.35), p1 - 0.02)
  const probabilities: Record<string, number> = {}
  probabilities[classes[i1] as string] = Number(p1.toFixed(3))
  probabilities[classes[i2] as string] = Number(Math.max(0.05, p2).toFixed(3))
  // Distribute the rest as small noise across remaining classes.
  let leftover = Math.max(0, 1 - probabilities[classes[i1] as string]! - probabilities[classes[i2] as string]!)
  const others = classes.filter((_, idx) => idx !== i1 && idx !== i2)
  for (const c of others) {
    const v = leftover * (0.1 + rng() * 0.3)
    probabilities[c] = Number(v.toFixed(3))
    leftover = Math.max(0, leftover - v)
  }
  return {
    prediction: classes[i1] as string,
    confidence: probabilities[classes[i1] as string],
    probabilities,
  }
}
function generateMockLime(): ExplainLimeResponse {
  const rng = mulberry32(mockSeed() ^ 0xa5a5a5a5)
  const tokens = mockTokens(`${props.ticket?.title ?? ''} ${props.ticket?.description ?? ''}`)
  const pool = tokens.length > 0 ? tokens : ['ticket', 'request', 'issue', 'system', 'access', 'report']
  const shuffled = [...pool]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j] as string, shuffled[i] as string]
  }
  const top: [string, number][] = shuffled.slice(0, Math.min(8, shuffled.length)).map((w, idx) => {
    const sign = idx >= 6 && rng() < 0.5 ? -1 : 1
    const mag = (0.85 - idx * 0.08) * (0.7 + rng() * 0.3)
    return [w, Number((sign * Math.max(0.05, mag)).toFixed(3))]
  })
  return [{ top_words: top, error: null }]
}
function generateMockNearest(pred: InferenceResponse): NearestTicketResponse {
  const rng = mulberry32(mockSeed() ^ 0x13572468)
  const refBase = props.ticket?.ref ?? 'TKT-0000'
  return {
    nearest_ticket_ref: `${refBase}-N1`,
    nearest_ticket_label: String(pred.prediction),
    similarity_score: Number((0.72 + rng() * 0.18).toFixed(3)),
  }
}
function generateMockSimilarBody(): { title: string; description: string } {
  const rng = mulberry32(mockSeed() ^ 0x9e3779b9)
  const baseTitle = props.ticket?.title ?? 'Past ticket'
  const baseDesc = props.ticket?.description ?? 'Past ticket description.'
  const variations = [
    'Previously reported — ',
    'Past case: ',
    'Earlier ticket: ',
  ]
  const tail = [
    ' Resolved by reassigning to the responsible team.',
    ' Closed after the requester confirmed the fix.',
    ' Workaround applied while permanent fix was deployed.',
  ]
  const v = variations[Math.floor(rng() * variations.length)] ?? variations[0]!
  const t = tail[Math.floor(rng() * tail.length)] ?? tail[0]!
  return { title: `${v}${baseTitle}`, description: `${baseDesc}${t}` }
}
function generateMockTopK(pred: InferenceResponse): TopKPrediction[] {
  const probs = pred.probabilities ?? {}
  const sorted = Object.entries(probs)
    .map(([label, probability]) => ({ label, probability: Number(probability) }))
    .sort((a, b) => b.probability - a.probability)
  if (sorted.length >= 2) return sorted.slice(0, 2)
  const classes = mockClassPool()
  const primary = String(pred.prediction)
  const secondary = classes.find((c) => c !== primary) ?? `${primary}-Alt`
  return [
    { label: primary, probability: pred.confidence ?? 0.65 },
    { label: secondary, probability: Math.max(0.05, (1 - (pred.confidence ?? 0.65)) * 0.5) },
  ]
}
function generateMockSimilarPerClass(topK: TopKPrediction[]): PerClassSimilarTicket[] {
  const refBase = props.ticket?.ref ?? 'TKT-0000'
  const baseTitle = props.ticket?.title ?? 'Past ticket'
  const baseDesc = props.ticket?.description ?? 'Past ticket description.'
  const sentences = baseDesc
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
  return topK.map((pred, idx) => {
    const rng = mulberry32(mockSeed() ^ (0x51ed270b + idx))
    const sentence =
      sentences[Math.min(idx, sentences.length - 1)] ??
      `User reported a ${pred.label.toLowerCase()} issue similar to this one.`
    const prefix = ['Resolved by ', 'Previously handled by ', 'Past case for '][idx % 3]
    return {
      class_label: pred.label,
      ticket_ref: `${refBase}-C${idx + 1}`,
      title: `${prefix}${pred.label} — ${baseTitle}`.slice(0, 120),
      most_important_sentence: sentence,
      similarity_score: Number((0.62 + rng() * 0.28).toFixed(3)),
    }
  })
}

// Inference mutation
const {
  mutate: runInference,
  isPending: isInferring,
  reset: resetInference,
} = useInferWithModelCheck(computed(() => props.instanceId), {
  onSuccess: (data) => {
    prediction.value = data
    telemetry.recordView(
      'inspect_ticket',
      props.ticket?.ref ?? props.ticket?.id ?? null,
      'queue_aided',
      { prediction: data.prediction, confidence: data.confidence ?? null },
    )
    // Auto-trigger XAI after prediction
    if (props.showXai && props.ticket) {
      runXaiAnalysis()
    }
    // Supplementary, fire-and-forget: top-K predictions → per-class similar tickets.
    if (props.ticket && topKEnabled.value && perClassSimilarEnabled.value) {
      void fetchTopKAndPerClass(buildInferenceData(props.ticket))
    }
  },
})

// Top-K + per-class similar tickets mutations
const inferTopKMutation = useInferTopK(computed(() => props.instanceId), 2)
const perClassMutation = useNearestTicketsPerClassMutation(
  computed(() => props.instanceId),
)

/**
 * Fire-and-forget: fetch top-K predictions, then their per-class nearest
 * historical tickets. Silent on failure — supplementary signal only.
 */
async function fetchTopKAndPerClass(data: InferenceData) {
  try {
    const topKRes = await inferTopKMutation.mutateAsync(data)
    const preds = topKRes?.predictions ?? []
    topKPredictions.value = preds
    if (preds.length === 0) return

    isLoadingSimilarPerClass.value = true
    const classLabels = preds.map((p) => String(p.label))
    const perClassRes = await perClassMutation.mutateAsync({
      ticket_data: data,
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

// Map class label -> top-K probability, for surfacing alongside each per-class card
const probabilityByClass = computed((): Record<string, number> => {
  const out: Record<string, number> = {}
  for (const p of topKPredictions.value) {
    out[String(p.label)] = p.probability
  }
  return out
})

// XAI mutations
const { mutate: explainLime, isPending: isExplainingLime } = useExplainLimeMutation(
  computed(() => props.instanceId),
  {
    onSuccess: (data) => {
      explanation.value = data
      telemetry.recordView(
        'view_explanation',
        props.ticket?.ref ?? props.ticket?.id ?? null,
        'queue_aided',
        { explanation_type: 'lime' },
      )
    },
  }
)

const { mutate: findNearest, isPending: isFindingNearest } = useNearestTicketMutation(
  computed(() => props.instanceId),
  {
    onSuccess: (data) => {
      nearestTickets.value = data
      telemetry.recordView(
        'view_nearest_ticket',
        props.ticket?.ref ?? props.ticket?.id ?? null,
        'queue_aided',
        {
          nearest_ref: Array.isArray(data.nearest_ticket_ref)
            ? data.nearest_ticket_ref[0]
            : data.nearest_ticket_ref,
        },
      )
    },
  }
)

// Team options for reassignment
const teamOptions = computed(() => {
  if (!props.teams?.length) return []
  return props.teams.map((t) => ({ value: t, label: t }))
})

// Confidence level for styling
const confidenceLevel = computed((): 'high' | 'medium' | 'low' => {
  const conf = prediction.value?.confidence
  if (conf === undefined) return 'low'
  if (conf >= 0.8) return 'high'
  if (conf >= 0.5) return 'medium'
  return 'low'
})

const confidenceVariant = computed((): 'success' | 'warning' | 'destructive' => {
  switch (confidenceLevel.value) {
    case 'high':
      return 'success'
    case 'medium':
      return 'warning'
    case 'low':
      return 'destructive'
  }
})

// Combined loading flags (real mutations + mock simulation)
const isInferringAny = computed(() => isInferring.value || mockInferring.value)
const isExplainingAny = computed(() => isExplainingLime.value || mockExplaining.value)
const isFindingNearestAny = computed(() => isFindingNearest.value || mockFindingNearest.value)
// (kept for parity with previous API; may be reused by callers)
const isLoadingXai = computed(() => isExplainingAny.value || isFindingNearestAny.value)
void isLoadingXai

// Build inference data from ticket
function buildInferenceData(ticket: QueueTicket): InferenceData {
  return {
    title_anon: ticket.title,
    description_anon: ticket.description,
    team_name: ticket.team,
    service_name: ticket.category,
    service_subcategory_name: ticket.subcategory,
  }
}

// Run XAI analysis (real or mocked depending on global mock-mode)
function runXaiAnalysis() {
  if (!props.ticket) return
  if (mockStore.mockEnabled) {
    mockExplaining.value = true
    mockFindingNearest.value = true
    const lime = generateMockLime()
    const nearest = prediction.value
      ? generateMockNearest(prediction.value)
      : generateMockNearest(generateMockPrediction())
    const body = generateMockSimilarBody()
    setTimeout(() => {
      explanation.value = lime
      mockExplaining.value = false
      telemetry.recordView(
        'view_explanation',
        props.ticket?.ref ?? props.ticket?.id ?? null,
        'queue_aided',
        { explanation_type: 'lime', mock: true },
      )
    }, 250)
    setTimeout(() => {
      nearestTickets.value = nearest
      similarTicketBody.value = body
      mockFindingNearest.value = false
      const nearestRef = Array.isArray(nearest.nearest_ticket_ref)
        ? nearest.nearest_ticket_ref[0]
        : nearest.nearest_ticket_ref
      telemetry.recordView(
        'view_nearest_ticket',
        props.ticket?.ref ?? props.ticket?.id ?? null,
        'queue_aided',
        { nearest_ref: nearestRef, mock: true },
      )
    }, 350)
    return
  }
  const ticketData = buildInferenceData(props.ticket)
  explainLime({ ticket_data: ticketData })
  findNearest({ ticket_data: ticketData })
}

// Handle prediction request (real or mocked depending on global mock-mode)
function handlePredict() {
  if (!props.ticket) return
  prediction.value = null
  explanation.value = null
  nearestTickets.value = null
  similarTicketBody.value = null
  topKPredictions.value = []
  similarPerClass.value = []
  isLoadingSimilarPerClass.value = false
  if (mockStore.mockEnabled) {
    mockInferring.value = true
    const fake = generateMockPrediction()
    setTimeout(() => {
      prediction.value = fake
      mockInferring.value = false
      telemetry.recordView(
        'inspect_ticket',
        props.ticket?.ref ?? props.ticket?.id ?? null,
        'queue_aided',
        { prediction: fake.prediction, confidence: fake.confidence ?? null, mock: true },
      )
      if (props.showXai) runXaiAnalysis()
      // Fabricate top-K + per-class similar tickets so the panel renders
      // end-to-end in mock mode without backend support.
      const topK = generateMockTopK(fake)
      topKPredictions.value = topK
      isLoadingSimilarPerClass.value = true
      setTimeout(() => {
        similarPerClass.value = generateMockSimilarPerClass(topK)
        isLoadingSimilarPerClass.value = false
      }, 250)
    }, 300)
    return
  }
  runInference(buildInferenceData(props.ticket))
}

// Confirm prediction as label
function handleConfirm() {
  if (!prediction.value) return
  const team = String(prediction.value.prediction)
  labeledTeamName.value = team
  showLabeledFlash.value = true
  emit('confirm', team, {
    prediction: String(prediction.value.prediction),
    confidence: prediction.value.confidence ?? null,
  })
}

// Reassign to different team
function handleReassign() {
  if (!selectedReassignTeam.value) return
  const team = selectedReassignTeam.value
  labeledTeamName.value = team
  showLabeledFlash.value = true
  emit('reassign', team, {
    prediction: prediction.value ? String(prediction.value.prediction) : null,
    confidence: prediction.value?.confidence ?? null,
  })
  selectedReassignTeam.value = ''
}

// Format timestamp
function formatDate(date: Date): string {
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Watch for ticket changes - auto-predict if unlabeled
watch(
  () => props.ticket?.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      // Reset state
      prediction.value = null
      explanation.value = null
      nearestTickets.value = null
      similarTicketBody.value = null
      loadingSimilarBody.value = false
      topKPredictions.value = []
      similarPerClass.value = []
      isLoadingSimilarPerClass.value = false
      selectedReassignTeam.value = ''
      showLabeledFlash.value = false
      labeledTeamName.value = ''
      mockInferring.value = false
      mockExplaining.value = false
      mockFindingNearest.value = false
      resetInference()

      // Auto-predict for unlabeled tickets. In mock mode we don't require a
      // valid instanceId since predictions are fabricated locally.
      const canRun = mockStore.mockEnabled || props.instanceId > 0
      if (props.ticket?.status === 'unlabeled' && canRun) {
        handlePredict()
      }
    }
  },
  { immediate: true }
)

// Computed singular view of the nearest ticket response (the API returns the
// same keys with either scalar or array values depending on entry point).
const nearestSummary = computed(() => {
  const n = nearestTickets.value
  if (!n) return null
  const refVal = Array.isArray(n.nearest_ticket_ref) ? n.nearest_ticket_ref[0] : n.nearest_ticket_ref
  const labelVal = Array.isArray(n.nearest_ticket_label) ? n.nearest_ticket_label[0] : n.nearest_ticket_label
  const simVal = Array.isArray(n.similarity_score) ? n.similarity_score[0] : n.similarity_score
  if (!refVal) return null
  return { ref: String(refVal), label: labelVal ? String(labelVal) : undefined, similarity: typeof simVal === 'number' ? simVal : undefined }
})

// When we have a nearest-ticket ref from the real API, fetch its body so the
// side-by-side view can render the same LIME-highlighted words across both
// tickets. Mock mode fills similarTicketBody directly inside runXaiAnalysis.
watch(nearestSummary, async (summary) => {
  if (!summary || mockStore.mockEnabled) return
  if (props.instanceId <= 0) return
  loadingSimilarBody.value = true
  similarTicketBody.value = null
  try {
    const response = await apiService.getTickets(props.instanceId, [summary.ref])
    const first = response.tickets?.[0]
    if (first) {
      similarTicketBody.value = {
        title: first.Title_anon,
        description: first.Description_anon,
      }
    }
  } catch {
    similarTicketBody.value = null
  } finally {
    loadingSimilarBody.value = false
  }
})

const similarTicketForView = computed(() => {
  if (!nearestSummary.value) return null
  return {
    ref: nearestSummary.value.ref,
    label: nearestSummary.value.label,
    similarity: nearestSummary.value.similarity,
    title: similarTicketBody.value?.title,
    description: similarTicketBody.value?.description,
  }
})

const currentTicketForView = computed(() => ({
  title: props.ticket?.title,
  description: props.ticket?.description,
}))
</script>

<template>
  <Transition name="detail-fade" mode="out-in">
  <div class="detail-panel" v-if="ticket" :key="ticket.id" data-track-region="ticket_detail">
    <!-- Labeled Flash Overlay -->
    <Transition name="flash-fade">
      <div v-if="showLabeledFlash" class="detail-panel__labeled-flash">
        <CheckCircle :size="20" />
        <span>Labeled &mdash; {{ labeledTeamName }}</span>
      </div>
    </Transition>

    <!-- Header -->
    <header class="detail-panel__header">
      <div class="detail-panel__header-row">
        <div class="detail-panel__header-left">
          <span class="detail-panel__ref">{{ ticket.ref }}</span>
          <span class="detail-panel__ref-sep">&middot;</span>
          <Badge v-if="ticket.team" variant="secondary">{{ ticket.team }}</Badge>
          <Badge v-if="ticket.category" variant="outline">{{ ticket.category }}</Badge>
          <span class="detail-panel__time">{{ formatDate(ticket.timestamp) }}</span>
        </div>
        <div class="detail-panel__header-right">
          <Button variant="ghost" size="icon" @click="$emit('next')" title="Next ticket">
            <ChevronRight :size="16" />
          </Button>
          <Button variant="ghost" size="icon" @click="$emit('close')">
            <X :size="16" />
          </Button>
        </div>
      </div>
      <h2 class="detail-panel__title">{{ ticket.title }}</h2>
    </header>

    <!-- Content -->
    <div class="detail-panel__content">
      <!-- Description (plain paragraph, no card wrapper) -->
      <p class="detail-panel__description">{{ ticket.description }}</p>

      <!-- Prediction Section -->
      <section class="detail-panel__prediction">
        <Transition name="prediction-fade" mode="out-in">
        <!-- Loading -->
        <div v-if="isInferringAny" key="loading" class="detail-panel__loading">
          <Progress :value="undefined" />
          <span>Analyzing ticket...</span>
        </div>

        <!-- Prediction Result -->
        <div v-else-if="prediction" key="result" class="detail-panel__prediction-inner" data-track-region="prediction_card">
          <PredictionResult
            :prediction="prediction.prediction"
            :confidence="prediction.confidence"
            :probabilities="prediction.probabilities"
            show-details
            compact
          >
            <template #actions>
              <Button variant="outline" size="sm" data-track-region="confirm_button" @click="handleConfirm">
                <Check :size="14" />
                Confirm
              </Button>
            </template>
          </PredictionResult>

          <!-- Actions row: Reassign + Re-analyze -->
          <div class="detail-panel__actions">
            <div class="detail-panel__reassign" data-track-region="reassign_select">
              <Select
                v-model="selectedReassignTeam"
                placeholder="Reassign to..."
                :options="teamOptions"
                size="sm"
              />
              <Button
                variant="ghost"
                size="sm"
                :disabled="!selectedReassignTeam"
                @click="handleReassign"
              >
                Reassign
              </Button>
            </div>

            <Button
              variant="ghost"
              size="sm"
              @click="handlePredict"
              :disabled="isInferringAny"
              title="Re-analyze"
            >
              <RefreshCw :size="14" :class="{ 'animate-spin': isInferringAny }" />
            </Button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else key="empty" class="detail-panel__empty">
          <Button variant="default" size="sm" @click="handlePredict">
            Analyze Ticket
          </Button>
        </div>
        </Transition>
      </section>

      <!-- Skip-with-reason feedback (always visible; backend call is gated
           by capability + handled by the parent page). -->
      <section class="detail-panel__feedback" data-track-region="labeler_feedback">
        <span class="detail-panel__feedback-label">Skip this ticket:</span>
        <div class="detail-panel__feedback-row">
          <Button
            variant="ghost"
            size="sm"
            :disabled="feedbackPending"
            @click="$emit('feedback', 'I_AM_TIRED')"
          >
            <Coffee :size="14" />
            I'm Tired
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :disabled="feedbackPending"
            @click="$emit('feedback', 'DIFFICULT_TICKET')"
          >
            <AlertTriangle :size="14" />
            Difficult Ticket
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :disabled="feedbackPending"
            @click="$emit('feedback', 'I_DONT_KNOW')"
          >
            <HelpCircle :size="14" />
            I Don't Know
          </Button>
        </div>
      </section>

      <!-- Side-by-side LIME-highlighted comparison (replaces the previous
           XAI tabs + labeling-context insights). Renders the current ticket
           body alongside the nearest already-labeled ticket, with the LIME
           top words highlighted in both columns using the same color scale. -->
      <SideBySideExplanation
        v-if="showXai && prediction"
        :current-ticket="currentTicketForView"
        :similar-ticket="similarTicketForView"
        :lime="explanation"
        :loading-lime="isExplainingAny"
        :loading-similar="isFindingNearestAny || loadingSimilarBody"
      />

      <!-- Similar Tickets by Predicted Class (top-K, capability-gated) -->
      <section
        v-if="perClassSimilarEnabled && topKEnabled && (similarPerClass.length > 0 || isLoadingSimilarPerClass)"
        class="detail-panel__per-class"
        data-track-region="per_class_similar"
      >
        <h3 class="detail-panel__per-class-title">
          <Sparkles :size="16" />
          Similar Tickets by Predicted Class
        </h3>
        <p class="detail-panel__per-class-desc">
          The closest historical ticket for each of the model's top predictions.
        </p>

        <div
          v-if="isLoadingSimilarPerClass && similarPerClass.length === 0"
          class="detail-panel__per-class-loading"
        >
          <Progress :value="undefined" />
          <span>Looking up similar tickets per class...</span>
        </div>

        <div v-else class="detail-panel__per-class-grid">
          <SimilarTicketByClass
            v-for="(item, idx) in similarPerClass"
            :key="`${item.class_label}-${item.ticket_ref}`"
            :item="item"
            :rank="idx + 1"
            :probability="probabilityByClass[item.class_label] ?? null"
          />
        </div>
      </section>
    </div>
  </div>

  <!-- Empty State -->
  <div v-else key="empty" class="detail-panel detail-panel--empty">
    <div class="detail-panel__empty-state">
      <FileText :size="40" class="detail-panel__empty-icon" />
      <p>Select a ticket to view details</p>
    </div>
  </div>
  </Transition>
</template>

<style scoped lang="scss">
.detail-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
  border-left: 1px solid var(--border);
  overflow: hidden;

  &--empty {
    align-items: center;
    justify-content: center;
  }

  &__header {
    padding: 0.625rem 1rem;
    background: var(--card);
    border-bottom: 1px solid var(--border);
  }

  &__header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.375rem;
  }

  &__header-left {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
    min-width: 0;
  }

  &__header-right {
    display: flex;
    align-items: center;
    gap: 0.125rem;
    flex-shrink: 0;
  }

  &__ref {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--muted-foreground);
    text-transform: uppercase;
  }

  &__ref-sep {
    color: var(--muted-foreground);
    font-size: 0.75rem;
  }

  &__time {
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__title {
    margin: 0;
    font-size: 1.0625rem;
    font-weight: 600;
    color: var(--foreground);
    line-height: 1.35;
  }

  &__content {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  &__description {
    margin: 0;
    font-size: 0.9375rem;
    line-height: 1.65;
    color: var(--foreground);
    white-space: pre-wrap;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
  }

  &__prediction {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__prediction-inner {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__labeled-flash {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: color-mix(in srgb, var(--success, #22c55e) 12%, var(--card));
    color: var(--success, #22c55e);
    font-size: 0.8125rem;
    font-weight: 600;
    border-bottom: 1px solid color-mix(in srgb, var(--success, #22c55e) 20%, var(--border));
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1.5rem 1rem;
    text-align: center;
    color: var(--muted-foreground);
    font-size: 0.875rem;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    padding-top: 0.5rem;
  }

  &__reassign {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-left: auto;
  }

  &__empty {
    display: flex;
    justify-content: center;
    padding: 1.5rem 1rem;

    &-icon {
      opacity: 0.4;
    }
  }

  &__empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 2rem;
    text-align: center;
    color: var(--muted-foreground);

    p {
      margin: 0;
      font-size: 0.875rem;
    }
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// Detail panel transition
.detail-fade-enter-active,
.detail-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.detail-fade-enter-from {
  opacity: 0;
  transform: translateX(12px);
}
.detail-fade-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

// Prediction section transition
.prediction-fade-enter-active,
.prediction-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.15s ease;
}
.prediction-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.prediction-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

// Flash overlay transition
.flash-fade-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.flash-fade-leave-active {
  transition: opacity 0.4s ease;
}
.flash-fade-enter-from {
  opacity: 0;
  transform: translateY(-100%);
}
.flash-fade-leave-to {
  opacity: 0;
}

// Skip-with-reason feedback row
.detail-panel__feedback {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 0.75rem 1rem;
  margin: 0 1rem;
  border-top: 1px dashed var(--border);
  border-bottom: 1px dashed var(--border);
}

.detail-panel__feedback-label {
  font-size: 0.8125rem;
  color: var(--muted-foreground);
}

.detail-panel__feedback-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  justify-content: center;
}

// Similar Tickets by Predicted Class
.detail-panel__per-class {
  padding: 0.75rem 1rem 1rem;
  margin: 0 1rem;
  border-top: 1px solid var(--border);
}

.detail-panel__per-class-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0 0 0.25rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--foreground);
}

.detail-panel__per-class-desc {
  margin: 0 0 0.75rem;
  font-size: 0.8125rem;
  color: var(--muted-foreground);
}

.detail-panel__per-class-loading {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: var(--muted-foreground);
}

.detail-panel__per-class-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.5rem;

  @media (min-width: 720px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
