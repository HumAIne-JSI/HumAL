<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Progress from '@/components/ui/Progress.vue'
import Spinner from '@/components/ui/Spinner.vue'
import ExportButton from '@/components/ExportButton.vue'
import InstanceSelector from '@/components/InstanceSelector.vue'
import { useInstances } from '@/composables/api/useActiveLearning'
import { useCategories, useSubcategories } from '@/composables/api/useData'
import { useInfer } from '@/composables/api/useInference'
import {
  useAssistedResolution,
  useResolutionFeedback,
  useFeedbackStats,
  useSaveResolvedTicket,
  DEFAULT_RESOLUTION_TOP_K,
  type AssistedResolution,
} from '@/composables/api/useResolution'
import { useAuthStore } from '@/stores/useAuthStore'
import { useLabeledTicketsStore, type LabeledTicket } from '@/stores/useLabeledTicketsStore'
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry'
import type { ResolutionSimilarReply, ResolutionFeedbackStatsResponse } from '@/types/api'
import {
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  RefreshCw,
  FileText,
  Sparkles,
  Users,
  Target,
  Save,
  Gavel,
  Brain,
  Inbox,
  Trash2,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const telemetry = useBenchmarkTelemetry()
const labeledStore = useLabeledTicketsStore()
const labeledTickets = computed(() => labeledStore.tickets)

// Labeled-list UI state: collapse + filtering.
const labeledCollapsed = ref(false)
const labeledSearch = ref('')
const labeledTeamFilter = ref('')
const labeledTeams = computed(() => {
  const set = new Set<string>()
  for (const ticket of labeledTickets.value) {
    if (ticket.label) set.add(ticket.label)
  }
  return Array.from(set).sort()
})
const filteredLabeledTickets = computed(() => {
  const query = labeledSearch.value.trim().toLowerCase()
  const team = labeledTeamFilter.value
  return labeledTickets.value.filter((ticket) => {
    if (team && ticket.label !== team) return false
    if (!query) return true
    return (
      ticket.ref.toLowerCase().includes(query) ||
      ticket.title.toLowerCase().includes(query) ||
      ticket.description.toLowerCase().includes(query) ||
      ticket.label.toLowerCase().includes(query)
    )
  })
})

// Form state
const ticketTitle = ref('')
const ticketDescription = ref('')
const topK = ref(DEFAULT_RESOLUTION_TOP_K)
const selectedCategory = ref('')
const selectedSubcategory = ref('')

// A labeled ticket pulled from the queue: its human label is reused as the
// predicted-team hint, taking priority over model inference.
const presetTeam = ref('')
const selectedLabeledRef = ref('')

// Optional Active-Learning bridge: a trained instance used to predict the team
// before resolving, sharpening retrieval + judging.
const selectedInstanceId = ref(0)
const instanceModel = computed<string>({
  get: () => (selectedInstanceId.value > 0 ? String(selectedInstanceId.value) : ''),
  set: (value) => {
    selectedInstanceId.value = value ? Number(value) : 0
  },
})

// Result state
const result = ref<AssistedResolution | null>(null)
const editedResponse = ref('')
const savedToKb = ref(false)
const copiedToClipboard = ref(false)
// Per-reply feedback: retrieved_id -> submitted vote / aggregated stats.
const votes = ref<Record<string, 0 | 1>>({})
const stats = ref<Record<string, ResolutionFeedbackStatsResponse>>({})
const votingId = ref<string | null>(null)
// A stable id grouping all feedback from one generated resolution.
const queryId = ref('')

// Manual-effort telemetry: how much / how long the operator edits the suggested
// reply before using it, so Analytics can estimate operator effort saved.
const generatedAtMs = ref<number | null>(null)
const firstEditMs = ref<number | null>(null)
const effortRecorded = ref(false)

// Detect the first manual edit of the generated reply.
watch(editedResponse, (value) => {
  if (result.value && firstEditMs.value == null && value !== result.value.response) {
    firstEditMs.value = Date.now()
  }
})

// Reference data for the optional service-category fields.
const { data: instancesData } = useInstances()
const firstInstanceId = computed(() => {
  const instances = instancesData.value?.instances
  const keys = instances ? Object.keys(instances) : []
  return keys.length ? Number(keys[0]) : 0
})
const catInstanceId = computed(() =>
  selectedInstanceId.value > 0 ? selectedInstanceId.value : firstInstanceId.value,
)
const { data: categoriesData } = useCategories(catInstanceId, undefined, {
  enabled: computed(() => catInstanceId.value > 0),
})
const { data: subcategoriesData } = useSubcategories(catInstanceId, undefined, undefined, {
  enabled: computed(() => catInstanceId.value > 0),
})
const categories = computed(() => categoriesData.value?.categories ?? [])
const subcategories = computed(() => subcategoriesData.value?.subcategories ?? [])

// Mutations
const assisted = useAssistedResolution({ meta: { silent: true } })
const inferMutation = useInfer(selectedInstanceId, { meta: { silent: true } })
const feedbackMutation = useResolutionFeedback({ meta: { silent: true } })
const statsMutation = useFeedbackStats()
const saveMutation = useSaveResolvedTicket({ meta: { silent: true } })

// Computed
const hasInput = computed(() => !!(ticketTitle.value.trim() || ticketDescription.value.trim()))
const isResolving = computed(() => assisted.isPending.value || inferMutation.isPending.value)
const isSaving = computed(() => saveMutation.isPending.value)
const confidencePct = computed(() => (result.value ? (result.value.team_confidence ?? 0) * 100 : 0))

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
      similar_count: result.value.similar_replies.length,
    },
  ]
})

