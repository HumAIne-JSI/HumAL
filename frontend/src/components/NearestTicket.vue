<script setup lang="ts">
import { computed, watch } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Spinner from '@/components/ui/Spinner.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Accordion from '@/components/ui/Accordion.vue'
import { Search } from 'lucide-vue-next'
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry'
import type { NearestTicketResponse, Ticket } from '@/types/api'

export interface NearestTicketDisplay {
  ref: string
  label: string
  similarity: number
  details?: Ticket | null
}

export interface NearestTicketProps {
  nearestTicket: NearestTicketResponse | null
  ticketDetails?: Ticket | null
  loading?: boolean
  showDetails?: boolean
  sourceTicketRef?: string | null
  page?: string
}

const props = withDefaults(defineProps<NearestTicketProps>(), {
  loading: false,
  showDetails: true,
  ticketDetails: null,
  sourceTicketRef: null,
  page: 'queue_aided',
})

const telemetry = useBenchmarkTelemetry()

// Process response into display format
const displayData = computed((): NearestTicketDisplay | null => {
  if (!props.nearestTicket) return null

  const neighbor =
    props.nearestTicket.predicted_class_neighbors?.[0] ??
    props.nearestTicket.historical_neighbors?.[0] ??
    null

  if (!neighbor || !neighbor.ref) return null

  return {
    ref: String(neighbor.ref),
    label: String(neighbor.label ?? ''),
    similarity: Number(neighbor.similarity ?? 0),
    details: props.ticketDetails,
  }
})

const hasData = computed(() => displayData.value !== null)

// Similarity badge variant based on score
const similarityVariant = computed((): 'success' | 'info' | 'secondary' => {
  if (!displayData.value) return 'secondary'
  if (displayData.value.similarity >= 0.8) return 'success'
  if (displayData.value.similarity >= 0.5) return 'info'
  return 'secondary'
})

const similarityPercentage = computed(() => {
  if (!displayData.value) return 0
  return Math.round(displayData.value.similarity * 100 * 10) / 10
})

// Emit `view_nearest_ticket` once when the panel first receives data, so the
// dashboard can credit XAI engagement against the active ticket.
watch(
  () => displayData.value?.ref,
  (next, prev) => {
    if (next && next !== prev) {
      telemetry.recordView('view_nearest_ticket', props.sourceTicketRef ?? null, props.page, {
        nearest_ref: next,
        similarity: displayData.value?.similarity ?? null,
      })
    }
  },
)
</script>

<template>
  <div class="nearest-ticket">
    <!-- Header -->
    <div class="nearest-ticket__header">
      <div class="nearest-ticket__title">
        <Search :size="18" />
        <span>Similar Ticket</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="nearest-ticket__loading">
      <Spinner label="Finding similar tickets..." />
    </div>

    <!-- Content -->
    <template v-else-if="hasData && displayData">
      <div class="nearest-ticket__summary">
        <p>
          Found a previously labeled ticket that is 
          <strong>{{ similarityPercentage }}%</strong> similar to this one.
        </p>
      </div>

      <div class="nearest-ticket__info">
        <div class="info-row">
          <span class="info-row__label">Ticket Reference:</span>
          <Badge variant="outline">{{ displayData.ref }}</Badge>
        </div>
        <div class="info-row">
          <span class="info-row__label">Assigned Team:</span>
          <Badge variant="secondary">{{ displayData.label }}</Badge>
        </div>
        <div class="info-row">
          <span class="info-row__label">Similarity Score:</span>
          <Badge :variant="similarityVariant">
            {{ similarityPercentage }}%
          </Badge>
        </div>
      </div>

      <!-- Ticket Details (if available) -->
      <template v-if="showDetails && displayData.details">
        <Accordion type="single" collapsible class="nearest-ticket__details">
          <template #default>
            <div class="ticket-details">
              <div class="ticket-details__categories">
                <Badge v-if="displayData.details['Service->Name']" variant="secondary">
                  {{ displayData.details['Service->Name'] }}
                </Badge>
                <Badge v-if="displayData.details['Service subcategory->Name']" variant="outline">
                  {{ displayData.details['Service subcategory->Name'] }}
                </Badge>
              </div>

              <div v-if="displayData.details.Title_anon" class="ticket-details__field">
                <span class="ticket-details__label">Title:</span>
                <p class="ticket-details__value">{{ displayData.details.Title_anon }}</p>
              </div>

              <div v-if="displayData.details.Description_anon" class="ticket-details__field">
                <span class="ticket-details__label">Description:</span>
                <Textarea
                  :model-value="displayData.details.Description_anon"
                  readonly
                  :rows="3"
                  class="ticket-details__description"
                />
              </div>
            </div>
          </template>
        </Accordion>
      </template>
    </template>

    <!-- No Data -->
    <div v-else-if="!loading" class="nearest-ticket__empty">
      <span>No similar tickets found</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.nearest-ticket {
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

      strong {
        color: var(--foreground);
      }
    }
  }

  &__info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--muted);
    border-radius: var(--radius);
  }

  &__details {
    margin-top: 0.5rem;
  }

  &__empty {
    padding: 1rem;
    text-align: center;
    color: var(--muted-foreground);
    font-size: 0.875rem;
  }
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.875rem;

  &__label {
    font-weight: 500;
  }
}

.ticket-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--muted);
  border-radius: var(--radius);

  &__categories {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--muted-foreground);
  }

  &__value {
    margin: 0;
    font-size: 0.875rem;
  }

  &__description {
    font-size: 0.875rem;
    resize: none;
  }
}
</style>
