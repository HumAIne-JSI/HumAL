<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'
import Select from '@/components/ui/Select.vue'
import LimeHighlightedText from '@/components/LimeHighlightedText.vue'
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
  Neighbor,
  NearestTicketResponse,
  TopKPrediction,
  PerClassSimilarTicket,
  LabelerFeedbackType,
  TicketAnalysisSource,
} from '@/types/api'
import {
  X,
  FileText,
  Check,
  CheckCircle,
  ChevronRight,
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
  isTired?: boolean
  isDifficult?: boolean
}

const props = withDefaults(defineProps<TicketDetailPanelProps>(), {
  showXai: true,
  feedbackPending: false,
  isTired: false,
  isDifficult: false,
})

const emit = defineEmits<{
  (e: 'close'): void
  (
    e: 'confirm',
    team: string,
    meta: {
      prediction?: string | null
      secondPrediction?: string | null
      confidence?: number | null
      predictionRank?: number
    },
  ): void
  (
    e: 'reassign',
    team: string,
    meta: { prediction?: string | null; secondPrediction?: string | null; confidence?: number | null },
  ): void
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
const neighborTicketBodies = ref<Record<string, { title?: string; description?: string }>>({})
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

// Backend capabilities gate only the optional per-class similar-ticket UI.
// Ranked predictions are a required queue input and come from infer_proba.
const { data: capabilities } = useCapabilities()
const capabilitySet = computed(() => new Set(capabilities.value?.capabilities ?? []))
const perClassSimilarEnabled = computed(
  () => mockStore.mockEnabled || capabilitySet.value.has('similar_tickets_per_class'),
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
  'the',
  'and',
  'for',
  'with',
  'that',
  'this',
  'from',
  'have',
  'has',
  'are',
  'was',
  'were',
  'but',
  'not',
  'can',
  'cannot',
  'all',
  'any',
  'will',
  'when',
  'where',
  'what',
  'which',
  'into',
  'about',
  'been',
  'because',
  'just',
  'only',
  'over',
  'under',
  'after',
  'before',
  'their',
  'there',
  'they',
  'them',
  'then',
  'than',
  'these',
  'those',
  'your',
  'please',
  'thanks',
  'need',
  'needs',
  'tried',
  'using',
  'use',
  'get',
  'got',
  'make',
  'made',
])
const NEAREST_TICKET_TOP_K = 2
function mockTokens(text: string): string[] {
  if (!text) return []
  const seen = new Set<string>()
  const out: string[] = []
  for (const w of text
    .toLowerCase()
    .replace(/[^a-z0-9\s\-]/g, ' ')
    .split(/\s+/)) {
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
  let leftover = Math.max(
    0,
    1 - probabilities[classes[i1] as string]! - probabilities[classes[i2] as string]!,
  )
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
  const pool =
    tokens.length > 0 ? tokens : ['ticket', 'request', 'issue', 'system', 'access', 'report']
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
  return [
    {
      text: `${props.ticket?.title ?? ''} ${props.ticket?.description ?? ''}`.trim(),
      prediction: { label: '', probabilities: {} },
      word_weights: top.map(([word, weight]) => ({ word, weight })),
      highlighted_tokens: [],
      index: props.ticket?.ref ?? '',
      error: null,
      class_explanations: [],
    },
  ]
}
function generateMockNearest(pred: InferenceResponse): NearestTicketResponse {
  const rng = mulberry32(mockSeed() ^ 0x13572468)
  const refBase = props.ticket?.ref ?? 'TKT-0000'
  const makeNeighbor = (role: 'H' | 'P', index: number, label: string) => {
    const body = generateMockSimilarBody()
    const description =
      `${body.description} ${index === 1 ? 'A second related case was reviewed for comparison.' : ''}`.trim()
    return {
      ref: `${refBase}-${role}${index + 1}`,
      label,
      similarity: Number((0.68 + rng() * 0.18 - index * 0.08).toFixed(3)),
      title: `${body.title} ${index + 1}`,
      description,
      best_sentence: firstSentence(description),
    }
  }
  const historicalNeighbors = [
    makeNeighbor('H', 0, 'Previously resolved'),
    makeNeighbor('H', 1, 'Previously resolved'),
  ]
  const predictedClassNeighbors = [
    makeNeighbor('P', 0, String(pred.prediction)),
    makeNeighbor('P', 1, String(pred.prediction)),
  ]
  return {
    query_idx: null,
    predicted_class_neighbors: predictedClassNeighbors,
    historical_neighbors: historicalNeighbors,
  }
}
/** First available neighbour across predicted-class then historical lists. */
function firstNeighbor(n: NearestTicketResponse | null) {
  if (!n) return null
  return n.predicted_class_neighbors?.[0] ?? n.historical_neighbors?.[0] ?? null
}
function generateMockSimilarBody(): { title: string; description: string } {
  const rng = mulberry32(mockSeed() ^ 0x9e3779b9)
  const baseTitle = props.ticket?.title ?? 'Past ticket'
  const baseDesc = props.ticket?.description ?? 'Past ticket description.'
  const variations = ['Previously reported — ', 'Past case: ', 'Earlier ticket: ']
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
} = useInferWithModelCheck(
  computed(() => props.instanceId),
  {
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
       // Top-K predictions drive the queue's confirmation choices. Similar
      // tickets remain an optional follow-up using the same ranked classes.
      if (props.ticket) {
        void fetchTopKAndPerClass(buildAnalysisSource(props.ticket))
      }
    },
  },
)

