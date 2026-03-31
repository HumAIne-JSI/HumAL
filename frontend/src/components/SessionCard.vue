<script setup lang="ts">
import { computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import type { SessionSummary } from '@/types/api'
import { Activity, Tag, Clock, TrendingUp, Target } from 'lucide-vue-next'

export interface SessionCardProps {
  session: SessionSummary
  selected?: boolean
}

const props = withDefaults(defineProps<SessionCardProps>(), {
  selected: false,
})

const emit = defineEmits<{
  (e: 'select', session: SessionSummary): void
}>()

// Format F1 score as percentage
const f1Display = computed(() => {
  if (props.session.latest_f1 === undefined) return 'N/A'
  return `${(props.session.latest_f1 * 100).toFixed(1)}%`
})

// Format accuracy as percentage
const accuracyDisplay = computed(() => {
  if (props.session.latest_accuracy === undefined) return 'N/A'
  return `${(props.session.latest_accuracy * 100).toFixed(1)}%`
})

// Format date
const dateDisplay = computed(() => {
  try {
    return new Date(props.session.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return props.session.created_at
  }
})

// Get improvement badge variant
const improvementVariant = computed(() => {
  if (!props.session.f1_improvement) return 'secondary'
  return props.session.f1_improvement > 0 ? 'success' : 'warning'
})
</script>

<template>
  <div
    :class="['session-card', { 'session-card--selected': selected }]"
    @click="emit('select', session)"
  >
    <Card variant="default" padding="sm">
      <template #title>
        <div class="session-header">
          <span class="session-id">{{ session.session_id }}</span>
          <Badge variant="outline" class="text-xs">
            {{ session.qs_strategy }}
          </Badge>
        </div>
      </template>

      <template #description>
        <span class="session-model">{{ session.model_name }}</span>
      </template>

      <div class="session-metrics">
        <div class="metric">
          <div class="metric-label">
            <TrendingUp class="w-3.5 h-3.5" />
            F1 Score
          </div>
          <div class="metric-value">{{ f1Display }}</div>
        </div>

        <div class="metric">
          <div class="metric-label">
            <Target class="w-3.5 h-3.5" />
            Accuracy
          </div>
          <div class="metric-value">{{ accuracyDisplay }}</div>
        </div>

        <div class="metric">
          <div class="metric-label">
            <Tag class="w-3.5 h-3.5" />
            Labels
          </div>
          <div class="metric-value">{{ session.total_labeled }}</div>
        </div>

        <div class="metric">
          <div class="metric-label">
            <Activity class="w-3.5 h-3.5" />
            Iterations
          </div>
          <div class="metric-value">{{ session.labeling_iterations }}</div>
        </div>
      </div>

      <template #footer>
        <div class="session-footer">
          <span class="session-date">
            <Clock class="w-3.5 h-3.5" />
            {{ dateDisplay }}
          </span>
          <Badge v-if="session.f1_improvement" :variant="improvementVariant" class="text-xs">
            {{ session.f1_improvement > 0 ? '+' : '' }}{{ (session.f1_improvement * 100).toFixed(1) }}%
          </Badge>
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped lang="scss">
.session-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;

  &:hover {
    transform: translateY(-2px);
  }

  &--selected {
    :deep(.card) {
      border-color: var(--primary);
      box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
    }
  }
}

.session-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.session-id {
  font-family: var(--font-mono, monospace);
  font-size: 0.875rem;
}

.session-model {
  color: var(--muted-foreground);
  font-size: 0.75rem;
}

.session-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.metric-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  color: var(--muted-foreground);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.metric-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--foreground);
}

.session-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.session-date {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--muted-foreground);
}
</style>
