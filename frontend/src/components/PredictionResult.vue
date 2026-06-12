<script setup lang="ts">
import { computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'

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

const hasProbabilities = computed(() => topProbabilities.value.length > 0)
</script>

<template>
  <Card :variant="compact ? 'elevated' : 'default'" :padding="compact ? 'sm' : 'default'">
    <template #title>
      <div class="prediction-result__header">
        <span class="prediction-result__label">Prediction</span>
        <Badge variant="default" class="prediction-result__value">
          {{ prediction }}
        </Badge>
        <span v-if="confidencePercent !== null" :class="['prediction-result__confidence-inline', `prediction-result__confidence-inline--${confidenceColor}`]">
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
          <div class="prediction-result__prob-heading">Top {{ topProbabilities.length }} predictions</div>
          <div
            v-for="item in topProbabilities"
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
