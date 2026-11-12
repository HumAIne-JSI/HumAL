<script setup lang="ts">
interface Props {
  currentPhase?: 'analyzing' | 'classifying' | 'generating' | 'retrieving'
}

const props = withDefaults(defineProps<Props>(), {
  currentPhase: 'analyzing',
})

const phases = [
  { id: 'analyzing', label: 'Analyzing' },
  { id: 'classifying', label: 'Classifying' },
  { id: 'generating', label: 'Generating' },
  { id: 'retrieving', label: 'Retrieving' },
]

const isPhaseActive = (phaseId: string) => phaseId === props.currentPhase
</script>

<template>
  <div class="loading-phase" role="status" :aria-label="`Loading phase: ${currentPhase}`">
    <div class="loading-phase__indicators">
      <div
        v-for="(phase, idx) in phases"
        :key="phase.id"
        class="loading-phase__step"
      >
        <div
          class="loading-phase__dot"
          :class="{ 'loading-phase__dot--active': isPhaseActive(phase.id) }"
        />
        <span v-if="idx < phases.length - 1" class="loading-phase__connector" />
      </div>
    </div>
    <div class="loading-phase__labels">
      <div
        v-for="phase in phases"
        :key="phase.id"
        class="loading-phase__label"
        :class="{ 'loading-phase__label--active': isPhaseActive(phase.id) }"
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
}

.loading-phase__step {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 0.5rem;
}

.loading-phase__dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background-color: var(--muted);
  flex-shrink: 0;
  transition: all 0.3s ease;

  &--active {
    background-color: var(--primary);
    width: 1rem;
    height: 1rem;
    animation: pulse 2s ease-in-out infinite;

    @media (prefers-reduced-motion: reduce) {
      animation: none;
    }
  }
}

.loading-phase__connector {
  flex: 1;
  height: 0.125rem;
  background-color: var(--muted);
  margin: 0 0.25rem;
}

.loading-phase__labels {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

.loading-phase__label {
  flex: 1;
  text-align: center;
  transition: color 0.3s ease;

  &--active {
    color: var(--primary);
    font-weight: 500;
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
</style>