// Top-K + per-class similar tickets mutations
const inferTopKMutation = useInferTopK(
  computed(() => props.instanceId),
  2,
)
const perClassMutation = useNearestTicketsPerClassMutation(computed(() => props.instanceId))

/**
 * Fire-and-forget: fetch top-K predictions, then their per-class nearest
 * historical tickets. Silent on failure — supplementary signal only.
 */
async function fetchTopKAndPerClass(source: TicketAnalysisSource) {
  try {
    const topKRes = await inferTopKMutation.mutateAsync(source)
    const preds = topKRes?.predictions ?? []
    topKPredictions.value = preds
    if (preds.length === 0 || !perClassSimilarEnabled.value) return

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

// Map class label -> top-K probability, for surfacing alongside each per-class card
const probabilityByClass = computed((): Record<string, number> => {
  const out: Record<string, number> = {}
  for (const p of topKPredictions.value) {
    out[String(p.label)] = p.probability
  }
  return out
})

// Ranked choices used by the queue confirmation actions. Keep a primary
// prediction as a graceful fallback while the probability request completes.
const rankedPredictions = computed<TopKPrediction[]>(() => {
  if (topKPredictions.value.length > 0) return topKPredictions.value.slice(0, 2)

  const probabilities = prediction.value?.probabilities
  if (probabilities) {
    const ranked = Object.entries(probabilities)
      .map(([label, probability]) => ({ label, probability }))
      .sort((a, b) => b.probability - a.probability)
      .slice(0, 2)
    if (ranked.length > 0) return ranked
  }

  if (!prediction.value) return []
  return [
    {
      label: String(prediction.value.prediction),
      probability: prediction.value.confidence ?? 0,
    },
  ]
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
  },
)

const { mutate: findNearest, isPending: isFindingNearest } = useNearestTicketMutation(
  computed(() => props.instanceId),
  {
    onSuccess: (data) => {
      nearestTickets.value = data[0] ?? null
      telemetry.recordView(
        'view_nearest_ticket',
        props.ticket?.ref ?? props.ticket?.id ?? null,
        'queue_aided',
        {
          nearest_ref: firstNeighbor(data[0] ?? null)?.ref,
          historical_ref: data[0]?.historical_neighbors?.[0]?.ref,
          predicted_class_ref: data[0]?.predicted_class_neighbors?.[0]?.ref,
          historical_refs: data[0]?.historical_neighbors
            ?.slice(0, NEAREST_TICKET_TOP_K)
            .map((neighbor) => neighbor.ref),
          predicted_class_refs: data[0]?.predicted_class_neighbors
            ?.slice(0, NEAREST_TICKET_TOP_K)
            .map((neighbor) => neighbor.ref),
        },
      )
    },
  },
)

// Team options for reassignment
const teamOptions = computed(() => {
  if (!props.teams?.length) return []
  return props.teams.map((t) => ({ value: t, label: t }))
})

// Combined loading flags (real mutations + mock simulation)
const isInferringAny = computed(
  () => isInferring.value || mockInferring.value || inferTopKMutation.isPending.value,
)
const isExplainingAny = computed(() => isExplainingLime.value || mockExplaining.value)
const isFindingNearestAny = computed(() => isFindingNearest.value || mockFindingNearest.value)
const hasLimeHighlights = computed(() => (explanation.value?.[0]?.word_weights?.length ?? 0) > 0)
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

// Build an analysis source that prefers the ticket ref (so backend can look
// it up directly) but carries the text data as a fallback.
function buildAnalysisSource(ticket: QueueTicket): TicketAnalysisSource {
  const ref = ticket.ref ?? ticket.id ?? null
  const ticketData = buildInferenceData(ticket)
  return ref ? { ticketRefs: [ref], ticketData } : { ticketData }
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
      neighborTicketBodies.value = Object.fromEntries(
        [...nearest.historical_neighbors, ...nearest.predicted_class_neighbors].map((neighbor) => [
          String(neighbor.ref),
          {
            title: neighbor.title ?? undefined,
            description: neighbor.description ?? undefined,
          },
        ]),
      )
      mockFindingNearest.value = false
      const nearestRef = firstNeighbor(nearest)?.ref
      telemetry.recordView(
        'view_nearest_ticket',
        props.ticket?.ref ?? props.ticket?.id ?? null,
        'queue_aided',
        {
          nearest_ref: nearestRef,
          historical_ref: nearest.historical_neighbors?.[0]?.ref,
          predicted_class_ref: nearest.predicted_class_neighbors?.[0]?.ref,
          historical_refs: nearest.historical_neighbors
            ?.slice(0, NEAREST_TICKET_TOP_K)
            .map((neighbor) => neighbor.ref),
          predicted_class_refs: nearest.predicted_class_neighbors
            ?.slice(0, NEAREST_TICKET_TOP_K)
            .map((neighbor) => neighbor.ref),
          mock: true,
        },
      )
    }, 350)
    return
  }
  const ticketData = buildInferenceData(props.ticket)
  const ticketRef = props.ticket?.ref ?? props.ticket?.id ?? null
  const source: TicketAnalysisSource = ticketRef
    ? { ticketRefs: [ticketRef], ticketData }
    : { ticketData }
  explainLime({ query_idx: source.ticketRefs, ticket_data: source.ticketData })
  findNearest({ query_idx: source.ticketRefs, ticket_data: source.ticketData, top_k: NEAREST_TICKET_TOP_K })
}

