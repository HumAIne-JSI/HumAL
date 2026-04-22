<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import Select from '@/components/ui/Select.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import XaiTabs from '@/components/XaiTabs.vue'
import { useInferWithModelCheck } from '@/composables/api/useInference'
import { useExplainLimeMutation, useNearestTicketMutation } from '@/composables/api/useXai'
import type { QueueTicket } from '@/stores/useTicketQueueStore'
import type { InferenceData, InferenceResponse, ExplainLimeResponse, NearestTicketResponse } from '@/types/api'
import {
  X,
  FileText,
  Check,
  CheckCircle,
  ChevronRight,
  RefreshCw,
} from 'lucide-vue-next'

export interface TicketDetailPanelProps {
  ticket: QueueTicket | null
  instanceId: number
  teams?: string[]
  showXai?: boolean
}

const props = withDefaults(defineProps<TicketDetailPanelProps>(), {
  showXai: true,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', team: string): void
  (e: 'reassign', team: string): void
  (e: 'next'): void
  (e: 'labeled'): void
}>()

// Prediction state
const prediction = ref<InferenceResponse | null>(null)
const explanation = ref<ExplainLimeResponse | null>(null)
const nearestTickets = ref<NearestTicketResponse | null>(null)
const selectedReassignTeam = ref<string>('')
const showLabeledFlash = ref(false)
const labeledTeamName = ref('')

// Inference mutation
const {
  mutate: runInference,
  isPending: isInferring,
  reset: resetInference,
} = useInferWithModelCheck(computed(() => props.instanceId), {
  onSuccess: (data) => {
    prediction.value = data
    // Auto-trigger XAI after prediction
    if (props.showXai && props.ticket) {
      runXaiAnalysis()
    }
  },
})

// XAI mutations
const { mutate: explainLime, isPending: isExplainingLime } = useExplainLimeMutation(
  computed(() => props.instanceId),
  {
    onSuccess: (data) => {
      explanation.value = data
    },
  }
)

const { mutate: findNearest, isPending: isFindingNearest } = useNearestTicketMutation(
  computed(() => props.instanceId),
  {
    onSuccess: (data) => {
      nearestTickets.value = data
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

// Is loading any XAI
const isLoadingXai = computed(() => isExplainingLime.value || isFindingNearest.value)

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

// Run XAI analysis
function runXaiAnalysis() {
  if (!props.ticket) return
  const ticketData = buildInferenceData(props.ticket)
  explainLime({ ticket_data: ticketData })
  findNearest({ ticket_data: ticketData })
}

// Handle prediction request
function handlePredict() {
  if (!props.ticket) return
  prediction.value = null
  explanation.value = null
  nearestTickets.value = null
  runInference(buildInferenceData(props.ticket))
}

// Confirm prediction as label
function handleConfirm() {
  if (!prediction.value) return
  const team = String(prediction.value.prediction)
  labeledTeamName.value = team
  showLabeledFlash.value = true
  emit('confirm', team)
}

// Reassign to different team
function handleReassign() {
  if (!selectedReassignTeam.value) return
  const team = selectedReassignTeam.value
  labeledTeamName.value = team
  showLabeledFlash.value = true
  emit('reassign', team)
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
      selectedReassignTeam.value = ''
      showLabeledFlash.value = false
      labeledTeamName.value = ''
      resetInference()

      // Auto-predict for unlabeled tickets
      if (props.ticket?.status === 'unlabeled' && props.instanceId > 0) {
        handlePredict()
      }
    }
  },
  { immediate: true }
)
</script>

<template>
  <Transition name="detail-fade" mode="out-in">
  <div class="detail-panel" v-if="ticket" :key="ticket.id">
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
        <div v-if="isInferring" key="loading" class="detail-panel__loading">
          <Progress :value="undefined" />
          <span>Analyzing ticket...</span>
        </div>

        <!-- Prediction Result -->
        <div v-else-if="prediction" key="result" class="detail-panel__prediction-inner">
          <PredictionResult
            :prediction="prediction.prediction"
            :confidence="prediction.confidence"
            :probabilities="prediction.probabilities"
            show-details
            compact
          >
            <template #actions>
              <Button variant="outline" size="sm" @click="handleConfirm">
                <Check :size="14" />
                Confirm
              </Button>
            </template>
          </PredictionResult>

          <!-- Actions row: Reassign + Re-analyze -->
          <div class="detail-panel__actions">
            <div class="detail-panel__reassign">
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
              :disabled="isInferring"
              title="Re-analyze"
            >
              <RefreshCw :size="14" :class="{ 'animate-spin': isInferring }" />
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

      <!-- XAI Tabs -->
      <XaiTabs
        v-if="showXai && prediction"
        :explanation="explanation"
        :nearest-tickets="nearestTickets"
        :loading-lime="isExplainingLime"
        :loading-nearest="isFindingNearest"
      />
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
</style>
