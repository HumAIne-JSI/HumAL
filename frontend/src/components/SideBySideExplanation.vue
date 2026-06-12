<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'
import { Search, Sparkles } from 'lucide-vue-next'
import type { ExplainLimeResponse } from '@/types/api'

export interface SideBySideTicket {
  title?: string
  description?: string
}

export interface SideBySideSimilarTicket extends SideBySideTicket {
  ref?: string
  label?: string
  similarity?: number
}

export interface SideBySideExplanationProps {
  currentTicket: SideBySideTicket
  similarTicket?: SideBySideSimilarTicket | null
  lime?: ExplainLimeResponse | null
  loadingLime?: boolean
  loadingSimilar?: boolean
}

const props = withDefaults(defineProps<SideBySideExplanationProps>(), {
  similarTicket: null,
  lime: null,
  loadingLime: false,
  loadingSimilar: false,
})

interface Token {
  kind: 'word' | 'gap'
  text: string
  weight?: number
}

const wordWeights = computed(() => {
  const map = new Map<string, number>()
  const item = props.lime?.[0]
  if (!item || !item.top_words) return map
  for (const [word, weight] of item.top_words) {
    if (!word) continue
    const key = word.toLowerCase()
    const existing = map.get(key)
    if (existing === undefined || Math.abs(weight) > Math.abs(existing)) {
      map.set(key, weight)
    }
  }
  return map
})

const maxAbsWeight = computed(() => {
  let max = 0
  for (const w of wordWeights.value.values()) {
    if (Math.abs(w) > max) max = Math.abs(w)
  }
  return max || 1
})

function tokenize(text: string): Token[] {
  if (!text) return []
  const tokens: Token[] = []
  const regex = /([A-Za-z0-9]+(?:'[A-Za-z0-9]+)?)/g
  let last = 0
  let match: RegExpExecArray | null
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) {
      tokens.push({ kind: 'gap', text: text.slice(last, match.index) })
    }
    const word = match[0]
    const weight = wordWeights.value.get(word.toLowerCase())
    tokens.push({ kind: 'word', text: word, weight })
    last = match.index + word.length
  }
  if (last < text.length) {
    tokens.push({ kind: 'gap', text: text.slice(last) })
  }
  return tokens
}

function highlightStyle(weight: number): string {
  const intensity = Math.min(1, Math.abs(weight) / maxAbsWeight.value)
  const pct = (10 + intensity * 50).toFixed(1)
  const color = weight >= 0 ? 'var(--primary)' : 'var(--destructive)'
  return `background-color: color-mix(in srgb, ${color} ${pct}%, transparent); border-bottom: 2px solid ${color};`
}

function tokenTitle(token: Token): string {
  if (token.kind !== 'word' || token.weight === undefined) return ''
  return `${token.text}: ${token.weight >= 0 ? '+' : ''}${token.weight.toFixed(3)}`
}

const currentTitleTokens = computed(() => tokenize(props.currentTicket.title ?? ''))
const currentBodyTokens = computed(() => tokenize(props.currentTicket.description ?? ''))
const similarTitleTokens = computed(() => tokenize(props.similarTicket?.title ?? ''))
const similarBodyTokens = computed(() => tokenize(props.similarTicket?.description ?? ''))

const similarityPercent = computed(() => {
  const sim = props.similarTicket?.similarity
  if (sim === undefined || sim === null) return null
  return Math.round(sim * 100)
})

const similarityVariant = computed(() => {
  const pct = similarityPercent.value
  if (pct === null) return 'secondary'
  if (pct >= 80) return 'success'
  if (pct >= 50) return 'info'
  return 'secondary'
})

const hasLime = computed(() => wordWeights.value.size > 0)
const hasSimilar = computed(
  () => props.similarTicket !== null && (props.similarTicket?.ref || props.similarTicket?.description),
)
</script>

