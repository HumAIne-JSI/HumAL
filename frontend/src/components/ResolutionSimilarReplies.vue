<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { ArrowUpLeft, Check, ThumbsDown, ThumbsUp } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import type { ResolutionFeedbackStatsResponse, ResolutionSimilarReply } from '@/types/api'

type VoteLabel = 0 | 1

const LONG_REPLY_CHARS = 240
const MAX_STAGGER_ITEMS = 5
const STAGGER_MS = 40

const props = defineProps<{
  replies: ResolutionSimilarReply[]
  loading: boolean
  disabled: boolean
  votes: Record<string, VoteLabel>
  pendingVotes: Record<string, VoteLabel>
  stats: Record<string, ResolutionFeedbackStatsResponse>
  appliedId: string | null
}>()

const emit = defineEmits<{
  'use-reply': [reply: ResolutionSimilarReply]
  vote: [reply: ResolutionSimilarReply, label: VoteLabel]
}>()

const uid = useId()
const headingId = `${uid}-heading`
const expanded = ref<Record<string, boolean>>({})

const matchPct = (reply: ResolutionSimilarReply) => Math.round((reply.enhanced_score ?? 0) * 100)
const isLong = (reply: ResolutionSimilarReply) => reply.first_reply.length > LONG_REPLY_CHARS
const isApplied = (reply: ResolutionSimilarReply) => props.appliedId === reply.retrieved_id
const isPending = (id: string, label: VoteLabel) => props.pendingVotes[id] === label
const staggerStyle = (index: number) => ({
  '--stagger': `${Math.min(index, MAX_STAGGER_ITEMS) * STAGGER_MS}ms`
})

const statsById = computed(() => {
  const totals: Record<string, { up: number; down: number }> = {}
  for (const [id, entry] of Object.entries(props.stats)) {
    totals[id] = entry.agg.reduce(
      (sum, [, up, down]) => ({ up: sum.up + up, down: sum.down + down }),
      { up: 0, down: 0 }
    )
  }
  return totals
})

function statsLabel(id: string): string {
  const totals = statsById.value[id]
  return totals ? `${totals.up} helpful, ${totals.down} not helpful` : ''
}

function toggleExpanded(id: string): void {
  expanded.value[id] = !expanded.value[id]
}
</script>

