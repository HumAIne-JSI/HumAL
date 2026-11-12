<script setup lang="ts">
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'

export type ResolutionStage = 'intake' | 'review' | 'sent'
type StepState = 'done' | 'current' | 'upcoming'

const props = defineProps<{
  current: ResolutionStage
}>()

const STEPS: { id: ResolutionStage; label: string }[] = [
  { id: 'intake', label: 'Ticket' },
  { id: 'review', label: 'Review draft' },
  { id: 'sent', label: 'Send to team' }
]

const currentIndex = computed(() => STEPS.findIndex((step) => step.id === props.current))

function stepState(index: number): StepState {
  if (index < currentIndex.value || props.current === 'sent') return 'done'
  return index === currentIndex.value ? 'current' : 'upcoming'
}
</script>

<template>
  <ol class="steps" aria-label="Progress">
    <li
      v-for="(step, index) in STEPS"
      :key="step.id"
      class="steps__item"
      :class="`steps__item--${stepState(index)}`"
      :aria-current="index === currentIndex ? 'step' : undefined"
    >
      <span class="steps__marker" aria-hidden="true">
        <Check v-if="stepState(index) === 'done'" :size="12" :stroke-width="3" />
        <template v-else>{{ index + 1 }}</template>
      </span>
      <span class="steps__label">{{ step.label }}</span>
    </li>
  </ol>
</template>

<style scoped lang="scss">
.steps {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.steps__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: var(--muted-foreground);
  white-space: nowrap;

  &:not(:last-child)::after {
    content: '';
    width: 1.5rem;
    height: 1px;
    background: var(--border);
    transition: background-color 0.2s ease;
  }

  &--current {
    color: var(--foreground);
    font-weight: 600;
  }

  &--done {
    color: var(--foreground);

    &::after {
      background: var(--foreground);
    }
  }
}

.steps__marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.375rem;
  height: 1.375rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  font-size: 0.6875rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease;

  .steps__item--current &,
  .steps__item--done & {
    border-color: var(--primary);
    background: var(--primary);
    color: var(--primary-foreground);
  }
}

@media (max-width: 480px) {
  .steps__item:not(.steps__item--current) .steps__label {
    display: none;
  }

  .steps__item:not(:last-child)::after {
    width: 0.75rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .steps__item::after,
  .steps__marker {
    transition: none;
  }
}
</style>
