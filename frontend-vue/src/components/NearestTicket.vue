<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Accordion from '@/components/ui/Accordion.vue'
import { Search } from 'lucide-vue-next'
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
}

const props = withDefaults(defineProps<NearestTicketProps>(), {
  loading: false,
  showDetails: true,
  ticketDetails: null,
})

// Process response into display format
const displayData = computed((): NearestTicketDisplay | null => {
  if (!props.nearestTicket) return null
  
  const { nearest_ticket_ref, nearest_ticket_label, similarity_score } = props.nearestTicket
  
  // Handle both array and single value responses
  const ref = Array.isArray(nearest_ticket_ref) ? nearest_ticket_ref[0] : nearest_ticket_ref
  const label = Array.isArray(nearest_ticket_label) ? nearest_ticket_label[0] : nearest_ticket_label
  const similarity = Array.isArray(similarity_score) ? similarity_score[0] : similarity_score
  
  if (!ref || label === undefined || similarity === undefined) return null
  
  return {
    ref: String(ref),
    label: String(label),
    similarity: Number(similarity),
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
      <Progress :value="undefined" />
      <span>Finding similar tickets...</span>
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