<template>
  <section class="side-by-side" data-track-region="lime_panel">
    <header class="side-by-side__header">
      <Sparkles :size="14" />
      <span class="side-by-side__title">Why this prediction</span>
      <span v-if="hasLime" class="side-by-side__legend">
        <span class="side-by-side__legend-item">
          <span class="side-by-side__legend-swatch side-by-side__legend-swatch--pos"></span>
          supports
        </span>
        <span class="side-by-side__legend-item">
          <span class="side-by-side__legend-swatch side-by-side__legend-swatch--neg"></span>
          opposes
        </span>
      </span>
    </header>

    <div class="side-by-side__grid">
      <!-- Current Ticket Column -->
      <article class="side-by-side__col">
        <header class="side-by-side__col-header">
          <span class="side-by-side__col-label">Current ticket</span>
        </header>
        <div v-if="loadingLime" class="side-by-side__loading">
          <Progress :value="undefined" />
          <span>Computing word importance...</span>
        </div>
        <div v-else class="side-by-side__body">
          <h4 v-if="currentTicket.title" class="side-by-side__body-title">
            <template v-for="(token, idx) in currentTitleTokens" :key="`ct-${idx}`">
              <mark
                v-if="token.kind === 'word' && token.weight !== undefined"
                :style="highlightStyle(token.weight)"
                :title="tokenTitle(token)"
              >{{ token.text }}</mark>
              <template v-else>{{ token.text }}</template>
            </template>
          </h4>
          <p v-if="currentTicket.description" class="side-by-side__body-text">
            <template v-for="(token, idx) in currentBodyTokens" :key="`cb-${idx}`">
              <mark
                v-if="token.kind === 'word' && token.weight !== undefined"
                :style="highlightStyle(token.weight)"
                :title="tokenTitle(token)"
              >{{ token.text }}</mark>
              <template v-else>{{ token.text }}</template>
            </template>
          </p>
          <p v-else-if="!currentTicket.title" class="side-by-side__empty-text">
            No ticket text available.
          </p>
        </div>
      </article>

      <!-- Similar Ticket Column -->
      <article class="side-by-side__col" data-track-region="nearest_ticket">
        <header class="side-by-side__col-header">
          <Search :size="12" class="side-by-side__col-icon" />
          <span class="side-by-side__col-label">Most similar labeled ticket</span>
          <Badge v-if="similarTicket?.ref" variant="outline" class="side-by-side__col-badge">
            {{ similarTicket.ref }}
          </Badge>
          <Badge v-if="similarTicket?.label" variant="secondary" class="side-by-side__col-badge">
            {{ similarTicket.label }}
          </Badge>
          <Badge
            v-if="similarityPercent !== null"
            :variant="similarityVariant"
            class="side-by-side__col-badge"
          >
            {{ similarityPercent }}% similar
          </Badge>
        </header>
        <div v-if="loadingSimilar" class="side-by-side__loading">
          <Progress :value="undefined" />
          <span>Finding similar ticket...</span>
        </div>
        <div v-else-if="hasSimilar" class="side-by-side__body">
          <h4 v-if="similarTicket?.title" class="side-by-side__body-title">
            <template v-for="(token, idx) in similarTitleTokens" :key="`st-${idx}`">
              <mark
                v-if="token.kind === 'word' && token.weight !== undefined"
                :style="highlightStyle(token.weight)"
                :title="tokenTitle(token)"
              >{{ token.text }}</mark>
              <template v-else>{{ token.text }}</template>
            </template>
          </h4>
          <p v-if="similarTicket?.description" class="side-by-side__body-text">
            <template v-for="(token, idx) in similarBodyTokens" :key="`sb-${idx}`">
              <mark
                v-if="token.kind === 'word' && token.weight !== undefined"
                :style="highlightStyle(token.weight)"
                :title="tokenTitle(token)"
              >{{ token.text }}</mark>
              <template v-else>{{ token.text }}</template>
            </template>
          </p>
          <p v-else-if="!similarTicket?.title" class="side-by-side__empty-text">
            Ticket body unavailable.
          </p>
        </div>
        <div v-else class="side-by-side__empty">
          No similar labeled ticket found.
        </div>
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

  &__legend {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.75rem;
  }

  &__legend-item {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
  }

  &__legend-swatch {
    width: 0.625rem;
    height: 0.625rem;
    border-radius: 2px;

    &--pos {
      background: color-mix(in srgb, var(--primary) 45%, transparent);
      border-bottom: 2px solid var(--primary);
    }

    &--neg {
      background: color-mix(in srgb, var(--destructive) 45%, transparent);
      border-bottom: 2px solid var(--destructive);
    }
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
    padding: 0.625rem;
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    min-width: 0;
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

    mark {
      background: transparent;
      color: inherit;
      padding: 0 1px;
      border-radius: 2px;
    }
  }

  &__body-text {
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--foreground);
    white-space: pre-wrap;
    word-wrap: break-word;

    mark {
      background: transparent;
      color: inherit;
      padding: 0 1px;
      border-radius: 2px;
      cursor: help;
    }
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

  &__empty {
    padding: 0.75rem;
    font-size: 0.8125rem;
    color: var(--muted-foreground);
    font-style: italic;
  }

  &__empty-text {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--muted-foreground);
    font-style: italic;
  }
}
</style>
