<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import InstanceSelector from '@/components/InstanceSelector.vue'
import TicketForm from '@/components/TicketForm.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import LimeExplanation from '@/components/LimeExplanation.vue'
import NearestTicket from '@/components/NearestTicket.vue'
import ExportButton from '@/components/ExportButton.vue'
import { useInstanceInfo } from '@/composables/api/useActiveLearning'
import { useInferWithModelCheck } from '@/composables/api/useInference'
import { useExplainLimeMutation, useNearestTicketMutation } from '@/composables/api/useXai'
import { useTickets } from '@/composables/api/useData'
import { usePredictionHistory } from '@/composables/usePredictionHistory'
import type { InferenceData, InferenceResponse, ExplainLimeResponse, NearestTicketResponse, Ticket } from '@/types/api'
import {
  Zap,
  Brain,
  Clock,
  TrendingUp,
  Cpu,
  Trash2,
  AlertCircle,
  Sparkles,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

// URL-synced instance ID
const selectedInstanceId = ref<number>(0)

// Initialize from route query
onMounted(() => {
  const instanceParam = route.query.instance
  if (instanceParam) {
    selectedInstanceId.value = Number(instanceParam)
  }
})

// Sync URL with instance selection
watch(selectedInstanceId, (newId) => {
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

// Inference mutation
const inferMutation = useInferWithModelCheck(selectedInstanceId, {
  onModelNotTrained: () => {
    toast.error('Model not trained', {
      description: 'Please train the model before running inference',
    })
  },
})

// XAI mutations
const limeMutation = useExplainLimeMutation(selectedInstanceId)
const nearestMutation = useNearestTicketMutation(selectedInstanceId)

// Prediction history composable
const { items: predictionHistory, add: addPrediction, clear: clearHistory, todayCount, avgProcessingTime } = usePredictionHistory()

// Ticket input form
const ticket = ref<InferenceData>({
  title_anon: '',
  description_anon: '',
  service_name: '',
  service_subcategory_name: '',
})

// Results
const currentPrediction = ref<InferenceResponse | null>(null)
const explanation = ref<ExplainLimeResponse | null>(null)
const nearestResult = ref<NearestTicketResponse | null>(null)
const nearestTicketDetails = ref<Ticket | null>(null)

// Processing states
const isProcessing = ref(false)
const isLoadingXai = ref(false)

// Prediction ID for preventing stale XAI updates
let currentPredictionId = 0

// Computed
const hasInstance = computed(() => selectedInstanceId.value > 0)
// Consider trained if has test_accuracy, training_accuracy, or f1_scores (matching old frontend logic)
const isTrained = computed(() => {
  if (!instanceInfo.value) return false
  return (
    instanceInfo.value.test_accuracy !== undefined ||
    instanceInfo.value.training_accuracy !== undefined ||
    (instanceInfo.value.f1_scores && instanceInfo.value.f1_scores.length > 0)
  )
})
const canRunInference = computed(() => hasInstance.value && isTrained.value)
const hasInput = computed(() => !!(ticket.value.title_anon?.trim() || ticket.value.description_anon?.trim()))

// Model accuracy for display (matches old frontend logic with f1_scores fallback)
const modelAccuracy = computed(() => {
  if (!instanceInfo.value) return 0
  // Prefer test_accuracy, then training_accuracy, then last f1_score
  if (instanceInfo.value.test_accuracy !== undefined) {
    return instanceInfo.value.test_accuracy * 100
  }
  if (instanceInfo.value.training_accuracy !== undefined) {
    return instanceInfo.value.training_accuracy * 100
  }
  if (instanceInfo.value.f1_scores && instanceInfo.value.f1_scores.length > 0) {
    return instanceInfo.value.f1_scores[instanceInfo.value.f1_scores.length - 1] * 100
  }
  return 0
})

// Tickets query for fetching nearest ticket details
const nearestTicketRef = computed(() => {
  if (!nearestResult.value) return []
  const ref = Array.isArray(nearestResult.value.nearest_ticket_ref)
    ? nearestResult.value.nearest_ticket_ref[0]
    : nearestResult.value.nearest_ticket_ref
  return ref ? [String(ref)] : []
})

const { data: nearestTicketsData } = useTickets(
  selectedInstanceId,
  nearestTicketRef,
  undefined, // trainDataPath
  { enabled: computed(() => nearestTicketRef.value.length > 0) }
)

// Update nearest ticket details when data arrives
watch(nearestTicketsData, (data) => {
  if (data?.tickets && data.tickets.length > 0) {
    nearestTicketDetails.value = data.tickets[0] ?? null
  } else {
    nearestTicketDetails.value = null
  }
})

// Export data
const exportData = computed(() => {
  return predictionHistory.value.map((item) => ({
    timestamp: item.timestamp.toISOString(),
    title: item.input.title_anon ?? '',
    description: item.input.description_anon ?? '',
    service: item.input.service_name ?? '',
    subcategory: item.input.service_subcategory_name ?? '',
    prediction: item.output.prediction,
    confidence: item.output.confidence,
    processing_time_ms: item.processingTime,
  }))
})

// Methods
const handleInstanceSelect = (value: string) => {
  selectedInstanceId.value = Number(value) || 0
  // Clear results on instance change
  currentPrediction.value = null
  explanation.value = null
  nearestResult.value = null
  nearestTicketDetails.value = null
}

const clearInput = () => {
  ticket.value = {
    title_anon: '',
    description_anon: '',
    service_name: '',
    service_subcategory_name: '',
  }
  currentPrediction.value = null
  explanation.value = null
  nearestResult.value = null
  nearestTicketDetails.value = null
}

const runPrediction = async () => {
  if (!hasInput.value) {
    toast.error('Empty ticket', { description: 'Please enter title or description' })
    return
  }

  // Increment prediction ID to invalidate pending XAI requests
  currentPredictionId++
  const thisPredictionId = currentPredictionId

  isProcessing.value = true
  currentPrediction.value = null
  explanation.value = null
  nearestResult.value = null
  nearestTicketDetails.value = null

  const startTime = Date.now()

  try {
    // Run inference
    const inferRes = await inferMutation.mutateAsync(ticket.value)
    currentPrediction.value = inferRes

    const processingTime = Date.now() - startTime

    // Add to history
    addPrediction({
      input: { ...ticket.value },
      output: inferRes,
      processingTime,
    })

    toast.success('Prediction complete', {
      description: `Category: ${inferRes.prediction} (${((inferRes.confidence ?? 0) * 100).toFixed(1)}%)`,
    })

    // Fire-and-forget XAI calls
    isLoadingXai.value = true
    
    Promise.all([
      limeMutation.mutateAsync({ ticket_data: ticket.value }).catch((e) => {
        console.warn('LIME explanation failed:', e)
        return null
      }),
      nearestMutation.mutateAsync({ ticket_data: ticket.value }).catch((e) => {
        console.warn('Nearest ticket failed:', e)
        return null
      }),
    ]).then(([limeRes, nearestRes]) => {
      // Only update if this is still the current prediction
      if (thisPredictionId === currentPredictionId) {
        explanation.value = limeRes
        nearestResult.value = nearestRes
      }
    }).finally(() => {
      if (thisPredictionId === currentPredictionId) {
        isLoadingXai.value = false
      }
    })

  } catch (e) {
    toast.error('Prediction failed', { description: (e as Error).message })
  } finally {
    isProcessing.value = false
  }
}

// Example tickets
const exampleTickets: { title: string; description: string }[] = [
  {
    title: 'Jira License Request',
    description: 'I need a Jira license to access the project Agile Transformation and track my development tasks',
  },
  {
    title: 'Laptop Screen Issue',
    description: "My laptop screen is flickering and sometimes goes black. It's affecting my productivity.",
  },
  {
    title: 'VPN Connection Problem',
    description: 'Unable to connect to company VPN from home. Getting timeout errors when trying to authenticate.',
  },
]

const useExample = (example: { title: string; description: string }) => {
  ticket.value = {
    ...ticket.value,
    title_anon: example.title,
    description_anon: example.description,
  }
}

const getPriorityFromConfidence = (confidence: number): string => {
  if (confidence >= 0.9) return 'Critical'
  if (confidence >= 0.7) return 'High'
  if (confidence >= 0.5) return 'Medium'
  return 'Low'
}

const getPriorityVariant = (priority: string): 'destructive' | 'warning' | 'info' | 'secondary' => {
  switch (priority) {
    case 'Critical': return 'destructive'
    case 'High': return 'warning'
    case 'Medium': return 'info'
    default: return 'secondary'
  }
}

const formatTime = (date: Date): string => {
  return date.toLocaleString('en-US', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="inference">
    <!-- Header -->
    <header class="inference__header">
      <div class="inference__header-content">
        <h1 class="inference__title">Inference</h1>
        <p class="inference__subtitle">Use the trained model to predict ticket classifications</p>
      </div>
      <Badge variant="outline" class="inference__badge">
        <Cpu :size="14" />
        AI Prediction Engine
      </Badge>
    </header>

    <!-- Stats Cards Row -->
    <div class="inference__stats">
      <!-- Select Model Card -->
      <Card class="inference__stat-card">
        <div class="stat-card">
          <div class="stat-card__header">
            <Brain :size="18" class="stat-card__icon" />
            <span class="stat-card__title">Select Model</span>
          </div>
          <div class="stat-card__content">
            <InstanceSelector
              :model-value="String(selectedInstanceId || '')"
              placeholder="Select model..."
              @update:model-value="handleInstanceSelect"
            />
            <div v-if="hasInstance && instanceInfo" class="stat-card__accuracy">
              <span class="stat-card__accuracy-label">Model Accuracy</span>
              <div class="stat-card__accuracy-bar">
                <Progress :value="modelAccuracy" :max="100" color="default" />
                <span class="stat-card__accuracy-value">{{ modelAccuracy.toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <!-- Today's Predictions Card -->
      <Card class="inference__stat-card">
        <div class="stat-card">
          <div class="stat-card__header">
            <Zap :size="18" class="stat-card__icon" />
            <span class="stat-card__title">Today's Predictions</span>
          </div>
          <div class="stat-card__content stat-card__content--center">
            <span class="stat-card__value">{{ todayCount() }}</span>
            <span class="stat-card__sublabel">predictions today</span>
          </div>
        </div>
      </Card>

      <!-- Avg Processing Time Card -->
      <Card class="inference__stat-card">
        <div class="stat-card">
          <div class="stat-card__header">
            <Clock :size="18" class="stat-card__icon" />
            <span class="stat-card__title">Avg Processing Time</span>
          </div>
          <div class="stat-card__content stat-card__content--center">
            <span class="stat-card__value">{{ avgProcessingTime() }}ms</span>
            <span class="stat-card__sublabel">per prediction</span>
          </div>
        </div>
      </Card>
    </div>

    <!-- Warning if not trained -->
    <Card v-if="hasInstance && !isTrained" class="inference__warning" variant="outline" padding="sm">
      <div class="warning-content">
        <AlertCircle :size="20" />
        <span>This instance has not been trained yet. Please complete training first.</span>
        <Button variant="outline" size="sm" @click="router.push({ path: '/training', query: { instance: String(selectedInstanceId) } })">
          Go to Training
        </Button>
      </div>
    </Card>

    <!-- Main Content: Two Column Layout -->
    <div class="inference__main">
      <!-- Left Column: Input & Results -->
      <div class="inference__left">
        <!-- Input Section -->
        <Card class="inference__input-card">
          <template #title>Ticket Details</template>
          <template #description>Enter the ticket to classify</template>

          <TicketForm
            v-model="ticket"
            show-categories
            :disabled="!canRunInference"
          />

          <template #footer>
            <div class="input-actions">
              <Button variant="ghost" size="sm" @click="clearInput" :disabled="isProcessing">
                Clear
              </Button>
              <Button
                @click="runPrediction"
                :loading="isProcessing"
                :disabled="!canRunInference || !hasInput"
              >
                <Cpu :size="16" />
                Run Prediction
              </Button>
            </div>
          </template>
        </Card>

        <!-- Results Section -->
        <div v-if="currentPrediction || isProcessing" class="inference__results">
          <!-- Prediction Card -->
          <Card class="results__prediction">
            <template #title>Prediction Result</template>
            <template #action v-if="currentPrediction">
              <Badge variant="success">Complete</Badge>
            </template>

            <div v-if="isProcessing" class="results__loading">
              <Progress :value="undefined" />
              <span>Analyzing ticket...</span>
            </div>

            <PredictionResult
              v-else-if="currentPrediction"
              :prediction="currentPrediction.prediction"
              :confidence="currentPrediction.confidence"
              :probabilities="currentPrediction.probabilities"
              show-details
            />
          </Card>

          <!-- XAI Cards -->
          <Card v-if="currentPrediction" class="results__xai">
            <LimeExplanation
              :explanation="explanation"
              :loading="isLoadingXai && !explanation"
              collapsible
              :default-expanded="true"
            />
          </Card>

          <Card v-if="currentPrediction" class="results__xai">
            <NearestTicket
              :nearest-ticket="nearestResult"
              :ticket-details="nearestTicketDetails"
              :loading="isLoadingXai && !nearestResult"
              show-details
            />
          </Card>
        </div>
      </div>

      <!-- Right Column: History & Examples -->
      <div class="inference__right">
        <!-- Prediction History Section -->
        <Card class="inference__history-card">
          <template #title>Prediction History</template>
          <template #action>
            <div class="history-actions">
              <ExportButton
                v-if="predictionHistory.length > 0"
                :data="exportData"
                filename="prediction_history"
                size="sm"
              />
              <Button
                v-if="predictionHistory.length > 0"
                variant="ghost"
                size="sm"
                @click="clearHistory"
              >
                <Trash2 :size="14" />
              </Button>
              <TrendingUp :size="18" class="history-icon" />
            </div>
          </template>

          <div class="history-section">
            <div v-if="predictionHistory.length === 0" class="history-section__empty">
              <p>No predictions yet. Run a prediction to see history.</p>
            </div>

            <div v-else class="history-section__list">
              <div
                v-for="item in predictionHistory.slice(0, 10)"
                :key="item.id"
                class="history-item"
              >
                <p class="history-item__description">
                  {{ item.input.title_anon || item.input.description_anon }}
                </p>
                <div class="history-item__tags">
                  <Badge variant="secondary">{{ item.output.prediction }}</Badge>
                  <Badge :variant="getPriorityVariant(getPriorityFromConfidence(item.output.confidence ?? 0))">
                    {{ getPriorityFromConfidence(item.output.confidence ?? 0) }}
                  </Badge>
                  <span class="history-item__confidence">
                    {{ ((item.output.confidence ?? 0) * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="history-item__footer">
                  <span class="history-item__time">{{ formatTime(item.timestamp) }}</span>
                  <span class="history-item__processing">{{ item.processingTime }}ms</span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <!-- Example Tickets Section -->
        <Card class="inference__examples-card">
          <template #title>
            <Sparkles :size="18" />
            Example Tickets
          </template>
          <template #description>Try these sample tickets</template>

          <div class="examples-section">
            <div
              v-for="(example, index) in exampleTickets"
              :key="index"
              class="example-item"
            >
              <h4 class="example-item__title">{{ example.title }}</h4>
              <p class="example-item__description">{{ example.description }}</p>
              <Button
                variant="outline"
                size="sm"
                @click="useExample(example)"
                :disabled="!canRunInference"
              >
                Use Example
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.inference {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
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

  &__badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--primary);
  }

  &__stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 1.5rem;

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
    }
  }

  &__stat-card {
    min-height: 140px;
  }

  &__warning {
    margin-bottom: 1.5rem;
  }

  &__main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;

    @media (max-width: 1200px) {
      grid-template-columns: 1fr;
    }
  }

  &__left,
  &__right {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  &__results {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__history-card {
    min-height: 300px;
  }

  &__examples-card {
    :deep(.card__title) {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
  }
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.5rem;

  &__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__icon {
    color: var(--muted-foreground);
  }

  &__title {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--foreground);
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    flex: 1;

    &--center {
      justify-content: center;
    }
  }

  &__value {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
  }

  &__sublabel {
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }

  &__accuracy {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  &__accuracy-label {
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__accuracy-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;

    .progress {
      flex: 1;
    }
  }

  &__accuracy-value {
    font-size: 0.875rem;
    font-weight: 600;
    min-width: 50px;
    text-align: right;
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

.results__xai {
  padding: 1rem;
}

.history-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.history-icon {
  color: var(--muted-foreground);
}

.history-section {
  margin-top: 0.5rem;

  &__empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 150px;
    color: var(--muted-foreground);
    text-align: center;

    p {
      margin: 0;
    }
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 400px;
    overflow-y: auto;
  }
}

.history-item {
  padding: 0.75rem;
  background: var(--muted);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.375rem;

  &__description {
    font-size: 0.8125rem;
    margin: 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__tags {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  &__confidence {
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--success);
  }

  &__footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.6875rem;
    color: var(--muted-foreground);
  }

  &__processing {
    font-family: monospace;
  }
}

.examples-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.example-item {
  padding: 1rem;
  background: var(--muted);
  border-radius: var(--radius);

  &__title {
    font-size: 0.875rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  &__description {
    font-size: 0.8125rem;
    color: var(--muted-foreground);
    margin: 0 0 0.75rem 0;
    line-height: 1.4;
  }
}
</style>
