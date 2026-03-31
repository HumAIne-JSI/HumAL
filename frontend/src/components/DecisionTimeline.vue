<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import type { Decision } from '@/types/api'
import {
  getActorTypeLabel,
  formatTimestamp,
  formatActionName,
} from '@/data/sampleAnalytics'
import { Clock, Bot, User, Settings, ChevronDown, ChevronRight } from 'lucide-vue-next'

export interface DecisionTimelineProps {
  decisions: Decision[]
  maxVisible?: number
  showPayload?: boolean
}

const props = withDefaults(defineProps<DecisionTimelineProps>(), {
  maxVisible: 0, // 0 = show all
  showPayload: true,
})

const emit = defineEmits<{
  (e: 'select', decision: Decision): void
}>()

// Computed: visible decisions (optionally limited)
const visibleDecisions = computed(() => {
  if (props.maxVisible === 0 || props.maxVisible >= props.decisions.length) {
    return props.decisions
  }
  return props.decisions.slice(0, props.maxVisible)
})

const hasMore = computed(() => {
  return props.maxVisible > 0 && props.maxVisible < props.decisions.length
})

// Get icon component for actor type
function getActorIcon(actorType: 'system' | 'ai' | 'human') {
  switch (actorType) {
    case 'system': return Settings
    case 'ai': return Bot
    case 'human': return User
  }
}

// Get badge variant for actor type
function getActorVariant(actorType: 'system' | 'ai' | 'human') {
  switch (actorType) {
    case 'system': return 'secondary'
    case 'ai': return 'info'
    case 'human': return 'success'
  }
}

// Format payload for display (simplified)
function formatPayload(payload: Record<string, unknown>): string {
  const entries = Object.entries(payload)
  if (entries.length === 0) return ''
  
  return entries
    .slice(0, 3)
    .map(([k, v]) => {
      const value = typeof v === 'object' ? JSON.stringify(v) : String(v)
      const truncated = value.length > 50 ? value.slice(0, 47) + '...' : value
      return `${k}: ${truncated}`
    })
    .join(' | ')
}
</script>

<template>
  <div class="decision-timeline">
    <div 
      v-for="(decision, index) in visibleDecisions" 
      :key="index"
      class="timeline-item"
      @click="emit('select', decision)"
    >
      <!-- Timeline connector -->
      <div class="timeline-connector">
        <div class="timeline-dot" :class="`timeline-dot--${decision.actor_type}`">
          <component :is="getActorIcon(decision.actor_type)" class="w-3 h-3" />
        </div>
        <div v-if="index < visibleDecisions.length - 1" class="timeline-line"></div>
      </div>

      <!-- Content -->
      <div class="timeline-content">
        <div class="timeline-header">
          <Badge :variant="getActorVariant(decision.actor_type)" class="text-xs">
            {{ getActorTypeLabel(decision.actor_type) }}
          </Badge>
          <span class="timeline-action">{{ formatActionName(decision.action) }}</span>
          <span class="timeline-time">
            <Clock class="w-3 h-3" />
            {{ formatTimestamp(decision.t) }}
          </span>
        </div>

        <!-- Optional metadata -->
        <div v-if="decision.interaction_id || decision.latency_ms || decision.duration_s" class="timeline-meta">
          <span v-if="decision.interaction_id" class="meta-item">
            ID: {{ decision.interaction_id }}
          </span>
          <span v-if="decision.latency_ms" class="meta-item">
            Latency: {{ decision.latency_ms.toFixed(0) }}ms
          </span>
          <span v-if="decision.duration_s" class="meta-item">
            Duration: {{ decision.duration_s.toFixed(1) }}s
          </span>
        </div>

        <!-- Payload preview -->
        <div v-if="showPayload && Object.keys(decision.payload).length > 0" class="timeline-payload">
          {{ formatPayload(decision.payload) }}
        </div>
      </div>
    </div>

    <!-- Show more indicator -->
    <div v-if="hasMore" class="timeline-more">
      <span class="text-muted-foreground text-sm">
        + {{ decisions.length - maxVisible }} more decisions
      </span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.decision-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--radius);
  transition: background-color 0.15s ease;

  &:hover {
    background-color: var(--accent);
  }
}

.timeline-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 1.5rem;
  flex-shrink: 0;
}

.timeline-dot {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;

  &--system {
    background-color: var(--muted-foreground);
  }

  &--ai {
    background-color: hsl(217, 91%, 60%);
  }

  &--human {
    background-color: hsl(142, 76%, 36%);
  }
}

.timeline-line {
  width: 2px;
  flex-grow: 1;
  min-height: 1rem;
  background-color: var(--border);
  margin-top: 0.25rem;
}

.timeline-content {
  flex: 1;
  min-width: 0;
  padding-bottom: 0.5rem;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.timeline-action {
  font-weight: 500;
  color: var(--foreground);
}

.timeline-time {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--muted-foreground);
  font-size: 0.75rem;
  margin-left: auto;
}

.timeline-meta {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.timeline-payload {
  margin-top: 0.25rem;
  padding: 0.375rem 0.5rem;
  background-color: var(--muted);
  border-radius: calc(var(--radius) - 2px);
  font-size: 0.75rem;
  color: var(--muted-foreground);
  font-family: var(--font-mono, monospace);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-more {
  padding: 0.5rem 0.5rem 0.5rem 2.25rem;
}
</style>
