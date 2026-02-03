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
  height: 0.5rem;
  width: 100%;
  overflow: hidden;
  border-radius: 9999px;
  background-color: color-mix(in srgb, var(--primary) 20%, transparent);
}

.progress-indicator {
  height: 100%;
  width: 100%;
  flex: 1;
  background-color: var(--primary);
  transition: all 0.2s ease-out;
}

/* Color variants using semantic colors */
.progress--success {
  background-color: color-mix(in srgb, var(--success) 20%, transparent);
}
.progress--success .progress-indicator {
  background-color: var(--success);
}

.progress--warning {
  background-color: color-mix(in srgb, var(--warning) 20%, transparent);
}
.progress--warning .progress-indicator {
  background-color: var(--warning);
}

.progress--danger {
  background-color: color-mix(in srgb, var(--destructive) 20%, transparent);
}
.progress--danger .progress-indicator {
  background-color: var(--destructive);
}

.progress--info {
  background-color: color-mix(in srgb, var(--info) 20%, transparent);
}
.progress--info .progress-indicator {
  background-color: var(--info);
}
</style>
