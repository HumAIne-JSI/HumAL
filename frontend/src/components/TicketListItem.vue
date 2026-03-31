<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Checkbox from '@/components/ui/Checkbox.vue'
import { Clock, Users, Sparkles } from 'lucide-vue-next'
import type { QueueTicket, TicketStatus } from '@/stores/useTicketQueueStore'

export interface TicketListItemProps {
  ticket: QueueTicket
  selected?: boolean
  bulkSelected?: boolean
  showBulkCheckbox?: boolean
}

const props = withDefaults(defineProps<TicketListItemProps>(), {
  selected: false,
  bulkSelected: false,
  showBulkCheckbox: false,
})

const emit = defineEmits<{
  (e: 'select'): void
  (e: 'toggle-bulk'): void
}>()

// Status badge variant mapping
const statusVariant = computed((): 'secondary' | 'warning' | 'info' | 'success' => {
  switch (props.ticket.status) {
    case 'unlabeled':
      return 'secondary'
    case 'pending-review':
      return 'warning'
    case 'auto-classified':
      return 'info'
    case 'resolved':
      return 'success'
    default:
      return 'secondary'
  }
})

// Confidence badge variant based on level
const confidenceVariant = computed((): 'success' | 'warning' | 'destructive' | 'secondary' => {
  const conf = props.ticket.confidence
  if (conf === undefined) return 'secondary'
  if (conf >= 0.8) return 'success'
  if (conf >= 0.5) return 'warning'
  return 'destructive'
})

// Format confidence as percentage
const confidencePercent = computed(() => {
  if (props.ticket.confidence === undefined) return null
  return Math.round(props.ticket.confidence * 100)
})

// Format timestamp
const timeAgo = computed(() => {
  const now = new Date()
  const diff = now.getTime() - props.ticket.timestamp.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'Just now'
})

// Truncate text
function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}
</script>

<template>
  <div
    :class="[
      'ticket-item',
      {
        'ticket-item--selected': selected,
        'ticket-item--bulk-selected': bulkSelected,
      },
    ]"
    role="button"
    tabindex="0"
    @click="$emit('select')"
    @keydown.enter="$emit('select')"
    @keydown.space.prevent="$emit('toggle-bulk')"
  >
    <!-- Bulk Selection Checkbox -->
    <div
      v-if="showBulkCheckbox"
      class="ticket-item__checkbox"
      @click.stop
    >
      <Checkbox
        :model-value="bulkSelected"
        @update:model-value="$emit('toggle-bulk')"
      />
    </div>

    <!-- Main Content -->
    <div class="ticket-item__content">
      <!-- Header Row -->
      <div class="ticket-item__header">
        <span class="ticket-item__ref">{{ ticket.ref }}</span>
        <Badge :variant="statusVariant" size="sm">
          {{ ticket.status.replace('-', ' ') }}
        </Badge>
      </div>

      <!-- Title -->
      <h4 class="ticket-item__title">
        {{ truncate(ticket.title, 80) }}
      </h4>

      <!-- Description Preview -->
      <p class="ticket-item__description">
        {{ truncate(ticket.description, 120) }}
      </p>

      <!-- Meta Row -->
      <div class="ticket-item__meta">
        <!-- Team -->
        <span v-if="ticket.team" class="ticket-item__team">
          <Users :size="12" />
          {{ ticket.team }}
        </span>

        <!-- Prediction with Confidence -->
        <span v-if="ticket.prediction && confidencePercent !== null" class="ticket-item__prediction">
          <Sparkles :size="12" />
          {{ ticket.prediction }}
          <Badge :variant="confidenceVariant" size="sm">
            {{ confidencePercent }}%
          </Badge>
        </span>

        <!-- Timestamp -->
        <span class="ticket-item__time">
          <Clock :size="12" />
          {{ timeAgo }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.ticket-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: var(--card);
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--accent);
  }

  &:focus {
    outline: none;
    background: var(--accent);
  }

  &--selected {
    background: color-mix(in srgb, var(--primary) 10%, var(--card));
    border-left: 3px solid var(--primary);
    padding-left: calc(1rem - 3px);

    &:hover {
      background: color-mix(in srgb, var(--primary) 15%, var(--card));
    }
  }

  &--bulk-selected {
    background: color-mix(in srgb, var(--info) 8%, var(--card));
  }

  &__checkbox {
    display: flex;
    align-items: flex-start;
    padding-top: 0.125rem;
  }

  &__content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  &__ref {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--muted-foreground);
    text-transform: uppercase;
  }

  &__title {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--foreground);
    line-height: 1.3;
  }

  &__description {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--muted-foreground);
    line-height: 1.4;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__team,
  &__prediction,
  &__time {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  &__prediction {
    gap: 0.375rem;
  }
}
</style>
