<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Progress from '@/components/ui/Progress.vue'
import Select from '@/components/ui/Select.vue'
import { useInstances, useInstanceInfo } from '@/composables/api/useActiveLearning'
import { useInferWithModelCheck } from '@/composables/api/useInference'
import type { InferenceData, InferenceResponse } from '@/types/api'
import {
  Zap,
  Brain,
  Clock,
  TrendingUp,
  Cpu,
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

// Fetch all instances
const { data: instancesData } = useInstances()

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

// Single ticket input
const ticketDescription = ref('')

// Prediction history
interface PredictionHistoryItem {
  id: number
  description: string
  prediction: string
  priority: string
  confidence: number
  team: string
  timestamp: Date
}
const predictionHistory = ref<PredictionHistoryItem[]>([])

// Processing state
const isProcessing = ref(false)

// Stats
const todayPredictions = ref(0)
const avgProcessingTime = ref(0)

// Results
interface InferenceResult {
  input: InferenceData
  output: InferenceResponse | null
  error?: string
}
const currentResult = ref<InferenceResult | null>(null)

// Computed
const hasInstance = computed(() => selectedInstanceId.value > 0)
const isTrained = computed(() => instanceInfo.value?.test_accuracy !== undefined)
const canRunInference = computed(() => hasInstance.value && isTrained.value)

// Model options for select - show all instances, not just trained
const modelOptions = computed(() => {
  const instances = instancesData.value?.instances ?? {}
  return Object.entries(instances)
    .map(([id, info]) => {
      const accuracy = info.test_accuracy ?? info.training_accuracy
      const accuracyStr = accuracy !== undefined ? ` (${(accuracy * 100).toFixed(1)}%)` : ''
      return {
        value: id,
        label: `${info.model_name ?? info.model ?? 'Model'} v${id}${accuracyStr}`,
      }
    })
})

// Model accuracy for display
const modelAccuracy = computed(() => {
  if (!instanceInfo.value) return 0
  return (instanceInfo.value.test_accuracy ?? instanceInfo.value.training_accuracy ?? 0) * 100
})

// Methods
const handleInstanceSelect = (value: string) => {
  selectedInstanceId.value = Number(value) || 0
}

const clearInput = () => {
  ticketDescription.value = ''
  currentResult.value = null
}

const runPrediction = async () => {
  if (!ticketDescription.value.trim()) {
    toast.error('Empty ticket', { description: 'Please enter a ticket description' })
    return
  }

  isProcessing.value = true
  const startTime = Date.now()

  try {
    const input: InferenceData = {
      title_anon: '',
      description_anon: ticketDescription.value,
    }
    const output = await inferMutation.mutateAsync(input)
    currentResult.value = { input, output }

    // Update stats
    const processingTime = Date.now() - startTime
    avgProcessingTime.value = avgProcessingTime.value === 0
      ? processingTime
      : Math.round((avgProcessingTime.value + processingTime) / 2)
    todayPredictions.value++

    // Add to history
    predictionHistory.value.unshift({
      id: Date.now(),
      description: ticketDescription.value,
      prediction: String(output.prediction),
      priority: getPriorityFromConfidence(output.confidence),
      confidence: output.confidence,
      team: `${output.prediction} Team`,
      timestamp: new Date(),
    })

    // Keep only last 10 items
    if (predictionHistory.value.length > 10) {
      predictionHistory.value = predictionHistory.value.slice(0, 10)
    }

    toast.success('Prediction complete', {
      description: `Category: ${output.prediction} (${(output.confidence * 100).toFixed(1)}%)`,
    })
  } catch (e) {
    currentResult.value = {
      input: { title_anon: '', description_anon: ticketDescription.value },
      output: null,
      error: (e as Error).message,
    }
    toast.error('Prediction failed', { description: (e as Error).message })
  } finally {
    isProcessing.value = false
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
    year: 'numeric',
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
            <Select
              :model-value="String(selectedInstanceId || '')"
              :options="modelOptions"
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
            <span class="stat-card__value">{{ todayPredictions }}</span>
            <span class="stat-card__change stat-card__change--positive">
              +{{ todayPredictions }} from yesterday
            </span>
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
            <span class="stat-card__value">{{ avgProcessingTime || 0 }}ms</span>
            <span class="stat-card__sublabel">Per prediction</span>
          </div>
        </div>
      </Card>
    </div>

    <!-- Main Content: Two Column Layout -->
    <div class="inference__main">
      <!-- Input Section -->
      <Card class="inference__input-card">
        <template #title>Input Ticket Description</template>

        <div class="input-section">
          <label class="input-section__label">Ticket Description</label>
          <Textarea
            v-model="ticketDescription"
            placeholder="Enter the ticket description here... e.g., 'Users cannot access the company VPN from home'"
            :rows="6"
            :disabled="!canRunInference"
          />
        </div>

        <template #footer>
          <div class="input-section__actions">
            <Button
              @click="runPrediction"
              :loading="isProcessing"
              :disabled="!canRunInference || !ticketDescription.trim()"
              class="input-section__run-btn"
            >
              <Cpu :size="16" />
              Run Prediction
            </Button>
            <Button
              variant="outline"
              @click="clearInput"
              :disabled="!ticketDescription.trim() && !currentResult"
            >
              Clear
            </Button>
          </div>
        </template>
      </Card>

      <!-- Prediction History Section -->
      <Card class="inference__history-card">
        <template #title>Prediction History</template>
        <template #action>
          <TrendingUp :size="18" class="history-icon" />
        </template>

        <div class="history-section">
          <div v-if="predictionHistory.length === 0" class="history-section__empty">
            <p>No predictions yet. Run a prediction to see history.</p>
          </div>

          <div v-else class="history-section__list">
            <div
              v-for="item in predictionHistory"
              :key="item.id"
              class="history-item"
            >
              <p class="history-item__description">{{ item.description }}</p>
              <div class="history-item__tags">
                <Badge variant="secondary">{{ item.prediction }}</Badge>
                <Badge :variant="getPriorityVariant(item.priority)">{{ item.priority }}</Badge>
                <span class="history-item__confidence">{{ (item.confidence * 100).toFixed(1) }}%</span>
              </div>
              <div class="history-item__footer">
                <span class="history-item__team">{{ item.team }}</span>
                <span class="history-item__time">{{ formatTime(item.timestamp) }}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>
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
    min-height: 160px;
  }

  &__main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
    }
  }

  &__input-card,
  &__history-card {
    min-height: 400px;
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

  &__change {
    font-size: 0.875rem;

    &--positive {
      color: var(--success);
    }

    &--negative {
      color: var(--destructive);
    }
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

.input-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  &__label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--foreground);
  }

  &__actions {
    display: flex;
    gap: 0.75rem;
    width: 100%;
  }

  &__run-btn {
    flex: 1;
  }
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
    min-height: 200px;
    color: var(--muted-foreground);
    text-align: center;

    p {
      margin: 0;
    }
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
}

.history-item {
  padding: 1rem;
  background: var(--muted);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  &__description {
    font-size: 0.875rem;
    margin: 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
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
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--success);
  }

  &__footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75rem;
    color: var(--muted-foreground);
    margin-top: 0.25rem;
  }

  &__team {
    font-weight: 500;
  }

  &__time {
    text-align: right;
  }
}
</style>