// Helpers
const matchPct = (reply: ResolutionSimilarReply): number =>
  Math.round((reply.enhanced_score ?? 0) * 100)

const isVoting = (id: string): boolean => votingId.value === id

function statsFor(id: string): { up: number; down: number } | null {
  const entry = stats.value[id]
  if (!entry) return null
  let up = 0
  let down = 0
  for (const [, upvotes, downvotes] of entry.agg) {
    up += upvotes
    down += downvotes
  }
  return { up, down }
}

async function loadStats(replies: ResolutionSimilarReply[]): Promise<void> {
  await Promise.all(
    replies.map(async (reply) => {
      try {
        stats.value[reply.retrieved_id] = await statsMutation.mutateAsync({
          retrievedId: reply.retrieved_id,
        })
      } catch {
        // Feedback stats are non-critical decoration.
      }
    }),
  )
}

// Methods
async function generate(): Promise<void> {
  if (!hasInput.value) {
    toast.error('Empty ticket', { description: 'Please enter a title or description' })
    return
  }

  // Prefer the human label from the queue; otherwise best-effort AL inference to
  // predict the team/class and sharpen retrieval + judging.
  let predictedTeam: string | undefined = presetTeam.value || undefined
  if (!predictedTeam && selectedInstanceId.value > 0) {
    try {
      const inference = await inferMutation.mutateAsync({
        title_anon: ticketTitle.value,
        description_anon: ticketDescription.value,
      })
      predictedTeam = inference.prediction != null ? String(inference.prediction) : undefined
    } catch {
      // Inference is optional; the resolution API classifies on its own.
    }
  }

  try {
    const data = await assisted.mutateAsync({
      title: ticketTitle.value,
      description: ticketDescription.value,
      top_k: topK.value,
      predicted_team: predictedTeam,
    })
    result.value = data
    editedResponse.value = data.response
    savedToKb.value = false
    votes.value = {}
    stats.value = {}
    queryId.value = crypto.randomUUID()
    generatedAtMs.value = Date.now()
    firstEditMs.value = null
    effortRecorded.value = false
    toast.success('Resolution generated', {
      description: `${data.classification} · ${data.predicted_team}`,
    })
    telemetry.recordLab('run_prediction', 'Ticket', {
      page: 'resolution',
      classification: data.classification,
      predicted_team: data.predicted_team,
    })
    await loadStats(data.similar_replies)
  } catch (error) {
    toast.error('Resolution failed', {
      description: error instanceof Error ? error.message : 'Unable to reach the resolution service',
    })
  }
}