<template>
  <section class="evidence" :aria-labelledby="headingId">
    <header class="evidence__header">
      <h3 :id="headingId" class="evidence__heading">
        Similar past replies
        <span v-if="!loading" class="evidence__count">{{ replies.length }}</span>
      </h3>
      <p class="evidence__lede">
        The draft builds on these. Rate them to improve future suggestions.
      </p>
    </header>

    <div v-if="loading" class="evidence__list" aria-hidden="true">
      <SkeletonCard v-for="i in 3" :key="i" :title="false" description :lines="3" />
    </div>

    <p v-else-if="!replies.length" class="evidence__empty">
      No similar past tickets were found, so the draft is based on this ticket alone.
    </p>

    <ul v-else class="evidence__list">
      <li
        v-for="(reply, index) in replies"
        :key="reply.retrieved_id"
        class="reply"
        :class="{ 'reply--applied': isApplied(reply) }"
        :style="staggerStyle(index)"
      >
        <div class="reply__meta">
          <span class="reply__match">{{ matchPct(reply) }}% match</span>
          <span class="reply__id">{{ reply.retrieved_id }}</span>
          <span
            v-if="statsById[reply.retrieved_id]"
            class="reply__stats"
            :title="statsLabel(reply.retrieved_id)"
          >
            <ThumbsUp :size="12" aria-hidden="true" />
            {{ statsById[reply.retrieved_id]!.up }}
            <ThumbsDown :size="12" aria-hidden="true" />
            {{ statsById[reply.retrieved_id]!.down }}
          </span>
        </div>

        <h4 class="reply__title">{{ reply.Title_anon || 'Untitled ticket' }}</h4>
        <p v-if="reply.Description_anon" class="reply__desc">{{ reply.Description_anon }}</p>

        <template v-if="reply.first_reply">
          <blockquote
            :id="`${uid}-quote-${index}`"
            class="reply__quote"
            :class="{ 'reply__quote--clamped': isLong(reply) && !expanded[reply.retrieved_id] }"
          >
            {{ reply.first_reply }}
          </blockquote>
          <button
            v-if="isLong(reply)"
            type="button"
            class="reply__more"
            :aria-expanded="!!expanded[reply.retrieved_id]"
            :aria-controls="`${uid}-quote-${index}`"
            @click="toggleExpanded(reply.retrieved_id)"
          >
            {{ expanded[reply.retrieved_id] ? 'Show less' : 'Show more' }}
          </button>
        </template>

        <div class="reply__actions">
          <Button
            v-if="reply.first_reply"
            :variant="isApplied(reply) ? 'secondary' : 'outline'"
            size="sm"
            type="button"
            :disabled="disabled || isApplied(reply)"
            @click="emit('use-reply', reply)"
          >
            <Check v-if="isApplied(reply)" :size="14" />
            <ArrowUpLeft v-else :size="14" />
            {{ isApplied(reply) ? 'In draft' : 'Use in draft' }}
          </Button>
          <div class="reply__vote" role="group" :aria-label="`Rate reply ${reply.retrieved_id}`">
            <Button
              :variant="votes[reply.retrieved_id] === 1 ? 'default' : 'ghost'"
              size="icon"
              type="button"
              aria-label="Helpful"
              :aria-pressed="votes[reply.retrieved_id] === 1"
              :loading="isPending(reply.retrieved_id, 1)"
              :disabled="reply.retrieved_id in pendingVotes"
              @click="emit('vote', reply, 1)"
            >
              <ThumbsUp :size="14" />
            </Button>
            <Button
              :variant="votes[reply.retrieved_id] === 0 ? 'default' : 'ghost'"
              size="icon"
              type="button"
              aria-label="Not helpful"
              :aria-pressed="votes[reply.retrieved_id] === 0"
              :loading="isPending(reply.retrieved_id, 0)"
              :disabled="reply.retrieved_id in pendingVotes"
              @click="emit('vote', reply, 0)"
            >
              <ThumbsDown :size="14" />
            </Button>
          </div>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped lang="scss">
.evidence {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.evidence__heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.evidence__count {
  min-width: 1.375rem;
  padding: 0 0.375rem;
  border-radius: 999px;
  background: var(--muted);
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
  text-align: center;
}

.evidence__lede {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: var(--muted-foreground);
}

.evidence__empty {
  margin: 0;
  padding: 1rem;
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.evidence__list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.reply {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
  transition: border-color 0.15s ease;
  animation: reply-in 0.24s ease-out both;
  animation-delay: var(--stagger, 0ms);

  &--applied {
    border-color: var(--primary);
    box-shadow: inset 3px 0 0 var(--primary);
  }
}

@keyframes reply-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
}

.reply__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.reply__match {
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  background: var(--primary);
  color: var(--primary-foreground);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.reply__id {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--muted-foreground);
}

.reply__stats {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-left: auto;
  color: var(--muted-foreground);
  font-variant-numeric: tabular-nums;
}

.reply__title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.35;
}

.reply__desc {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  font-size: 0.8125rem;
  color: var(--muted-foreground);
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.reply__quote {
  margin: 0.25rem 0 0;
  padding: 0.625rem 0.75rem;
  border-left: 2px solid var(--foreground);
  background: var(--muted);
  border-radius: 0 calc(var(--radius) - 2px) calc(var(--radius) - 2px) 0;
  font-size: 0.875rem;
  line-height: 1.55;
  white-space: pre-line;

  &--clamped {
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
  }
}

.reply__more {
  align-self: flex-start;
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted-foreground);
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;

  &:hover {
    color: var(--foreground);
  }

  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 2px;
    border-radius: 2px;
  }
}

.reply__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.reply__vote {
  display: flex;
  gap: 0.25rem;
}

@media (prefers-reduced-motion: reduce) {
  .reply {
    animation: none;
    transition: none;
  }
}
</style>
