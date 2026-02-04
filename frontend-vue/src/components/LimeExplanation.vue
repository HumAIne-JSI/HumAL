<script setup lang="ts">
import { computed } from 'vue'
import Progress from '@/components/ui/Progress.vue'
import Button from '@/components/ui/Button.vue'
import { ChevronDown, ChevronUp, Lightbulb } from 'lucide-vue-next'
import type { ExplainLimeResponse } from '@/types/api'

export interface LimeExplanationProps {
  explanation: ExplainLimeResponse | null
  loading?: boolean
  maxWords?: number
  collapsible?: boolean
  defaultExpanded?: boolean
}

const props = withDefaults(defineProps<LimeExplanationProps>(), {
  loading: false,
  maxWords: 10,
  collapsible: true,
  defaultExpanded: false,
})

const isExpanded = defineModel<boolean>('expanded', { default: false })

// Initialize expanded state from defaultExpanded
if (props.defaultExpanded && !isExpanded.value) {
  isExpanded.value = true
}

// Process LIME response into sorted features
interface FeatureImportance {
  word: string
  importance: number
}

const sortedFeatures = computed((): FeatureImportance[] => {
  if (!props.explanation || !props.explanation[0]?.top_words) return []
  return props.explanation[0].top_words
    .map(([word, importance]) => ({ word, importance }))
    .sort((a, b) => Math.abs(b.importance) - Math.abs(a.importance))
    .slice(0, props.maxWords)
})

const hasExplanation = computed(() => sortedFeatures.value.length > 0)

// Compute max importance for scaling bars
const maxImportance = computed(() => {
  if (sortedFeatures.value.length === 0) return 1
  return Math.max(...sortedFeatures.value.map((f) => Math.abs(f.importance)))
})

const getBarWidth = (importance: number): string => {
  // Scale to percentage of max importance
  const percentage = (Math.abs(importance) / maxImportance.value) * 100
  return `${Math.min(percentage, 100)}%`
}

const toggleExpanded = () => {
  if (props.collapsible) {
    isExpanded.value = !isExpanded.value
  }
}
</script>

<template>
  <div class="lime-explanation">
    <!-- Header -->
    <div class="lime-explanation__header">
      <div class="lime-explanation__title">
        <Lightbulb :size="18" />
        <span>Why this prediction?</span>
      </div>
      <Button
        v-if="collapsible && hasExplanation"
        variant="ghost"
        size="sm"
        @click="toggleExpanded"
      >
        {{ isExpanded ? 'Hide' : 'Show' }} Details
        <ChevronDown v-if="!isExpanded" :size="14" />
        <ChevronUp v-else :size="14" />
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="lime-explanation__loading">
      <Progress :value="undefined" />
      <span>Generating explanation...</span>
    </div>

    <!-- Content -->
    <template v-else-if="hasExplanation">
      <div class="lime-explanation__summary">
        <p>The model based its prediction on the following key words:</p>
      </div>

      <div v-if="isExpanded || !collapsible" class="lime-explanation__features">
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
              :style="{ width: getBarWidth(feature.importance) }"
            />
          </div>
          <span
            class="feature-item__value"
            :class="{ 'feature-item__value--negative': feature.importance < 0 }"
          >
            {{ feature.importance.toFixed(3) }}
          </span>
        </div>
      </div>
    </template>

    <!-- No Explanation -->
    <div v-else-if="!loading" class="lime-explanation__empty">
      <span>Explanation not available</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.lime-explanation {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    font-size: 0.9375rem;

    svg {
      color: var(--muted-foreground);
    }
  }

  &__loading {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem 0;
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }

  &__summary {
    p {
      margin: 0;
      font-size: 0.875rem;
      color: var(--muted-foreground);
    }
  }

  &__features {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__empty {
    padding: 1rem;
    text-align: center;
    color: var(--muted-foreground);
    font-size: 0.875rem;
  }
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

    &--negative {
      color: var(--destructive);
    }
  }
}
</style>
