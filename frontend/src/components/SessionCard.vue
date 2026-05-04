<script setup lang="ts">
import { computed } from 'vue';
import Card from '@/components/ui/Card.vue';
import Badge from '@/components/ui/Badge.vue';
import { Activity, Clock, Layers } from 'lucide-vue-next';
import type { BenchmarkSessionSummary } from '@/types/api';

const props = withDefaults(
  defineProps<{ session: BenchmarkSessionSummary; selected?: boolean }>(),
  { selected: false },
);

const emit = defineEmits<{
  (e: 'select', session: BenchmarkSessionSummary): void;
}>();

const startedDisplay = computed(() => {
  if (!props.session.started_at) return '—';
  return new Date(props.session.started_at * 1000).toLocaleString();
});

const statusVariant = computed(() => (props.session.is_active ? 'success' : 'secondary'));
const statusLabel = computed(() => (props.session.is_active ? 'active' : 'finalized'));
</script>

<template>
  <div :class="['session-card', { 'session-card--selected': selected }]" @click="emit('select', session)">
    <Card variant="default" padding="sm">
      <template #title>
        <div class="session-header">
          <span class="session-id">{{ session.sim_id }}</span>
          <Badge :variant="statusVariant" class="text-xs">{{ statusLabel }}</Badge>
        </div>
      </template>
      <template #description>
        <span v-if="session.instance_id" class="session-instance">instance #{{ session.instance_id }}</span>
      </template>

      <div class="session-metrics">
        <div class="metric">
          <div class="metric-label"><Activity class="w-3.5 h-3.5" /> Events</div>
          <div class="metric-value">{{ session.num_events }}</div>
        </div>
        <div class="metric">
          <div class="metric-label"><Layers class="w-3.5 h-3.5" /> Agents</div>
          <div class="metric-value">{{ session.agents_used.length }}</div>
        </div>
        <div class="metric">
          <div class="metric-label"><Clock class="w-3.5 h-3.5" /> Started</div>
          <div class="metric-value metric-value--small">{{ startedDisplay }}</div>
        </div>
      </div>
      <div class="session-agents">
        <Badge v-for="a in session.agents_used" :key="a" variant="outline" class="text-[10px]">{{ a }}</Badge>
      </div>
    </Card>
  </div>
</template>

<style scoped lang="scss">
.session-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  &:hover { transform: translateY(-1px); }
  &--selected :deep(.card) {
    border-color: var(--primary);
    box-shadow: 0 0 0 1px var(--primary);
  }
}
.session-header { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.session-id { font-family: monospace; font-size: 0.75rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px; }
.session-instance { font-size: 0.75rem; color: var(--muted-foreground); }
.session-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.metric { display: flex; flex-direction: column; gap: 0.125rem; min-width: 0; }
.metric-label { display: flex; align-items: center; gap: 0.25rem; font-size: 0.65rem; color: var(--muted-foreground); text-transform: uppercase; }
.metric-value { font-size: 1rem; font-weight: 600; }
.metric-value--small { font-size: 0.7rem; font-weight: 500; }
.session-agents { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.5rem; }
</style>
