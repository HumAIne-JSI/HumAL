<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import Select from '@/components/ui/Select.vue'
import Accordion from '@/components/ui/Accordion.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import LimeExplanation from '@/components/LimeExplanation.vue'
import NearestTicket from '@/components/NearestTicket.vue'
import { useInferWithModelCheck } from '@/composables/api/useInference'
import { useExplainLimeMutation, useNearestTicketMutation } from '@/composables/api/useXai'
import type { QueueTicket } from '@/stores/useTicketQueueStore'
import type { InferenceData, InferenceResponse, ExplainLimeResponse, NearestTicketResponse } from '@/types/api'
import {
  X,
  FileText,
  Target,
  Lightbulb,
  Search,
  MessageSquare,
  Check,
  ChevronRight,
  Users,
  Clock,
  Tag,
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
}>()

// Prediction state
const prediction = ref<InferenceResponse | null>(null)
const explanation = ref<ExplainLimeResponse | null>(null)
const nearestTickets = ref<NearestTicketResponse | null>(null)
const selectedReassignTeam = ref<string>('')

// Active tab for accordion
const activeSection = ref<string[]>(['prediction'])

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
  emit('confirm', String(prediction.value.prediction))
}

// Reassign to different team
function handleReassign() {
  if (!selectedReassignTeam.value) return
  emit('reassign', selectedReassignTeam.value)
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
  <div class="detail-panel" v-if="ticket">
    <!-- Header -->
    <header class="detail-panel__header">
      <div class="detail-panel__header-content">
        <div class="detail-panel__ref">
          <FileText :size="16" />
          {{ ticket.ref }}
        </div>
        <Button variant="ghost" size="icon" @click="$emit('close')">
          <X :size="18" />
        </Button>
      </div>
      <h2 class="detail-panel__title">{{ ticket.title }}</h2>
      <div class="detail-panel__meta">
        <Badge v-if="ticket.team" variant="secondary">
          <Users :size="12" />
          {{ ticket.team }}
        </Badge>
        <Badge v-if="ticket.category" variant="outline">
          <Tag :size="12" />
          {{ ticket.category }}
        </Badge>
        <span class="detail-panel__time">
          <Clock :size="12" />
          {{ formatDate(ticket.timestamp) }}
        </span>
      </div>
    </header>

    <!-- Content -->
    <div class="detail-panel__content">
      <!-- Description -->
      <Card class="detail-panel__description">
        <template #title>
          <FileText :size="16" />
          Description
        </template>
        <p class="detail-panel__description-text">{{ ticket.description }}</p>
      </Card>

      <!-- Prediction Section -->
      <Card class="detail-panel__prediction">
        <template #title>
          <Target :size="16" />
          AI Prediction
        </template>
        <template #action>
          <Button
            v-if="!prediction && !isInferring"
            variant="default"
            size="sm"
            @click="handlePredict"
          >
            Analyze
          </Button>
          <Button
            v-else-if="prediction"
            variant="ghost"
            size="sm"
            @click="handlePredict"
            :disabled="isInferring"
          >
            <RefreshCw :size="14" :class="{ 'animate-spin': isInferring }" />
            Re-analyze
          </Button>
        </template>

        <!-- Loading -->
        <div v-if="isInferring" class="detail-panel__loading">
          <Progress :value="undefined" />
          <span>Analyzing ticket...</span>
        </div>

        <!-- Prediction Result -->
        <template v-else-if="prediction">
          <PredictionResult
            :prediction="prediction.prediction"
            :confidence="prediction.confidence"
            :probabilities="prediction.probabilities"
            show-details
          />

          <!-- Actions -->
          <div class="detail-panel__actions">
            <Button
              variant="default"
              @click="handleConfirm"
            >
              <Check :size="16" />
              Confirm Prediction
            </Button>

            <div class="detail-panel__reassign">
              <Select
                v-model="selectedReassignTeam"
                placeholder="Reassign to..."
                :options="teamOptions"
              />
              <Button
                variant="outline"
                :disabled="!selectedReassignTeam"
                @click="handleReassign"
              >
                Reassign
              </Button>
            </div>
          </div>

          <!-- Next button -->
          <Button
            variant="ghost"
            class="detail-panel__next"
            @click="$emit('next')"
          >
            Next Ticket
            <ChevronRight :size="16" />
          </Button>
        </template>

        <!-- Empty state -->
        <div v-else class="detail-panel__empty">
          <Target :size="32" class="detail-panel__empty-icon" />
          <p>Click "Analyze" to get AI predictions for this ticket</p>
        </div>
      </Card>

      <!-- XAI Section (collapsible) -->
      <template v-if="showXai && prediction">
        <!-- LIME Explanation -->
        <Card class="detail-panel__xai">
          <LimeExplanation
            :explanation="explanation"
            :loading="isExplainingLime"
            collapsible
            :default-expanded="confidenceLevel === 'low'"
          />
        </Card>

        <!-- Similar Tickets -->
        <Card class="detail-panel__xai">
          <NearestTicket
            :nearest-ticket="nearestTickets"
            :loading="isFindingNearest"
            show-details
          />
        </Card>
      </template>
    </div>
  </div>

  <!-- Empty State -->
  <div v-else class="detail-panel detail-panel--empty">
    <div class="detail-panel__empty-state">
      <FileText :size="48" class="detail-panel__empty-icon" />
      <h3>No Ticket Selected</h3>
      <p>Select a ticket from the list to view details and AI predictions</p>
    </div>
  </div>
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
    padding: 1rem 1.25rem;
    background: var(--card);
    border-bottom: 1px solid var(--border);
  }

  &__header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  &__ref {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--muted-foreground);
    text-transform: uppercase;
  }

  &__title {
    margin: 0 0 0.75rem;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--foreground);
    line-height: 1.3;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  &__time {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__description {
    &-text {
      margin: 0;
      font-size: 0.9375rem;
      line-height: 1.6;
      color: var(--foreground);
      white-space: pre-wrap;
    }
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 2rem 1rem;
    text-align: center;
    color: var(--muted-foreground);
  }

  &__actions {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }

  &__reassign {
    display: flex;
    gap: 0.5rem;
  }

  &__next {
    margin-top: 0.5rem;
    justify-content: center;
  }

  &__xai {
    // Specific styling if needed
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 2rem 1rem;
    text-align: center;
    color: var(--muted-foreground);

    &-icon {
      opacity: 0.5;
      margin-bottom: 0.5rem;
    }

    p {
      margin: 0;
      font-size: 0.875rem;
    }
  }

  &__empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 2rem;
    text-align: center;
    color: var(--muted-foreground);

    h3 {
      margin: 0;
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--foreground);
    }

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
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
