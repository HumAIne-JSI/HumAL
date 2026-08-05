<script setup lang="ts">
import { computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'
import type { TopKPrediction } from '@/types/api'

export interface PredictionResultProps {
  prediction: string | number
  confidence?: number
  probabilities?: Record<string, number>
  predictions?: TopKPrediction[]
  showDetails?: boolean
  compact?: boolean
}

const props = withDefaults(defineProps<PredictionResultProps>(), {
  showDetails: true,
  compact: false,
})

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

const topProbabilities = computed(() => {
  if (!props.probabilities) return []
  return Object.entries(props.probabilities)
    .map(([label, prob]) => ({ label, probability: prob }))
    .sort((a, b) => b.probability - a.probability)
    .slice(0, 3)
})

const displayedPredictions = computed(() =>
  props.predictions?.length ? props.predictions.slice(0, 2) : topProbabilities.value,
)

const hasProbabilities = computed(() => displayedPredictions.value.length > 0)
</script>

<template>
  <Card :variant="compact ? 'elevated' : 'default'" :padding="compact ? 'sm' : 'default'">
    <template #title>
      <div class="prediction-result__header">
        <span class="prediction-result__label">
          {{ predictions?.length ? 'AI Suggestions' : 'AI Suggestion' }}
        </span>
        <Badge variant="default" class="prediction-result__value">
          {{ prediction }}
        </Badge>
        <span
          v-if="confidencePercent !== null"
          :class="[
            'prediction-result__confidence-inline',
            `prediction-result__confidence-inline--${confidenceColor}`,
          ]"
        >
          {{ confidencePercent }}%
        </span>
      </div>
    </template>

    <template v-if="$slots.actions" #action>
      <slot name="actions" />
    </template>

    <div class="prediction-result__content">
      <template v-if="showDetails && hasProbabilities">
        <div class="prediction-result__probabilities">
          <div class="prediction-result__prob-heading">
            Top {{ displayedPredictions.length }} suggestions
          </div>
          <div
            v-for="(item, index) in displayedPredictions"
            :key="item.label"
            :class="[
              'prediction-result__prob-item',
              { 'prediction-result__prob-item--actionable': $slots['prediction-action'] },
            ]"
          >
            <span class="prediction-result__rank">{{ index + 1 }}</span>
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
            <slot name="prediction-action" :prediction="item" :rank="index + 1" />
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
    font-size: 0.8125rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--muted-foreground);
  }

  &__value {
    font-size: 0.9375rem;
    font-weight: 600;
  }

  &__confidence-inline {
    font-size: 0.8125rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--muted-foreground);
    margin-left: auto;

    &--success {
      color: var(--success);
    }

    &--warning {
      color: var(--warning);
    }

    &--danger {
      color: var(--destructive);
    }
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
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

  &__prob-heading {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--muted-foreground);
    margin-bottom: 0.125rem;
  }

  &__prob-item {
    display: grid;
    grid-template-columns: 1.25rem 120px 1fr 60px;
    gap: 0.75rem;
    align-items: center;
    font-size: 0.875rem;

    &--actionable {
      grid-template-columns: 1.25rem minmax(90px, 120px) minmax(80px, 1fr) 60px auto;
    }
  }

  &__rank {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.25rem;
    height: 1.25rem;
    border-radius: 999px;
    background: var(--background);
    color: var(--muted-foreground);
    font-size: 0.6875rem;
    font-weight: 600;
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