async function vote(reply: ResolutionSimilarReply, label: 0 | 1): Promise<void> {
  if (!result.value || votingId.value) return
  votingId.value = reply.retrieved_id
  try {
    await feedbackMutation.mutateAsync({
      query_id: queryId.value || crypto.randomUUID(),
      retrieved_id: reply.retrieved_id,
      label,
      predicted_class: result.value.predicted_class,
      predicted_team: result.value.predicted_team,
      user_id: authStore.user?.user_id,
    })
    votes.value[reply.retrieved_id] = label
    stats.value[reply.retrieved_id] = await statsMutation.mutateAsync({
      retrievedId: reply.retrieved_id,
    })
    toast.success(label === 1 ? 'Marked as helpful' : 'Marked as not helpful')
  } catch (error) {
    toast.error('Could not save feedback', {
      description: error instanceof Error ? error.message : undefined,
    })
  } finally {
    votingId.value = null
  }
}

function useReply(reply: ResolutionSimilarReply): void {
  if (reply.first_reply) {
    editedResponse.value = reply.first_reply
    toast.info('Reply applied', { description: 'You can edit it before saving' })
  }
}

// Load a labeled ticket from the queue into the form.
function useLabeledTicket(ticket: LabeledTicket): void {
  ticketTitle.value = ticket.title
  ticketDescription.value = ticket.description
  selectedCategory.value = ticket.category ?? ''
  selectedSubcategory.value = ticket.subcategory ?? ''
  presetTeam.value = ticket.label
  selectedLabeledRef.value = ticket.ref
  result.value = null
  editedResponse.value = ''
  savedToKb.value = false
  votes.value = {}
  stats.value = {}
  generatedAtMs.value = null
  firstEditMs.value = null
  effortRecorded.value = false
  toast.info('Ticket loaded', { description: `${ticket.ref} · ${ticket.label}` })
}

// Detach the queue association but keep the typed text for manual resolving.
function clearLoadedTicket(): void {
  presetTeam.value = ''
  selectedLabeledRef.value = ''
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString()
}

// Character-level edit distance (bounded) between the generated reply and the
// operator's final text — the basis of the "effort saved" estimate.
function editDistance(a: string, b: string): number {
  if (a === b) return 0
  if (a.length > 4000 || b.length > 4000) return Math.abs(a.length - b.length)
  const m = a.length
  const n = b.length
  if (m === 0) return n
  if (n === 0) return m
  const prev = Array.from({ length: n + 1 }, (_, i) => i)
  const curr = new Array<number>(n + 1)
  for (let i = 1; i <= m; i++) {
    curr[0] = i
    for (let j = 1; j <= n; j++) {
      const cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1
      curr[j] = Math.min(prev[j]! + 1, curr[j - 1]! + 1, prev[j - 1]! + cost)
    }
    for (let j = 0; j <= n; j++) prev[j] = curr[j]!
  }
  return prev[n]!
}

// Emit a one-time manual-effort telemetry event when the operator accepts a
// suggested resolution (copies or saves it): how much they changed it and how
// long they reviewed it before using it.
function recordEffort(outcome: 'saved' | 'copied'): void {
  if (!result.value || effortRecorded.value) return
  effortRecorded.value = true
  const generated = result.value.response ?? ''
  const final = editedResponse.value ?? ''
  const changed = editDistance(generated, final)
  const editRatio = Math.min(1, changed / Math.max(generated.length, final.length, 1))
  const now = Date.now()
  const reviewMs = generatedAtMs.value != null ? now - generatedAtMs.value : 0
  const editMs = firstEditMs.value != null ? now - firstEditMs.value : 0
  telemetry.recordLab(
    'validate_resolution',
    'Ticket',
    {
      page: 'resolution',
      outcome,
      edited: final !== generated,
      edit_ratio: Number(editRatio.toFixed(3)),
      chars_generated: generated.length,
      chars_final: final.length,
      chars_changed: changed,
      edit_duration_ms: editMs,
      predicted_team: result.value.predicted_team,
      classification: result.value.classification,
    },
    { latency_ms: reviewMs },
  )
}

