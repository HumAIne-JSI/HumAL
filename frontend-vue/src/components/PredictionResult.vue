<script setup lang="ts">
import { computed, ref } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'
import Button from '@/components/ui/Button.vue'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

export interface PredictionResultProps {
  prediction: string | number
  confidence?: number
  probabilities?: Record<string, number>
  showDetails?: boolean
  compact?: boolean
}

const props = withDefaults(defineProps<PredictionResultProps>(), {
  showDetails: true,
  compact: false,
})

const expanded = ref(false)

const confidencePercent = computed(() => {
  if (props.confidence === undefined) return null
  return Math.round(props.confidence * 100)
})

const confidenceColor = computed(() => {
  if (confidencePercent.value === null) return 'default'
  if (confidencePercent.value >= 80) return 'success'
  if (confidencePercent.value >= 60) return 'warning'
  return 'danger'
})

const sortedProbabilities = computed(() => {
  if (!props.probabilities) return []
  return Object.entries(props.probabilities)
    .map(([label, prob]) => ({ label, probability: prob }))
    .sort((a, b) => b.probability - a.probability)
})

const hasProbabilities = computed(() => sortedProbabilities.value.length > 0)
</script>

<template>
  <Card :variant="compact ? 'outline' : 'default'" :padding="compact ? 'sm' : 'default'">
    <template #title>
      <div class="prediction-result__header">
        <span class="prediction-result__label">Prediction</span>
        <Badge variant="default" class="prediction-result__value">
          {{ prediction }}
        </Badge>
      </div>
    </template>

    <div class="prediction-result__content">
      <div v-if="confidencePercent !== null" class="prediction-result__confidence">
        <div class="prediction-result__confidence-header">
          <span class="prediction-result__confidence-label">Confidence</span>
          <span class="prediction-result__confidence-value">{{ confidencePercent }}%</span>
        </div>
        <Progress :value="confidencePercent" :max="100" :color="confidenceColor" />
      </div>

      <template v-if="showDetails && hasProbabilities">
        <Button
          variant="ghost"
          size="sm"
          class="prediction-result__toggle"
          @click="expanded = !expanded"
        >
          <template v-if="expanded">
            <ChevronUp :size="16" />
            Hide probabilities
          </template>
          <template v-else>
            <ChevronDown :size="16" />
            Show all probabilities
          </template>
        </Button>

        <div v-if="expanded" class="prediction-result__probabilities">
          <div
            v-for="item in sortedProbabilities"
            :key="item.label"
            class="prediction-result__prob-item"
          >
            <span class="prediction-result__prob-label">{{ item.label }}</span>
            <div class="prediction-result__prob-bar-container">
              <Progress
                :value="Math.round(item.probability * 100)"
                :max="100"
                :color="item.label === String(prediction) ? 'success' : 'default'"
              />
            </div>
            <span class="prediction-result__prob-value">
              {{ (item.probability * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </template>
    </div>
  </Card>
</template>

<style scoped lang="scss">
.prediction-result {
  &__header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  &__label {
    font-weight: 500;
    color: var(--muted-foreground);
  }

  &__value {
    font-size: 1rem;
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 0.75rem;
  }

  &__confidence {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  &__confidence-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__confidence-label {
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }

  &__confidence-value {
    font-size: 0.875rem;
    font-weight: 600;
  }

  &__toggle {
    align-self: flex-start;
    margin-top: 0.5rem;
  }

  &__probabilities {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--muted);
    border-radius: var(--radius);
    margin-top: 0.5rem;
  }

  &__prob-item {
    display: grid;
    grid-template-columns: 120px 1fr 60px;
    gap: 0.75rem;
    align-items: center;
    font-size: 0.875rem;
  }

  &__prob-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__prob-bar-container {
    flex: 1;
  }

  &__prob-value {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
}
</style>
