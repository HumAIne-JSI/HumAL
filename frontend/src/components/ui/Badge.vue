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
  gap: 0.375rem;
  border-radius: calc(var(--radius) - 2px);
  border: 1px solid transparent;
  padding: 0.25rem 0.625rem;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1.2;
  width: fit-content;
  white-space: nowrap;
  flex-shrink: 0;
  overflow: hidden;
  transition: color 0.15s ease, background-color 0.15s ease, box-shadow 0.2s ease;
  outline: none;
}

.badge > :deep(svg) {
  width: 0.8rem;
  height: 0.8rem;
  pointer-events: none;
}

.badge:focus-visible {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring), 0.1);
}

/* Default variant */
.badge--default {
  background-color: var(--primary);
  color: var(--primary-foreground);
  border-color: transparent;
}

a.badge--default:hover,
button.badge--default:hover {
  background-color: color-mix(in oklch, var(--primary) 90%, black);
}

/* Secondary variant */
.badge--secondary {
  background-color: var(--secondary);
  color: var(--secondary-foreground);
  border-color: transparent;
}

a.badge--secondary:hover,
button.badge--secondary:hover {
  background-color: color-mix(in oklch, var(--secondary) 85%, black);
}

/* Destructive variant */
.badge--destructive {
  background-color: var(--destructive-muted);
  color: var(--destructive-muted-foreground);
  border-color: transparent;
}

a.badge--destructive:hover,
button.badge--destructive:hover {
  background-color: color-mix(in oklch, var(--destructive-muted) 85%, black);
}

.badge--destructive:focus-visible {
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.1);
}

.dark .badge--destructive {
  background-color: color-mix(in srgb, var(--destructive-muted) 80%, var(--foreground));
}

.dark .badge--destructive:focus-visible {
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.2);
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
  border-color: transparent;
}

/* Success variant */
.badge--success {
  background-color: var(--success-muted);
  color: var(--success-muted-foreground);
  border-color: transparent;
}

a.badge--success:hover,
button.badge--success:hover {
  background-color: color-mix(in oklch, var(--success-muted) 80%, black);
}

.badge--success:focus-visible {
  box-shadow: 0 0 0 3px rgba(var(--success), 0.1);
}

/* Warning variant */
.badge--warning {
  background-color: var(--warning-muted);
  color: var(--warning-muted-foreground);
  border-color: transparent;
}

a.badge--warning:hover,
button.badge--warning:hover {
  background-color: color-mix(in oklch, var(--warning-muted) 80%, black);
}

.badge--warning:focus-visible {
  box-shadow: 0 0 0 3px rgba(var(--warning), 0.1);
}

/* Info variant */
.badge--info {
  background-color: var(--info-muted);
  color: var(--info-muted-foreground);
  border-color: transparent;
}

a.badge--info:hover,
button.badge--info:hover {
  background-color: color-mix(in oklch, var(--info-muted) 80%, black);
}

.badge--info:focus-visible {
  box-shadow: 0 0 0 3px rgba(var(--info), 0.1);
}
</style>