// Handle prediction request (real or mocked depending on global mock-mode)
function handlePredict() {
  if (!props.ticket) return
  prediction.value = null
  explanation.value = null
  nearestTickets.value = null
  neighborTicketBodies.value = {}
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
  runInference(buildAnalysisSource(props.ticket))
}

const isManualReassignMode = computed(() => Boolean(selectedReassignTeam.value))

// Confirm one of the ranked model predictions as the label.
function handleConfirm(selectedPrediction = rankedPredictions.value[0], predictionRank = 1) {
  if (!selectedPrediction || isManualReassignMode.value || props.feedbackPending) return
  const team = String(selectedPrediction.label)
  const modelPrediction = String(rankedPredictions.value[0]?.label ?? team)
  labeledTeamName.value = team
  showLabeledFlash.value = true
  emit('confirm', team, {
    prediction: modelPrediction,
    secondPrediction: rankedPredictions.value[1]?.label ?? null,
    confidence: selectedPrediction.probability,
    predictionRank,
  })
}

// Reassign to different team
function handleReassign() {
  if (!selectedReassignTeam.value || props.feedbackPending) return
  const team = selectedReassignTeam.value
  labeledTeamName.value = team
  showLabeledFlash.value = true
  emit('reassign', team, {
    prediction: prediction.value ? String(prediction.value.prediction) : null,
    secondPrediction: rankedPredictions.value[1]?.label ?? null,
    confidence: prediction.value?.confidence ?? null,
  })
  selectedReassignTeam.value = ''
}

