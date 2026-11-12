<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  /** Diameter preset or explicit pixel value. */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number
  /** Semantic color of the spinning ring. */
  variant?: 'default' | 'primary' | 'muted' | 'current'
  /** Optional text shown next to (inline) or below (block) the spinner. */
  label?: string
  /** Center the spinner (and label) in a padded block for full-area loading. */
  block?: boolean
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  variant: 'default',
  label: '',
  block: false,
})

const SIZES: Record<string, number> = {
  xs: 12,
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48,
}

const dimension = computed<number>(() =>
  typeof props.size === 'number' ? props.size : SIZES[props.size] ?? 24,
)

const borderWidth = computed(() => Math.max(2, Math.round(dimension.value / 8)))

const ringStyle = computed(() => ({
  width: `${dimension.value}px`,
  height: `${dimension.value}px`,
  borderWidth: `${borderWidth.value}px`,
}))
</script>

<template>
  <div
    role="status"
    :aria-live="block ? 'polite' : undefined"
    :aria-label="label || 'Loading'"
    :class="[
      'spinner',
      `spinner--${variant}`,
      { 'spinner--block': block, 'spinner--inline': !block },
      props.class,
    ]"
  >
    <span class="spinner__ring" :style="ringStyle" />
    <span v-if="label" class="spinner__label">{{ label }}</span>
    <span v-else class="spinner__sr">Loading…</span>
  </div>
</template>

<style scoped lang="scss">
.spinner {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--muted-foreground);

  &--block {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 0.625rem;
    width: 100%;
    padding: 1.5rem;
    font-size: 0.875rem;
  }

  &--inline {
    font-size: 0.875rem;
  }

  &__ring {
    display: inline-block;
    box-sizing: border-box;
    border-style: solid;
    border-color: currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spinner-rotate 0.6s linear infinite;
    flex-shrink: 0;
  }

  &__label {
    color: var(--muted-foreground);
    line-height: 1.2;
  }

  // Visually hidden text for screen readers when no visible label is set.
  &__sr {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  // ==
  // Color variants
  // ==
  &--default .spinner__ring {
    color: var(--primary);
  }

  &--primary .spinner__ring {
    color: var(--primary);
  }

  &--muted .spinner__ring {
    color: var(--muted-foreground);
  }

  // `current` inherits the surrounding text color (e.g. inside a Button).
  &--current .spinner__ring {
    color: currentColor;
  }
}

@keyframes spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .spinner__ring {
    animation-duration: 1.5s;
  }
}
</style>