async function saveToKb(): Promise<void> {
  if (!result.value) return
  try {
    await saveMutation.mutateAsync({
      title: ticketTitle.value,
      description: ticketDescription.value,
      response: editedResponse.value,
      predicted_team: result.value.predicted_team,
      predicted_classification: result.value.classification,
      service_name: selectedCategory.value || undefined,
      service_subcategory: selectedSubcategory.value || undefined,
    })
    savedToKb.value = true
    toast.success('Saved to knowledge base')
    recordEffort('saved')
  } catch (error) {
    toast.error('Could not save to knowledge base', {
      description: error instanceof Error ? error.message : undefined,
    })
  }
}

async function copyResponse(): Promise<void> {
  try {
    await navigator.clipboard.writeText(editedResponse.value)
    copiedToClipboard.value = true
    setTimeout(() => (copiedToClipboard.value = false), 2000)
    toast.success('Copied to clipboard')
    recordEffort('copied')
  } catch {
    toast.error('Failed to copy')
  }
}

function clearForm(): void {
  ticketTitle.value = ''
  ticketDescription.value = ''
  selectedCategory.value = ''
  selectedSubcategory.value = ''
  topK.value = DEFAULT_RESOLUTION_TOP_K
  presetTeam.value = ''
  selectedLabeledRef.value = ''
  result.value = null
  editedResponse.value = ''
  savedToKb.value = false
  votes.value = {}
  stats.value = {}
  generatedAtMs.value = null
  firstEditMs.value = null
  effortRecorded.value = false
}

onMounted(() => {
  telemetry.recordLab('open_page', 'Ticket', { page: 'resolution' })
})
</script>

