<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import { Sparkles } from 'lucide-vue-next'
import type { PerClassSimilarTicket } from '@/types/api'

interface Props {
  item: PerClassSimilarTicket
  rank: number
  probability?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  probability: null,
})

const similarityPercentage = computed(() =>
  Math.round(props.item.similarity_score * 100 * 10) / 10
)

const probabilityPercentage = computed(() => {
  if (props.probability == null) return null
  return Math.round(props.probability * 100 * 10) / 10
})

const similarityVariant = computed<'success' | 'info' | 'secondary'>(() => {
  if (props.item.similarity_score >= 0.8) return 'success'
  if (props.item.similarity_score >= 0.5) return 'info'
  return 'secondary'
})
</script>

<template>
  <article class="similar-by-class">
    <header class="similar-by-class__header">
      <div class="similar-by-class__rank">
        <span class="similar-by-class__rank-badge">#{{ rank }}</span>
        <Sparkles :size="14" />
      </div>
      <div class="similar-by-class__class">
        <Badge variant="secondary">{{ item.class_label }}</Badge>
        <span
          v-if="probabilityPercentage !== null"
          class="similar-by-class__probability"
          :title="'Model confidence for this class'"
        >
          {{ probabilityPercentage }}%
        </span>
      </div>
    </header>

    <h4 class="similar-by-class__title">{{ item.title }}</h4>

    <p class="similar-by-class__excerpt">{{ item.most_important_sentence }}</p>

    <footer class="similar-by-class__footer">
      <Badge variant="outline">{{ item.ticket_ref }}</Badge>
      <Badge :variant="similarityVariant">{{ similarityPercentage }}% similar</Badge>
    </footer>
  </article>
</template>

<style scoped lang="scss">
.similar-by-class {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background-color: var(--card);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;

  &:hover {
    border-color: var(--ring);
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.06);
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  &__rank {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    color: var(--muted-foreground);
    font-size: 0.75rem;
    font-weight: 600;

    svg {
      opacity: 0.8;
    }
  }

  &__rank-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.5rem;
    height: 1.25rem;
    padding: 0 0.375rem;
    border-radius: 0.5rem;
    background-color: var(--muted);
    color: var(--muted-foreground);
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  &__class {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__probability {
    font-size: 0.75rem;
    color: var(--muted-foreground);
    font-variant-numeric: tabular-nums;
  }

  &__title {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
    line-height: 1.35;
    color: var(--foreground);
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  &__excerpt {
    margin: 0;
    font-size: 0.8125rem;
    line-height: 1.45;
    color: var(--muted-foreground);
    font-style: italic;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }

  &__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-top: 0.125rem;
  }
}
</style>