function clearReassignSelection() {
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
      neighborTicketBodies.value = {}
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
  { immediate: true },
)

const historicalNeighbors = computed<Neighbor[]>(
  () => nearestTickets.value?.historical_neighbors?.slice(0, NEAREST_TICKET_TOP_K) ?? [],
)
const predictedClassNeighbors = computed<Neighbor[]>(
  () => nearestTickets.value?.predicted_class_neighbors?.slice(0, NEAREST_TICKET_TOP_K) ?? [],
)
const neighborRefs = computed(() => [
  ...new Set(
    [...historicalNeighbors.value, ...predictedClassNeighbors.value]
      .map((neighbor) => neighbor.ref)
      .filter((ref): ref is string => Boolean(ref))
      .map(String),
  ),
])

let neighborBodyRequestId = 0

// Hydrate both nearest-ticket roles in one request. The role-specific arrays
// stay independent so a missing historical result cannot be replaced by a
// predicted-class result (or vice versa).
watch(neighborRefs, async (refs) => {
  const requestId = ++neighborBodyRequestId
  if (mockStore.mockEnabled) return

  neighborTicketBodies.value = {}
  loadingSimilarBody.value = false

  if (refs.length === 0 || props.instanceId <= 0) return

  loadingSimilarBody.value = true
  try {
    const response = await apiService.getTickets(props.instanceId, refs)
    if (requestId !== neighborBodyRequestId) return

    const bodies = new Map(
      response.tickets.map((ticket) => [
        String(ticket.Ref),
        {
          title: ticket.Title_anon,
          description: ticket.Description_anon,
        },
      ]),
    )
    neighborTicketBodies.value = Object.fromEntries(bodies)
  } catch {
    if (requestId === neighborBodyRequestId) {
      neighborTicketBodies.value = {}
    }
  } finally {
    if (requestId === neighborBodyRequestId) loadingSimilarBody.value = false
  }
})

function firstSentence(text?: string | null): string | undefined {
  const normalized = text?.trim()
  if (!normalized) return undefined
  const match = normalized.match(/^.*?[.!?](?:\s|$)/)
  return (match?.[0] ?? normalized).trim()
}

function neighborForView(
  neighbor: Neighbor,
  bodies: Record<string, { title?: string; description?: string }>,
) {
  const body = bodies[String(neighbor.ref)]
  const description = body?.description ?? neighbor.description ?? undefined
  return {
    ref: String(neighbor.ref),
    label: neighbor.label ? String(neighbor.label) : undefined,
    similarity: typeof neighbor.similarity === 'number' ? neighbor.similarity : undefined,
    title: body?.title ?? neighbor.title ?? undefined,
    description,
    bestSentence: neighbor.best_sentence?.trim() || firstSentence(description),
  }
}

const historicalTicketsForView = computed(() =>
  historicalNeighbors.value.map((neighbor) =>
    neighborForView(neighbor, neighborTicketBodies.value),
  ),
)
const predictedClassTicketsForView = computed(() =>
  predictedClassNeighbors.value.map((neighbor) =>
    neighborForView(neighbor, neighborTicketBodies.value),
  ),
)

