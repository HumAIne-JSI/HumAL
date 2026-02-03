<script setup lang="ts">
import { computed } from 'vue'

export interface ButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link' | 'success' | 'warning' | 'info'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  disabled?: boolean
  asChild?: boolean
}

const props = withDefaults(defineProps<ButtonProps>(), {
  variant: 'default',
  size: 'default',
  disabled: false,
  asChild: false,
})

const classes = computed(() => [
  'btn',
  `btn-v-${props.variant}`,
  `btn-s-${props.size}`,
])
</script>

<template>
  <component
    :is="asChild ? 'slot' : 'button'"
    :class="classes"
    :disabled="disabled"
    data-slot="button"
  >
    <slot />
  </component>
</template>

<style scoped lang="scss">
.btn {
  // Base styles
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  white-space: nowrap;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: var(--font-weight-medium);
  transition: background-color 0.15s ease, opacity 0.15s ease, color 0.15s ease;
  outline: none;
  flex-shrink: 0;
  cursor: pointer;
  border: none;

  // Disabled state
  &:disabled {
    pointer-events: none;
    opacity: 0.5;
  }

  // SVG icon styles
  :deep(svg) {
    pointer-events: none;
    flex-shrink: 0;

    &:not([class*='size-']) {
      width: 1rem;
      height: 1rem;
    }
  }

  // Focus visible state
  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 2px;
  }

  // ============================================
  // Variants (btn-v-*)
  // ============================================
  &-v-default {
    background-color: var(--primary);
    color: var(--primary-foreground);

    &:hover:not(:disabled) {
      filter: brightness(1.1);
    }
  }

  &-v-destructive {
    background-color: var(--destructive);
    color: var(--destructive-foreground);

    &:hover:not(:disabled) {
      filter: brightness(1.1);
    }
  }

  &-v-outline {
    border: 1px solid var(--border);
    background-color: transparent;
    color: var(--foreground);

    &:hover:not(:disabled) {
      background-color: var(--accent);
      color: var(--accent-foreground);
    }
  }

  &-v-secondary {
    background-color: var(--secondary);
    color: var(--secondary-foreground);

    &:hover:not(:disabled) {
      background-color: color-mix(in oklch, var(--secondary) 85%, black);
    }
  }

  &-v-ghost {
    background-color: transparent;
    color: var(--foreground);

    &:hover:not(:disabled) {
      background-color: var(--accent);
      color: var(--accent-foreground);
    }
  }

  &-v-link {
    background-color: transparent;
    color: var(--primary);
    text-decoration: none;
    text-underline-offset: 4px;

    &:hover:not(:disabled) {
      text-decoration: underline;
    }
  }

  &-v-success {
    background-color: var(--success);
    color: var(--success-foreground);

    &:hover:not(:disabled) {
      filter: brightness(1.1);
    }
  }

  &-v-warning {
    background-color: var(--warning);
    color: var(--warning-foreground);

    &:hover:not(:disabled) {
      filter: brightness(1.1);
    }
  }

  &-v-info {
    background-color: var(--info);
    color: var(--info-foreground);

    &:hover:not(:disabled) {
      filter: brightness(1.1);
    }
  }

  // ============================================
  // Sizes (btn-s-*)
  // ============================================
  &-s-default {
    height: 2.25rem;
    padding: 0.5rem 1rem;
  }

  &-s-sm {
    height: 2rem;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.8125rem;
  }

  &-s-lg {
    height: 2.5rem;
    padding: 0.5rem 1.5rem;
  }

  &-s-icon {
    width: 2.25rem;
    height: 2.25rem;
    padding: 0;
  }
}
</style>
