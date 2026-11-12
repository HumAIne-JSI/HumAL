<script setup lang="ts">
import { computed, useAttrs } from 'vue'

export type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info'

const props = withDefaults(defineProps<{
  variant?: BadgeVariant
  as?: string
}>(), {
  variant: 'default',
  as: 'span'
})

const classes = computed(() => [
  'badge',
  `badge--${props.variant}`
])
</script>

<template>
  <component
    :is="as"
    :class="classes"
    data-slot="badge"
  >
    <slot />
  </component>
</template>

<style>
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  border-radius: var(--radius);
  border: 1px solid transparent;
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium);
  line-height: 1.25;
  width: fit-content;
  white-space: nowrap;
  flex-shrink: 0;
  overflow: hidden;
  transition: color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
  outline: none;
}

.badge > :deep(svg) {
  width: 0.75rem;
  height: 0.75rem;
  pointer-events: none;
}

.badge:focus-visible {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring), 0.5);
}

/* Default variant */
.badge--default {
  background-color: var(--primary);
  color: var(--primary-foreground);
  border-color: transparent;
}

a.badge--default:hover,
button.badge--default:hover {
  background-color: var(--primary);
  opacity: 0.9;
}

/* Secondary variant */
.badge--secondary {
  background-color: var(--secondary);
  color: var(--secondary-foreground);
  border-color: transparent;
}

a.badge--secondary:hover,
button.badge--secondary:hover {
  background-color: var(--secondary);
  opacity: 0.9;
}

/* Destructive variant */
.badge--destructive {
  background-color: var(--destructive);
  color: white;
  border-color: transparent;
}

a.badge--destructive:hover,
button.badge--destructive:hover {
  background-color: var(--destructive);
  opacity: 0.9;
}

.badge--destructive:focus-visible {
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.2);
}

.dark .badge--destructive {
  background-color: rgba(var(--destructive), 0.6);
}

.dark .badge--destructive:focus-visible {
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.4);
}

/* Outline variant */
.badge--outline {
  background-color: transparent;
  color: var(--foreground);
  border-color: var(--border);
}

a.badge--outline:hover,
button.badge--outline:hover {
  background-color: var(--accent);
  color: var(--accent-foreground);
}

/* Success variant */
.badge--success {
  background-color: var(--success);
  color: var(--success-foreground);
  border-color: transparent;
}

a.badge--success:hover,
button.badge--success:hover {
  background-color: var(--success);
  opacity: 0.9;
}

.badge--success:focus-visible {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--success) 30%, transparent);
}

/* Warning variant */
.badge--warning {
  background-color: var(--warning);
  color: var(--warning-foreground);
  border-color: transparent;
}

a.badge--warning:hover,
button.badge--warning:hover {
  background-color: var(--warning);
  opacity: 0.9;
}

.badge--warning:focus-visible {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--warning) 30%, transparent);
}

/* Info variant */
.badge--info {
  background-color: var(--info);
  color: var(--info-foreground);
  border-color: transparent;
}

a.badge--info:hover,
button.badge--info:hover {
  background-color: var(--info);
  opacity: 0.9;
}

.badge--info:focus-visible {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--info) 30%, transparent);
  background-color: var(--accent);
  color: var(--accent-foreground);
}
</style>