// Expose imperative actions so parent-level keyboard shortcuts (e.g. the "c"
// confirm shortcut) can drive the panel. No-op when there's no prediction yet.
defineExpose({
  confirmPrediction: () => {
    if (rankedPredictions.value.length > 0) handleConfirm(rankedPredictions.value[0])
  },
})
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
        <h2 class="detail-panel__title">
          <LimeHighlightedText :text="ticket.title" :explanation="explanation" />
        </h2>
        <div
          v-if="hasLimeHighlights"
          class="detail-panel__lime-legend"
          aria-label="LIME highlight legend"
        >
          <span class="detail-panel__lime-legend-item">
            <span class="detail-panel__lime-swatch detail-panel__lime-swatch--positive"></span>
            supports
          </span>
          <span class="detail-panel__lime-legend-item">
            <span class="detail-panel__lime-swatch detail-panel__lime-swatch--negative"></span>
            opposes
          </span>
        </div>
      </header>

      <!-- Content -->
      <div class="detail-panel__content">
        <!-- Description (plain paragraph, no card wrapper) -->
        <p class="detail-panel__description">
          <LimeHighlightedText :text="ticket.description" :explanation="explanation" />
        </p>

        <!-- Prediction Section -->
        <section class="detail-panel__prediction">
          <Transition name="prediction-fade" mode="out-in">
            <!-- Loading -->
            <div v-if="isInferringAny" key="loading" class="detail-panel__loading">
              <Spinner label="Getting suggestion..." />
            </div>

            <!-- Prediction Result -->
            <div
              v-else-if="prediction"
              key="result"
              class="detail-panel__prediction-inner"
              data-track-region="prediction_card"
            >
              <div class="detail-panel__decision-grid">
                <section class="detail-panel__model-predictions" aria-label="Model predictions">
                  <div class="detail-panel__decision-heading">Model top predictions</div>
                  <div
                    v-for="(suggestion, index) in rankedPredictions"
                    :key="suggestion.label"
                    class="detail-panel__prediction-choice"
                  >
                    <span class="detail-panel__prediction-rank">{{ index + 1 }}</span>
                    <div class="detail-panel__prediction-choice-info">
                      <strong>{{ suggestion.label }}</strong>
                      <span>{{ (suggestion.probability * 100).toFixed(1) }}%</span>
                    </div>
                    <Button
                      variant="default"
                      size="sm"
                      data-track-region="confirm_button"
                      :disabled="isManualReassignMode || feedbackPending"
                      :title="
                        isManualReassignMode
                          ? 'Clear the manual reassignment before confirming a model prediction'
                          : `Confirm ${suggestion.label}`
                      "
                      @click="handleConfirm(suggestion, index + 1)"
                    >
                      <Check :size="14" />
                      Confirm
                    </Button>
                  </div>
                </section>

                <div class="detail-panel__decision-side">
                  <!-- Manual reassignment is separate from model confirmation. -->
                  <section class="detail-panel__reassign" data-track-region="reassign_select">
                    <span class="detail-panel__decision-heading">Manual reassignment</span>
                    <div class="detail-panel__reassign-controls">
                      <Select
                        v-model="selectedReassignTeam"
                        placeholder="Select team..."
                        :options="teamOptions"
                        size="sm"
                        :disabled="feedbackPending"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        :disabled="!selectedReassignTeam || feedbackPending"
                        @click="handleReassign"
                      >
                        Reassign
                      </Button>
                      <Button
                        v-if="selectedReassignTeam"
                        variant="ghost"
                        size="sm"
                        :disabled="feedbackPending"
                        @click="clearReassignSelection"
                      >
                        <X :size="14" />
                        Clear
                      </Button>
                    </div>
                    <p v-if="isManualReassignMode" class="detail-panel__reassign-warning">
                      Manual reassignment selected. Model confirmations are disabled.
                    </p>
                  </section>

                  <section class="detail-panel__feedback" data-track-region="labeler_feedback">
                    <span class="detail-panel__decision-heading">Tired/Difficult feedback</span>
                    <div class="detail-panel__feedback-row">
                      <Button
                        :variant="props.isTired ? 'secondary' : 'ghost'"
                        size="sm"
                        :disabled="feedbackPending"
                        :aria-pressed="props.isTired"
                        @click="$emit('feedback', 'I_AM_TIRED')"
                      >
                        <Coffee :size="14" />
                        Tired
                      </Button>
                      <Button
                        :variant="props.isDifficult ? 'secondary' : 'ghost'"
                        size="sm"
                        :disabled="feedbackPending"
                        :aria-pressed="props.isDifficult"
                        @click="$emit('feedback', 'DIFFICULT_TICKET')"
                      >
                        <AlertTriangle :size="14" />
                        Difficult
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
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-else key="empty" class="detail-panel__empty">
              <Button variant="default" size="sm" @click="handlePredict">
                Get AI Suggestion
              </Button>
            </div>
          </Transition>
        </section>

        <!-- Compare the two nearest-ticket roles returned by /nearest. -->
        <SideBySideExplanation
          v-if="showXai && prediction"
          :historical-tickets="historicalTicketsForView"
          :predicted-class-tickets="predictedClassTicketsForView"
          :loading-similar="isFindingNearestAny || loadingSimilarBody"
        />

        <!-- Similar Tickets by Predicted Class (top-K, capability-gated) -->
        <section
          v-if="perClassSimilarEnabled && (similarPerClass.length > 0 || isLoadingSimilarPerClass)"
          class="detail-panel__per-class"
          data-track-region="per_class_similar"
        >
          <h3 class="detail-panel__per-class-title">
            <Sparkles :size="16" />
            Similar Tickets by Category
          </h3>
          <p class="detail-panel__per-class-desc">
            The closest past ticket for each of the AI's top suggestions.
          </p>

          <div
            v-if="isLoadingSimilarPerClass && similarPerClass.length === 0"
            class="detail-panel__per-class-loading"
          >
            <Spinner label="Finding similar tickets by category..." />
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

  &__lime-legend {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.375rem;
    font-size: 0.6875rem;
    color: var(--muted-foreground);
  }

  &__lime-legend-item {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
  }

  &__lime-swatch {
    width: 0.625rem;
    height: 0.625rem;
    border-radius: 2px;

    &--positive {
      background: color-mix(in srgb, var(--primary) 45%, transparent);
      border-bottom: 2px solid var(--primary);
    }

    &--negative {
      background: color-mix(in srgb, var(--destructive) 45%, transparent);
      border-bottom: 2px solid var(--destructive);
    }
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

  &__decision-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 0.75rem;
    align-items: start;
  }

  &__model-predictions,
  &__decision-side {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 0;
  }

  &__decision-heading {
    color: var(--muted-foreground);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  &__prediction-choice {
    display: grid;
    grid-template-columns: 1.5rem minmax(0, 1fr) auto;
    align-items: center;
    gap: 0.5rem;
    min-height: 2.5rem;
    padding: 0.35rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--card);
  }

  &__prediction-rank {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.25rem;
    height: 1.25rem;
    border-radius: 999px;
    background: var(--muted);
    color: var(--muted-foreground);
    font-size: 0.6875rem;
    font-weight: 600;
  }

  &__prediction-choice-info {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 0.1rem;

    strong {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 0.8125rem;
    }

    span {
      color: var(--muted-foreground);
      font-size: 0.6875rem;
      font-variant-numeric: tabular-nums;
    }
  }

  &__reassign {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  &__reassign-controls {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    width: 100%;
    flex-wrap: wrap;

    .select {
      flex: 1 1 12rem;
      min-width: 10rem;
    }
  }

  &__reassign-warning {
    margin: 0;
    color: var(--warning);
    font-size: 0.75rem;
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

// Detail panel transition
.detail-fade-enter-active,
.detail-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
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
  transition:
    opacity 0.2s ease,
    transform 0.15s ease;
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
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
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
  gap: 0.4rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--border);
}

.detail-panel__feedback-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .detail-panel__decision-grid {
    grid-template-columns: 1fr;
  }
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
