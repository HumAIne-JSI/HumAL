<script setup lang="ts">
import { computed } from 'vue'

export interface LoadingPhaseStep {
  id: string
  label: string
}

interface Props {
  currentPhase?: string
  phases?: LoadingPhaseStep[]
}

const props = withDefaults(defineProps<Props>(), {
  currentPhase: 'analyzing',
  phases: () => [
    { id: 'analyzing', label: 'Analyzing' },
    { id: 'classifying', label: 'Classifying' },
    { id: 'generating', label: 'Generating' },
    { id: 'retrieving', label: 'Retrieving' }
  ]
})

const activeIndex = computed(() =>
  props.phases.findIndex((phase) => phase.id === props.currentPhase)
)
const activeLabel = computed(() => props.phases[activeIndex.value]?.label ?? props.currentPhase)

const isPhaseActive = (index: number) => index === activeIndex.value
const isPhaseDone = (index: number) => index < activeIndex.value
</script>

<template>
  <div class="loading-phase" role="status" :aria-label="`In progress: ${activeLabel}`">
    <div class="loading-phase__indicators">
      <div v-for="(phase, idx) in phases" :key="phase.id" class="loading-phase__step">
        <div
          class="loading-phase__dot"
          :class="{
            'loading-phase__dot--active': isPhaseActive(idx),
            'loading-phase__dot--done': isPhaseDone(idx)
          }"
        />
        <span
          v-if="idx < phases.length - 1"
          class="loading-phase__connector"
          :class="{ 'loading-phase__connector--done': isPhaseDone(idx) }"
        />
      </div>
    </div>
    <div class="loading-phase__labels">
      <div
        v-for="(phase, idx) in phases"
        :key="phase.id"
        class="loading-phase__label"
        :class="{
          'loading-phase__label--active': isPhaseActive(idx),
          'loading-phase__label--done': isPhaseDone(idx)
        }"
      >
        {{ phase.label }}
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.loading-phase {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.loading-phase__indicators {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 0.5rem;
}

.loading-phase__step {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 0.5rem;
  min-width: 0;
}

.loading-phase__dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background-color: var(--muted);
  flex-shrink: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &--active {
    background-color: var(--primary);
    width: 1rem;
    height: 1rem;
    animation: pulse 2s ease-in-out infinite;

    @media (prefers-reduced-motion: reduce) {
      animation: none;
    }
  }

  &--done {
    background-color: var(--primary);
  }
}

.loading-phase__connector {
  flex: 1;
  height: 0.125rem;
  background-color: var(--muted);
  margin: 0 0.25rem;
  min-width: 0.5rem;
  transition: background-color 0.3s ease;

  &--done {
    background-color: var(--primary);
  }
}

.loading-phase__labels {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--muted-foreground);
  flex-wrap: wrap;
}

.loading-phase__label {
  flex: 1;
  text-align: center;
  transition: color 0.3s ease;
  min-width: 4rem;
  word-break: break-word;

  &--active {
    color: var(--primary);
    font-weight: 500;
  }

  &--done {
    color: var(--foreground);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@media (max-width: 768px) {
  .loading-phase__labels {
    font-size: 0.65rem;
  }

  .loading-phase__label {
    min-width: 3.5rem;
  }
}

@media (max-width: 480px) {
  .loading-phase__dot {
    width: 0.625rem;
    height: 0.625rem;

    &--active {
      width: 0.875rem;
      height: 0.875rem;
    }
  }

  .loading-phase__labels {
    font-size: 0.6rem;
    gap: 0.25rem;
  }

  .loading-phase__label {
    min-width: 3rem;
    font-size: 0.6rem;
  }

  .loading-phase__step {
    gap: 0.25rem;
  }

  .loading-phase__connector {
    min-width: 0.25rem;
    margin: 0 0.125rem;
  }
}
</style>
