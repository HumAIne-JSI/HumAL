<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { ChevronDown, ChevronUp, History, Search } from 'lucide-vue-next'

export interface NeighborTicketView {
  title?: string
  description?: string
  bestSentence?: string
  ref?: string
  label?: string
  similarity?: number
}

interface Props {
  historicalTickets?: NeighborTicketView[]
  predictedClassTickets?: NeighborTicketView[]
  loadingSimilar?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  historicalTickets: () => [],
  predictedClassTickets: () => [],
  loadingSimilar: false,
})

const expandedKeys = ref<Set<string>>(new Set())

const ticketKeys = computed(() => [
  ...props.historicalTickets.map((ticket, index) => ticketKey('historical', ticket, index)),
  ...props.predictedClassTickets.map((ticket, index) =>
    ticketKey('predicted-class', ticket, index),
  ),
])

watch(ticketKeys, (keys) => {
  expandedKeys.value = new Set([...expandedKeys.value].filter((key) => keys.includes(key)))
})

function ticketKey(role: string, ticket: NeighborTicketView, index: number): string {
  return `${role}:${ticket.ref ?? index}`
}

function isExpanded(key: string): boolean {
  return expandedKeys.value.has(key)
}

function toggleExpanded(key: string): void {
  const next = new Set(expandedKeys.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  expandedKeys.value = next
}

function handleCardKeydown(event: KeyboardEvent, key: string): void {
  if (event.key !== 'Enter' && event.key !== ' ') return
  event.preventDefault()
  toggleExpanded(key)
}

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

function firstSentence(text?: string): string | undefined {
  const normalized = text?.trim()
  if (!normalized) return undefined
  const match = normalized.match(/^.*?[.!?](?:\s|$)/)
  return (match?.[0] ?? normalized).trim()
}

function bestSentence(ticket: NeighborTicketView): string {
  return (
    ticket.bestSentence?.trim() || firstSentence(ticket.description) || 'Best sentence unavailable.'
  )
}

function hasTicketBody(ticket: NeighborTicketView): boolean {
  return Boolean(ticket.description?.trim())
}

const hasHistoricalTickets = computed(() => props.historicalTickets.length > 0)
const hasPredictedClassTickets = computed(() => props.predictedClassTickets.length > 0)
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
          <span class="side-by-side__col-label">Closest past tickets</span>
        </header>

        <div v-if="hasHistoricalTickets" class="side-by-side__cards">
          <article
            v-for="(ticket, index) in historicalTickets"
            :key="ticketKey('historical', ticket, index)"
            class="side-by-side__card"
            :class="{
              'side-by-side__card--expanded': isExpanded(ticketKey('historical', ticket, index)),
            }"
            role="button"
            tabindex="0"
            :aria-expanded="isExpanded(ticketKey('historical', ticket, index))"
            :aria-label="`${isExpanded(ticketKey('historical', ticket, index)) ? 'Collapse' : 'Expand'} historical ticket ${ticket.ref ?? index + 1}`"
            @click="toggleExpanded(ticketKey('historical', ticket, index))"
            @keydown="handleCardKeydown($event, ticketKey('historical', ticket, index))"
          >
            <header class="side-by-side__card-header">
              <span class="side-by-side__rank">#{{ index + 1 }}</span>
              <h4 class="side-by-side__card-title">{{ ticket.title || 'Untitled ticket' }}</h4>
              <ChevronUp v-if="isExpanded(ticketKey('historical', ticket, index))" :size="15" />
              <ChevronDown v-else :size="15" />
            </header>
            <div class="side-by-side__card-meta">
              <Badge v-if="ticket.ref" variant="outline" class="side-by-side__col-badge">
                {{ ticket.ref }}
              </Badge>
              <Badge v-if="ticket.label" variant="secondary" class="side-by-side__col-badge">
                {{ ticket.label }}
              </Badge>
              <Badge
                v-if="formatSimilarity(ticket.similarity) !== null"
                :variant="similarityVariant(formatSimilarity(ticket.similarity))"
                class="side-by-side__col-badge"
              >
                {{ formatSimilarity(ticket.similarity) }}% match
              </Badge>
            </div>
            <p class="side-by-side__best-sentence">{{ bestSentence(ticket) }}</p>
            <div
              v-if="isExpanded(ticketKey('historical', ticket, index))"
              class="side-by-side__full-body"
            >
              <p v-if="hasTicketBody(ticket)" class="side-by-side__body-text">
                {{ ticket.description }}
              </p>
              <p v-else class="side-by-side__empty-text">Full ticket body unavailable.</p>
            </div>
          </article>
        </div>
        <div v-else class="side-by-side__empty">No historical tickets found.</div>
      </article>

      <article class="side-by-side__col" data-track-region="predicted_class_neighbor">
        <header class="side-by-side__col-header">
          <Search :size="12" class="side-by-side__col-icon" />
          <span class="side-by-side__col-label">Closest predicted class tickets</span>
        </header>

        <div v-if="hasPredictedClassTickets" class="side-by-side__cards">
          <article
            v-for="(ticket, index) in predictedClassTickets"
            :key="ticketKey('predicted-class', ticket, index)"
            class="side-by-side__card"
            :class="{
              'side-by-side__card--expanded': isExpanded(
                ticketKey('predicted-class', ticket, index),
              ),
            }"
            role="button"
            tabindex="0"
            :aria-expanded="isExpanded(ticketKey('predicted-class', ticket, index))"
            :aria-label="`${isExpanded(ticketKey('predicted-class', ticket, index)) ? 'Collapse' : 'Expand'} predicted class ticket ${ticket.ref ?? index + 1}`"
            @click="toggleExpanded(ticketKey('predicted-class', ticket, index))"
            @keydown="handleCardKeydown($event, ticketKey('predicted-class', ticket, index))"
          >
            <header class="side-by-side__card-header">
              <span class="side-by-side__rank">#{{ index + 1 }}</span>
              <h4 class="side-by-side__card-title">{{ ticket.title || 'Untitled ticket' }}</h4>
              <ChevronUp
                v-if="isExpanded(ticketKey('predicted-class', ticket, index))"
                :size="15"
              />
              <ChevronDown v-else :size="15" />
            </header>
            <div class="side-by-side__card-meta">
              <Badge v-if="ticket.ref" variant="outline" class="side-by-side__col-badge">
                {{ ticket.ref }}
              </Badge>
              <Badge v-if="ticket.label" variant="secondary" class="side-by-side__col-badge">
                {{ ticket.label }}
              </Badge>
              <Badge
                v-if="formatSimilarity(ticket.similarity) !== null"
                :variant="similarityVariant(formatSimilarity(ticket.similarity))"
                class="side-by-side__col-badge"
              >
                {{ formatSimilarity(ticket.similarity) }}% match
              </Badge>
            </div>
            <p class="side-by-side__best-sentence">{{ bestSentence(ticket) }}</p>
            <div
              v-if="isExpanded(ticketKey('predicted-class', ticket, index))"
              class="side-by-side__full-body"
            >
              <p v-if="hasTicketBody(ticket)" class="side-by-side__body-text">
                {{ ticket.description }}
              </p>
              <p v-else class="side-by-side__empty-text">Full ticket body unavailable.</p>
            </div>
          </article>
        </div>
        <div v-else class="side-by-side__empty">No predicted class tickets found.</div>
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

  &__cards {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__card {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.625rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: pointer;
    transition:
      border-color 0.15s ease,
      box-shadow 0.15s ease;

    &:hover,
    &:focus-visible,
    &--expanded {
      border-color: var(--ring);
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.06);
    }

    &:focus-visible {
      outline: 2px solid var(--ring, var(--primary));
      outline-offset: 2px;
    }
  }

  &__card-header {
    display: flex;
    align-items: flex-start;
    gap: 0.375rem;
    color: var(--muted-foreground);

    svg {
      flex-shrink: 0;
      margin-top: 0.125rem;
    }
  }

  &__rank {
    flex-shrink: 0;
    min-width: 1.375rem;
    padding: 0.125rem 0.25rem;
    border-radius: 0.375rem;
    background: var(--muted);
    color: var(--muted-foreground);
    font-size: 0.6875rem;
    font-weight: 700;
    text-align: center;
  }

  &__card-title {
    flex: 1;
    min-width: 0;
    margin: 0;
    color: var(--foreground);
    font-size: 0.875rem;
    font-weight: 600;
    line-height: 1.35;
  }

  &__card-meta {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
  }

  &__col-badge {
    font-size: 0.6875rem;
  }

  &__best-sentence {
    margin: 0;
    color: var(--muted-foreground);
    font-size: 0.8125rem;
    line-height: 1.45;
    font-style: italic;
  }

  &__full-body {
    padding-top: 0.5rem;
    border-top: 1px solid var(--border);
  }

  &__body-text {
    margin: 0;
    color: var(--foreground);
    font-size: 0.875rem;
    line-height: 1.6;
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
