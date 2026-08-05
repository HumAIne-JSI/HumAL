<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { History, Search } from 'lucide-vue-next'

export interface NeighborTicketView {
  title?: string
  description?: string
  ref?: string
  label?: string
  similarity?: number
}

interface Props {
  historicalTicket?: NeighborTicketView | null
  predictedClassTicket?: NeighborTicketView | null
  loadingSimilar?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  historicalTicket: null,
  predictedClassTicket: null,
  loadingSimilar: false,
})

const historicalSimilarityPercent = computed(() =>
  formatSimilarity(props.historicalTicket?.similarity),
)
const predictedClassSimilarityPercent = computed(() =>
  formatSimilarity(props.predictedClassTicket?.similarity),
)

function formatSimilarity(similarity?: number): number | null {
  if (similarity === undefined || similarity === null) return null
  return Math.round(similarity * 100)
}

function similarityVariant(percent: number | null): 'success' | 'info' | 'secondary' {
  if (percent === null) return 'secondary'
  if (percent >= 80) return 'success'
  if (percent >= 50) return 'info'
  return 'secondary'
}

const hasHistoricalTicket = computed(() =>
  Boolean(
    props.historicalTicket?.ref ||
    props.historicalTicket?.title ||
    props.historicalTicket?.description,
  ),
)
const hasPredictedClassTicket = computed(() =>
  Boolean(
    props.predictedClassTicket?.ref ||
    props.predictedClassTicket?.title ||
    props.predictedClassTicket?.description,
  ),
)
</script>

<template>
  <section class="side-by-side" data-track-region="nearest_ticket_comparison">
    <header class="side-by-side__header">
      <Search :size="14" />
      <span class="side-by-side__title">Why this suggestion</span>
    </header>

    <div v-if="loadingSimilar" class="side-by-side__loading">
      <Spinner label="Finding similar tickets..." />
    </div>

    <div v-else class="side-by-side__grid">
      <article class="side-by-side__col" data-track-region="historical_neighbor">
        <header class="side-by-side__col-header">
          <History :size="12" class="side-by-side__col-icon" />
          <span class="side-by-side__col-label">Closest past ticket</span>
          <Badge v-if="historicalTicket?.ref" variant="outline" class="side-by-side__col-badge">
            {{ historicalTicket.ref }}
          </Badge>
          <Badge v-if="historicalTicket?.label" variant="secondary" class="side-by-side__col-badge">
            {{ historicalTicket.label }}
          </Badge>
          <Badge
            v-if="historicalSimilarityPercent !== null"
            :variant="similarityVariant(historicalSimilarityPercent)"
            class="side-by-side__col-badge"
          >
            {{ historicalSimilarityPercent }}% match
          </Badge>
        </header>
        <div v-if="hasHistoricalTicket" class="side-by-side__body">
          <h4 v-if="historicalTicket?.title" class="side-by-side__body-title">
            {{ historicalTicket.title }}
          </h4>
          <p v-if="historicalTicket?.description" class="side-by-side__body-text">
            {{ historicalTicket.description }}
          </p>
          <p v-else-if="!historicalTicket?.title" class="side-by-side__empty-text">
            Ticket body unavailable.
          </p>
        </div>
        <div v-else class="side-by-side__empty">No historical ticket found.</div>
      </article>

      <article class="side-by-side__col" data-track-region="predicted_class_neighbor">
        <header class="side-by-side__col-header">
          <Search :size="12" class="side-by-side__col-icon" />
          <span class="side-by-side__col-label">Closest predicted class ticket</span>
          <Badge v-if="predictedClassTicket?.ref" variant="outline" class="side-by-side__col-badge">
            {{ predictedClassTicket.ref }}
          </Badge>
          <Badge
            v-if="predictedClassTicket?.label"
            variant="secondary"
            class="side-by-side__col-badge"
          >
            {{ predictedClassTicket.label }}
          </Badge>
          <Badge
            v-if="predictedClassSimilarityPercent !== null"
            :variant="similarityVariant(predictedClassSimilarityPercent)"
            class="side-by-side__col-badge"
          >
            {{ predictedClassSimilarityPercent }}% match
          </Badge>
        </header>
        <div v-if="hasPredictedClassTicket" class="side-by-side__body">
          <h4 v-if="predictedClassTicket?.title" class="side-by-side__body-title">
            {{ predictedClassTicket.title }}
          </h4>
          <p v-if="predictedClassTicket?.description" class="side-by-side__body-text">
            {{ predictedClassTicket.description }}
          </p>
          <p v-else-if="!predictedClassTicket?.title" class="side-by-side__empty-text">
            Ticket body unavailable.
          </p>
        </div>
        <div v-else class="side-by-side__empty">No predicted class ticket found.</div>
      </article>
    </div>
  </section>
</template>

<style scoped lang="scss">
.side-by-side {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);

  &__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--muted-foreground);
    font-size: 0.8125rem;
  }

  &__title {
    font-weight: 600;
    color: var(--foreground);
  }

  &__grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;

    @media (max-width: 900px) {
      grid-template-columns: 1fr;
    }
  }

  &__col {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 0;
    padding: 0.625rem;
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }

  &__col-header {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
  }

  &__col-icon {
    color: var(--muted-foreground);
  }

  &__col-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--muted-foreground);
  }

  &__col-badge {
    font-size: 0.6875rem;
  }

  &__body {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  &__body-title {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
    line-height: 1.4;
    color: var(--foreground);
  }

  &__body-text {
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--foreground);
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.375rem;
    padding: 1rem;
    color: var(--muted-foreground);
    font-size: 0.8125rem;
  }

  &__empty,
  &__empty-text {
    margin: 0;
    padding: 0.75rem;
    color: var(--muted-foreground);
    font-size: 0.8125rem;
    font-style: italic;
  }
}
</style>