<template>
  <div class="resolution">
    <header class="resolution__header">
      <div class="resolution__header-content">
        <h1 class="resolution__title">Ticket Evolution</h1>
        <p class="resolution__subtitle">
          After a ticket is routed to a team, Tier 2 Support gets a suggested first reply based on similar past tickets.
        </p>
      </div>
    </header>

    <div class="resolution__content">
      <!-- Labeled tickets from the queue -->
      <Card class="resolution__labeled">
        <template #title>
          <Inbox :size="18" />
          Labeled tickets from the queue
          <Badge v-if="labeledTickets.length" variant="secondary">{{ labeledTickets.length }}</Badge>
        </template>
        <template #description>Pick a ticket you labeled in the queue to resolve it</template>
        <template #action>
          <div class="labeled-actions">
            <Button
              variant="ghost"
              size="sm"
              :title="labeledCollapsed ? 'Expand' : 'Collapse'"
              @click="labeledCollapsed = !labeledCollapsed"
            >
              <ChevronDown v-if="labeledCollapsed" :size="16" />
              <ChevronUp v-else :size="16" />
            </Button>
            <Button variant="ghost" size="sm" title="Refresh list" @click="labeledStore.reload()">
              <RefreshCw :size="14" />
            </Button>
            <Button
              v-if="labeledTickets.length"
              variant="ghost"
              size="sm"
              title="Clear list"
              @click="labeledStore.clear()"
            >
              <Trash2 :size="14" />
            </Button>
          </div>
        </template>

        <div v-show="!labeledCollapsed" class="labeled-body">
          <p v-if="!labeledTickets.length" class="labeled-empty">
            No labeled tickets yet. Label tickets in the Ticket Queue and they will appear here.
          </p>

          <template v-else>
            <div class="labeled-filters">
              <Input
                v-model="labeledSearch"
                placeholder="Search ref, title, description..."
                class="labeled-filters__search"
              />
              <select v-model="labeledTeamFilter" class="form-select labeled-filters__team">
                <option value="">All teams</option>
                <option v-for="team in labeledTeams" :key="team" :value="team">{{ team }}</option>
              </select>
            </div>

            <p v-if="!filteredLabeledTickets.length" class="labeled-empty">
              No tickets match your filter.
            </p>

            <div v-else class="labeled-list">
              <div
                v-for="ticket in filteredLabeledTickets"
                :key="ticket.ref"
                class="labeled-item"
                :class="{ 'labeled-item--active': selectedLabeledRef === ticket.ref }"
              >
                <div class="labeled-item__main" @click="useLabeledTicket(ticket)">
                  <div class="labeled-item__header">
                    <Badge variant="outline">{{ ticket.ref }}</Badge>
                    <Badge variant="secondary">
                      <Users :size="12" />
                      {{ ticket.label }}
                    </Badge>
                    <Badge v-if="ticket.mock" variant="outline">demo</Badge>
                    <span class="labeled-item__time">{{ formatTime(ticket.timestamp) }}</span>
                  </div>
                  <h4 class="labeled-item__title">{{ ticket.title }}</h4>
                  <p v-if="ticket.description" class="labeled-item__desc">{{ ticket.description }}</p>
                </div>
                <div class="labeled-item__actions">
                  <Button variant="outline" size="sm" @click="useLabeledTicket(ticket)">
                    <Sparkles :size="14" />
                    Use
                  </Button>
                  <Button variant="ghost" size="sm" title="Remove" @click="labeledStore.remove(ticket.ref)">
                    <X :size="14" />
                  </Button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </Card>

      <!-- Input Form -->
      <Card class="resolution__form">
        <template #title>
          <FileText :size="18" />
          Ticket Details
        </template>
        <template #description>Enter the ticket and generate an assisted resolution</template>

        <div v-if="selectedLabeledRef" class="labeled-banner">
          <span>
            Using queue ticket <strong>{{ selectedLabeledRef }}</strong> · team
            <strong>{{ presetTeam }}</strong>
          </span>
          <Button variant="ghost" size="sm" @click="clearLoadedTicket">
            <X :size="14" />
            Detach
          </Button>
        </div>

        <div class="form-grid">
          <div class="form-field form-field--full">
            <label class="form-label">Title</label>
            <Input v-model="ticketTitle" placeholder="Enter ticket title..." :disabled="isResolving" />
          </div>

          <div class="form-field form-field--full">
            <label class="form-label">Description</label>
            <Textarea
              v-model="ticketDescription"
              placeholder="Enter ticket description..."
              :rows="4"
              :disabled="isResolving"
            />
          </div>

          <div class="form-field">
            <label class="form-label">
              <Brain :size="13" />
              AI model (optional)
            </label>
            <InstanceSelector
              v-model="instanceModel"
              placeholder="No team prediction"
              :disabled="isResolving"
              size="sm"
            />
            <span class="form-hint">Suggests the team with a trained AI before resolving.</span>
          </div>

          <div class="form-field">
            <label class="form-label">Suggestions to retrieve</label>
            <Input v-model.number="topK" type="number" min="1" max="20" :disabled="isResolving" />
          </div>

          <div class="form-field">
            <label class="form-label">Service category (optional)</label>
            <select v-model="selectedCategory" class="form-select" :disabled="isResolving">
              <option value="">Select category...</option>
              <option v-for="(cat, index) in categories" :key="index" :value="cat">{{ cat }}</option>
            </select>
          </div>

          <div class="form-field">
            <label class="form-label">Service subcategory (optional)</label>
            <select
              v-model="selectedSubcategory"
              class="form-select"
              :disabled="isResolving || !selectedCategory"
            >
              <option value="">Select subcategory...</option>
              <option v-for="(sub, index) in subcategories" :key="index" :value="sub">{{ sub }}</option>
            </select>
          </div>
        </div>

        <template #footer>
          <div class="form-actions">
            <Button variant="ghost" size="sm" @click="clearForm" :disabled="isResolving">Clear</Button>
            <Button @click="generate" :loading="isResolving" :disabled="!hasInput">
              <Sparkles :size="16" />
              Generate solution
            </Button>
          </div>
        </template>
      </Card>

      <!-- Results Section -->
      <template v-if="result || isResolving">
        <!-- Classification & Team -->
        <Card class="resolution__classification">
          <template #title>
            <Target :size="18" />
            Category
          </template>

          <div v-if="isResolving" class="loading-state">
            <Spinner label="Reading the ticket and writing a suggested reply..." />
          </div>

          <template v-else-if="result">
            <div class="classification-grid">
              <div class="classification-item">
                <span class="classification-label">Category</span>
                <Badge variant="default" size="lg">{{ result.classification }}</Badge>
              </div>
              <div class="classification-item">
                <span class="classification-label">Suggested Team</span>
                <Badge variant="secondary" size="lg">
                  <Users :size="14" />
                  {{ result.predicted_team }}
                </Badge>
              </div>
              <div class="classification-item">
                <span class="classification-label">Certainty</span>
                <div class="confidence-display">
                  <Progress :value="confidencePct" :max="100" />
                  <span>{{ confidencePct.toFixed(1) }}%</span>
                </div>
              </div>
              <div class="classification-item">
                <span class="classification-label">Quality check</span>
                <Badge :variant="result.votes_applied > 0 ? 'default' : 'outline'">
                  <Gavel :size="14" />
                  {{ result.votes_applied > 0 ? `${result.votes_applied} feedback vote(s) applied` : 'No prior feedback' }}
                </Badge>
              </div>
            </div>
          </template>
        </Card>

        <!-- Generated Response -->
        <Card class="resolution__response">
          <template #title>
            <MessageSquare :size="18" />
            Suggested Response
          </template>
          <template #action>
            <div class="response-actions">
              <ExportButton :data="exportData" filename="resolution_result" :disabled="!result" />
            </div>
          </template>

          <div v-if="isResolving" class="loading-state">
            <Spinner label="Generating response..." />
          </div>

          <template v-else-if="result">
            <Textarea
              v-model="editedResponse"
              :rows="6"
              placeholder="Edit the response here..."
              class="response-textarea"
            />

            <div class="response-toolbar">
              <Button variant="outline" size="sm" @click="copyResponse">
                <Check v-if="copiedToClipboard" :size="14" />
                <Copy v-else :size="14" />
                {{ copiedToClipboard ? 'Copied!' : 'Copy' }}
              </Button>
              <Button variant="outline" size="sm" :loading="isResolving" :disabled="!hasInput" @click="generate">
                <RefreshCw :size="14" />
                Regen
              </Button>
              <div class="response-toolbar__spacer" />
              <Button
                variant="default"
                size="sm"
                @click="saveToKb"
                :loading="isSaving"
                :disabled="savedToKb || !editedResponse"
              >
                {{ savedToKb ? 'Sent' : 'Send to  Team' }}
              </Button>
            </div>
          </template>
        </Card>

        <!-- Similar Replies -->
        <Card v-if="result && result.similar_replies.length > 0" class="resolution__similar">
          <template #title>
            <FileText :size="18" />
            Similar Past Replies ({{ result.similar_replies.length }})
          </template>
          <template #description>Rate a reply (👍 / 👎) or reuse it as your response</template>

          <div class="similar-replies">
            <div
              v-for="reply in result.similar_replies"
              :key="reply.retrieved_id"
              class="similar-reply"
            >
              <div class="similar-reply__header">
                <Badge variant="outline">{{ reply.retrieved_id }}</Badge>
                <Badge variant="secondary">{{ matchPct(reply) }}% match</Badge>
                <span v-if="statsFor(reply.retrieved_id)" class="similar-reply__stats">
                  <ThumbsUp :size="12" /> {{ statsFor(reply.retrieved_id)!.up }}
                  <ThumbsDown :size="12" /> {{ statsFor(reply.retrieved_id)!.down }}
                </span>
              </div>

              <h4 class="similar-reply__title">{{ reply.Title_anon || 'No title' }}</h4>

              <p v-if="reply.Description_anon" class="similar-reply__description">
                {{ reply.Description_anon }}
              </p>

              <div v-if="reply.first_reply" class="similar-reply__response">
                <span class="similar-reply__response-label">Past Reply:</span>
                <p>{{ reply.first_reply }}</p>
              </div>

              <div class="similar-reply__actions">
                <Button variant="ghost" size="sm" @click="useReply(reply)">
                  <Copy :size="14" />
                  Use this reply
                </Button>
                <div class="similar-reply__vote">
                  <Button
                    :variant="votes[reply.retrieved_id] === 1 ? 'default' : 'outline'"
                    size="sm"
                    :loading="isVoting(reply.retrieved_id)"
                    aria-label="Mark as helpful"
                    @click="vote(reply, 1)"
                  >
                    <ThumbsUp :size="14" />
                  </Button>
                  <Button
                    :variant="votes[reply.retrieved_id] === 0 ? 'default' : 'outline'"
                    size="sm"
                    :loading="isVoting(reply.retrieved_id)"
                    aria-label="Mark as not helpful"
                    @click="vote(reply, 0)"
                  >
                    <ThumbsDown :size="14" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
