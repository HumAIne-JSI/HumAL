<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  lines?: number
  width?: string
  lastLineWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  lines: 3,
  width: '100%',
  lastLineWidth: '80%',
})

const lineWidths = computed(() => {
  const widths = Array(props.lines - 1).fill(props.width)
  widths.push(props.lastLineWidth)
  return widths
})
</script>

<template>
  <div class="skeleton-text" role="status" aria-label="Loading text content">
    <div
      v-for="(width, idx) in lineWidths"
      :key="idx"
      class="skeleton-text__line"
      :style="{ width }"
    />
  </div>
</template>

<style scoped lang="scss">
.skeleton-text {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  &__line {
    height: 1rem;
    background-color: var(--muted);
    border-radius: 0.25rem;
    animation: shimmer 2s infinite;

    @media (prefers-reduced-motion: reduce) {
      animation: none;
      opacity: 0.6;
    }
  }
}

@keyframes shimmer {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.7;
  }
}
</style>
