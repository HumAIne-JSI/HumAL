<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  value?: number
  max?: number
  color?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  value: 0,
  max: 100,
  color: 'default',
})

const percentage = computed(() => {
  const val = Math.min(Math.max(props.value ?? 0, 0), props.max)
  return (val / props.max) * 100
})
</script>

<template>
  <div
    role="progressbar"
    :aria-valuenow="value"
    :aria-valuemin="0"
    :aria-valuemax="max"
    data-slot="progress"
    :class="['progress', `progress--${color}`, props.class]"
  >
    <div
      data-slot="progress-indicator"
      class="progress-indicator"
      :style="{ transform: `translateX(-${100 - percentage}%)` }"
    />
  </div>
</template>

<style scoped>
.progress {
  position: relative;
  height: 0.625rem;
  width: 100%;
  overflow: hidden;
  border-radius: 9999px;
  background-color: var(--muted);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.06);
}

.progress-indicator {
  height: 100%;
  width: 100%;
  flex: 1;
  background-color: var(--primary);
  background: linear-gradient(90deg, var(--primary), color-mix(in oklch, var(--primary) 90%, #fff));
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 9999px;
}

/* Color variants using semantic colors */
.progress--success {
  background-color: color-mix(in srgb, var(--success) 15%, transparent);
}
.progress--success .progress-indicator {
  background: linear-gradient(90deg, var(--success), color-mix(in oklch, var(--success) 90%, #fff));
}

.progress--warning {
  background-color: color-mix(in srgb, var(--warning) 15%, transparent);
}
.progress--warning .progress-indicator {
  background: linear-gradient(90deg, var(--warning), color-mix(in oklch, var(--warning) 90%, #fff));
}

.progress--danger {
  background-color: color-mix(in srgb, var(--destructive) 15%, transparent);
}
.progress--danger .progress-indicator {
  background: linear-gradient(90deg, var(--destructive), color-mix(in oklch, var(--destructive) 90%, #fff));
}

.progress--info {
  background-color: color-mix(in srgb, var(--info) 15%, transparent);
}
.progress--info .progress-indicator {
  background: linear-gradient(90deg, var(--info), color-mix(in oklch, var(--info) 90%, #fff));
}

@media (prefers-reduced-motion: reduce) {
  .progress-indicator {
    transition: none;
  }
}
</style>
