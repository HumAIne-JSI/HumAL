<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import Accordion from '@/components/ui/Accordion.vue'
import InstanceSelector from '@/components/InstanceSelector.vue'
import TicketForm from '@/components/TicketForm.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import ExportButton from '@/components/ExportButton.vue'
import { useInstances, useInstanceInfo } from '@/composables/api/useActiveLearning'
import { useInferWithModelCheck } from '@/composables/api/useInference'
import { useExplainLimeMutation, useNearestTicketMutation } from '@/composables/api/useXai'
import type { InferenceData, InferenceResponse, ExplainLimeResponse, NearestTicketResponse } from '@/types/api'
import {
  Zap,
  Search,
  Brain,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Lightbulb,
  Target,
  FileText,
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

// Input
const ticket = ref<InferenceData>({
  title_anon: '',
  description_anon: '',
})

// Results - use correct API types
const prediction = ref<InferenceResponse | null>(null)
const explanation = ref<ExplainLimeResponse | null>(null)
const nearestResult = ref<NearestTicketResponse | null>(null)

// Processing states
const isRunning = ref(false)
const showExplanation = ref(false)

// Computed
const hasInstance = computed(() => selectedInstanceId.value > 0)
const isTrained = computed(() => instanceInfo.value?.test_accuracy !== undefined)
const canRun = computed(() => hasInstance.value && isTrained.value)
const hasInput = computed(() => !!(ticket.value.title_anon || ticket.value.description_anon))

// Sorted explanation features by importance (top_words from LIME response)
interface FeatureImportance {
  word: string
  importance: number
}

const sortedFeatures = computed((): FeatureImportance[] => {
  if (!explanation.value || !explanation.value[0]?.top_words) return []
  // top_words is [string, number][]
  return explanation.value[0].top_words
    .map(([word, importance]) => ({ word, importance }))
    .sort((a, b) => Math.abs(b.importance) - Math.abs(a.importance))
    .slice(0, 10)
})

// Process nearest tickets response into display format
interface NearestTicketDisplay {
  ref: string
  team: string
  similarity: number
}

const nearestTickets = computed((): NearestTicketDisplay[] => {
  if (!nearestResult.value) return []
  const { nearest_ticket_ref, nearest_ticket_label, similarity_score } = nearestResult.value
  
  // Handle both array and single value responses
  const refs = Array.isArray(nearest_ticket_ref) ? nearest_ticket_ref : [nearest_ticket_ref]
  const labels = Array.isArray(nearest_ticket_label) ? nearest_ticket_label : [nearest_ticket_label]
  const scores = Array.isArray(similarity_score) ? similarity_score : [similarity_score]
  
  return refs.map((ref, i) => ({
    ref,
    team: labels[i] ?? 'Unknown',
    similarity: scores[i] ?? 0,
  }))
})

// Export data
const exportData = computed(() => {
  if (!prediction.value) return []
  return [
    {
      title: ticket.value.title_anon,
      description: ticket.value.description_anon,
      prediction: prediction.value.prediction,
      confidence: prediction.value.confidence,
      ...Object.fromEntries(
        Object.entries(prediction.value.probabilities ?? {}).map(([k, v]) => [`prob_${k}`, v])
      ),
      explanation_features: sortedFeatures.value.map((f) => `${f.word}: ${f.importance.toFixed(3)}`).join('; '),
      nearest_tickets: nearestTickets.value.map((t) => `${t.team}: ${t.ref}`).join(' | '),
    },
  ]
})

// Methods
const handleInstanceSelect = (value: string) => {
  selectedInstanceId.value = Number(value) || 0
  // Clear results on instance change
  prediction.value = null
  explanation.value = null
  nearestResult.value = null
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

  try {
    // Run inference
    const inferRes = await inferMutation.mutateAsync(ticket.value)
    prediction.value = inferRes

    // Run XAI in parallel - use correct payload structure
    const [limeRes, nearestRes] = await Promise.all([
      limeMutation.mutateAsync({ ticket_data: ticket.value }).catch((e) => {
        console.warn('LIME explanation failed:', e)
        return null
      }),
      nearestMutation.mutateAsync({ ticket_data: ticket.value }).catch((e) => {
        console.warn('Nearest tickets failed:', e)
        return null
      }),
    ])

    explanation.value = limeRes
    nearestResult.value = nearestRes

    toast.success('Dispatch analysis complete')
  } catch (e) {
    toast.error('Dispatch failed', { description: (e as Error).message })
  } finally {
    isRunning.value = false
  }
}

const clearAll = () => {
  ticket.value = { title_anon: '', description_anon: '' }
  prediction.value = null
  explanation.value = null
  nearestResult.value = null
}
</script>

<template>
  <div class="dispatching">
    <header class="dispatching__header">
      <div class="dispatching__header-content">
        <h1 class="dispatching__title">Ticket Dispatching</h1>
        <p class="dispatching__subtitle">Predict ticket assignments with explainable AI insights</p>
      </div>
      <div class="dispatching__header-actions">
        <InstanceSelector
          :model-value="String(selectedInstanceId || '')"
          placeholder="Select model..."
          filter-trained
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

    <!-- Warning if not trained -->
    <Card v-if="hasInstance && !isTrained" class="dispatching__warning" variant="outline" padding="sm">
      <div class="warning-content">
        <AlertCircle :size="20" />
        <span>This instance has not been trained yet. Please complete training first.</span>
        <Button variant="outline" size="sm" @click="router.push({ path: '/training', query: { instance: String(selectedInstanceId) } })">
          Go to Training
        </Button>
      </div>
    </Card>

    <!-- No instance selected -->
    <div v-if="!hasInstance" class="dispatching__empty">
      <Brain :size="48" class="dispatching__empty-icon" />
      <h3>No model selected</h3>
      <p>Select a trained model to analyze ticket dispatching</p>
    </div>

    <!-- Main Content -->
    <template v-else-if="canRun">
      <div class="dispatching__content">
        <!-- Input Section -->
        <Card class="dispatching__input">
          <template #title>Ticket Details</template>
          <template #description>Enter the ticket to analyze</template>

          <TicketForm v-model="ticket" show-categories show-all-fields />

          <template #footer>
            <div class="input-actions">
              <Button variant="ghost" size="sm" @click="clearAll" :disabled="isRunning">
                Clear
              </Button>
              <Button @click="runDispatch" :loading="isRunning" :disabled="!hasInput">
                <Zap :size="16" />
                Analyze & Dispatch
              </Button>
            </div>
          </template>
        </Card>

        <!-- Results Section -->
        <div v-if="prediction || isRunning" class="dispatching__results">
          <!-- Prediction Card -->
          <Card class="results__prediction">
            <template #title>
              <Target :size="18" />
              Prediction
            </template>
            <template #action v-if="prediction">
              <ExportButton :data="exportData" filename="dispatch_result" />
            </template>

            <div v-if="isRunning" class="results__loading">
              <Progress :value="undefined" />
              <span>Analyzing ticket...</span>
            </div>

            <PredictionResult
              v-else-if="prediction"
              :prediction="prediction.prediction"
              :confidence="prediction.confidence"
              :probabilities="prediction.probabilities"
              show-details
            />
          </Card>

          <!-- Explanation Card -->
          <Card v-if="explanation || isRunning" class="results__explanation">
            <template #title>
              <Lightbulb :size="18" />
              Why this prediction?
            </template>
            <template #action>
              <Button
                variant="ghost"
                size="sm"
                @click="showExplanation = !showExplanation"
              >
                {{ showExplanation ? 'Hide' : 'Show' }} Details
                <ChevronDown v-if="!showExplanation" :size="14" />
                <ChevronUp v-else :size="14" />
              </Button>
            </template>

            <div v-if="isRunning" class="results__loading">
              <Progress :value="undefined" />
              <span>Generating explanation...</span>
            </div>

            <template v-else-if="explanation && sortedFeatures.length > 0">
              <div class="explanation-summary">
                <p>The model based its prediction on the following key words:</p>
              </div>

              <div v-if="showExplanation" class="explanation-features">
                <div
                  v-for="(feature, index) in sortedFeatures"
                  :key="index"
                  class="feature-item"
                >
                  <span class="feature-item__word">{{ feature.word }}</span>
                  <div class="feature-item__bar-container">
                    <div
                      class="feature-item__bar"
                      :class="{ 'feature-item__bar--negative': feature.importance < 0 }"
                      :style="{ width: `${Math.abs(feature.importance) * 100}%` }"
                    />
                  </div>
                  <span class="feature-item__value" :class="{ negative: feature.importance < 0 }">
                    {{ feature.importance.toFixed(3) }}
                  </span>
                </div>
              </div>
            </template>

            <div v-else class="no-explanation">
              <span>Explanation not available</span>
            </div>
          </Card>

          <!-- Similar Tickets Card -->
          <Card v-if="nearestTickets.length > 0 || isRunning" class="results__similar">
            <template #title>
              <Search :size="18" />
              Similar Past Tickets
            </template>

            <div v-if="isRunning" class="results__loading">
              <Progress :value="undefined" />
              <span>Finding similar tickets...</span>
            </div>

            <Accordion
              v-else-if="nearestTickets.length > 0"
              type="single"
              collapsible
            >
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
            </Accordion>

            <div v-else class="no-similar">
              <span>No similar tickets found</span>
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

.explanation-summary {
  p {
    margin: 0;
    font-size: 0.9375rem;

    strong {
      color: var(--primary);
    }
  }
}

.explanation-features {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.feature-item {
  display: grid;
  grid-template-columns: 120px 1fr 60px;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;

  &__word {
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__bar-container {
    height: 8px;
    background: var(--muted);
    border-radius: 4px;
    overflow: hidden;
  }

  &__bar {
    height: 100%;
    background: var(--primary);
    border-radius: 4px;
    transition: width 0.3s ease;

    &--negative {
      background: var(--destructive);
    }
  }

  &__value {
    text-align: right;
    font-family: monospace;
    color: var(--primary);

    &.negative {
      color: var(--destructive);
    }
  }
}

.no-explanation,
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
</style>