.resolution {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;

  &__header {
    margin-bottom: 2rem;
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

  &__content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  &__form,
  &__labeled,
  &__classification,
  &__response,
  &__similar {
    :deep(.card__title) {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
  }
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;

  &--full {
    grid-column: 1 / -1;
  }
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.form-hint {
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

.form-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--background);
  font-size: 0.875rem;
  color: inherit;

  &:focus {
    outline: none;
    border-color: var(--ring);
    box-shadow: 0 0 0 2px var(--ring);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.classification-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.classification-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.classification-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted-foreground);
}

.confidence-display {
  display: flex;
  align-items: center;
  gap: 0.75rem;

  span {
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
  }
}

.response-actions {
  display: flex;
  gap: 0.5rem;
}

.response-textarea {
  margin-top: 1rem;
}

.response-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;

  &__spacer {
    flex: 1;
  }
}

.similar-replies {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.similar-reply {
  padding: 1rem;
  background: var(--muted);
  border-radius: var(--radius);
  transition: background 0.15s ease;

  &:hover {
    background: var(--accent);
  }

  &__header {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  &__title {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 500;
  }

  &__description {
    margin: 0.5rem 0 0;
    font-size: 0.875rem;
    color: var(--muted-foreground);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__response {
    margin-top: 0.75rem;
    padding: 0.75rem;
    background: var(--background);
    border-radius: calc(var(--radius) - 2px);
    font-size: 0.875rem;

    p {
      margin: 0.25rem 0 0;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }

  &__response-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &__use-btn {
    margin-top: 0.75rem;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  &__stats {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    margin-left: auto;
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }

  &__vote {
    display: flex;
    gap: 0.375rem;
  }
}

.labeled-actions {
  display: flex;
  gap: 0.25rem;
}

.labeled-empty {
  margin: 0.5rem 0 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.labeled-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
  max-height: 20rem;
  overflow-y: auto;
}

.labeled-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--muted);
  border: 1px solid transparent;
  border-radius: var(--radius);
  transition: background 0.15s ease, border-color 0.15s ease;

  &:hover {
    background: var(--accent);
  }

  &--active {
    border-color: var(--ring);
  }

  &__main {
    flex: 1;
    min-width: 0;
    cursor: pointer;
  }

  &__header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.375rem;
  }

  &__time {
    margin-left: auto;
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__title {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 500;
  }

  &__desc {
    margin: 0.25rem 0 0;
    font-size: 0.875rem;
    color: var(--muted-foreground);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex-shrink: 0;
  }
}

.labeled-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  background: var(--muted);
  border-radius: var(--radius);
}

.labeled-filters {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;

  &__search {
    flex: 1;
  }

  &__team {
    width: auto;
    min-width: 11rem;
  }
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .classification-grid {
    grid-template-columns: 1fr;
  }

  .labeled-filters {
    flex-direction: column;
  }
}
</style>