<script setup lang="ts">
/**
 * Script timeline: per-agent swimlanes of timestamped events.
 * Each event chip is clickable; emits `select` with the entry.
 */
import { computed } from 'vue';
import type { AgentId, ScriptEntry } from '@/types/api';

const props = withDefaults(
  defineProps<{
    entries: ScriptEntry[];
    agentFilter?: AgentId | null;
    selectedIndex?: number | null;
  }>(),
  { agentFilter: null, selectedIndex: null },
);

const emit = defineEmits<{ (e: 'select', entry: ScriptEntry, index: number): void }>();

const AGENT_ORDER: AgentId[] = ['ORCH', 'AL', 'LAB', 'MOD', 'XAI'];

const filtered = computed(() =>
  props.agentFilter ? props.entries.filter((e) => e.agent === props.agentFilter) : props.entries,
);

const tMax = computed(() => {
  const max = filtered.value.reduce((m, e) => Math.max(m, e.t), 0);
  return Math.max(max, 1);
});

interface Lane {
  agent: AgentId;
  events: { entry: ScriptEntry; index: number }[];
}

const lanes = computed<Lane[]>(() => {
  const visibleAgents = props.agentFilter ? [props.agentFilter] : AGENT_ORDER;
  return visibleAgents.map((agent) => ({
    agent,
    events: props.entries
      .map((entry, index) => ({ entry, index }))
      .filter(({ entry }) => entry.agent === agent),
  }));
});

function leftPercent(t: number): string {
  return `${(t / tMax.value) * 100}%`;
}

function agentColor(agent: AgentId): string {
  switch (agent) {
    case 'ORCH': return 'hsl(221, 83%, 53%)';
    case 'AL':   return 'hsl(199, 89%, 48%)';
    case 'LAB':  return 'hsl(38, 92%, 50%)';
    case 'MOD':  return 'hsl(142, 76%, 36%)';
    case 'XAI':  return 'hsl(280, 70%, 55%)';
  }
}
</script>

<template>
  <div class="script-timeline">
    <div class="timeline-axis">
      <span>t=0s</span>
      <span class="timeline-axis__mid">{{ (tMax / 2).toFixed(1) }}s</span>
      <span>{{ tMax.toFixed(1) }}s</span>
    </div>
    <div v-for="lane in lanes" :key="lane.agent" class="lane">
      <div class="lane__label" :style="{ color: agentColor(lane.agent) }">{{ lane.agent }}</div>
      <div class="lane__track">
        <button
          v-for="ev in lane.events"
          :key="ev.index"
          class="event-chip"
          :class="{ 'event-chip--selected': selectedIndex === ev.index }"
          :style="{ left: leftPercent(ev.entry.t), backgroundColor: agentColor(lane.agent) }"
          :title="`t=${ev.entry.t.toFixed(2)}s · ${ev.entry.action} → ${ev.entry.object}`"
          @click.stop="emit('select', ev.entry, ev.index)"
        >
          {{ ev.entry.action }}
        </button>
      </div>
    </div>
    <div v-if="!entries.length" class="empty">No events recorded yet</div>
  </div>
</template>

<style scoped lang="scss">
.script-timeline { display: flex; flex-direction: column; gap: 0.25rem; }
.timeline-axis {
  display: flex; justify-content: space-between;
  font-size: 0.7rem; color: var(--muted-foreground);
  padding: 0 0 0.25rem 4rem;
  border-bottom: 1px dashed var(--border);
}
.timeline-axis__mid { color: var(--muted-foreground); }
.lane { display: flex; align-items: center; gap: 0.5rem; min-height: 2rem; }
.lane__label {
  width: 3.5rem;
  font-family: monospace;
  font-weight: 600;
  font-size: 0.75rem;
  flex-shrink: 0;
}
.lane__track {
  position: relative;
  flex: 1;
  height: 1.75rem;
  background-color: var(--muted);
  border-radius: 9999px;
}
.event-chip {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  white-space: nowrap;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  border: none;
  color: white;
  font-size: 0.65rem;
  font-weight: 500;
  cursor: pointer;
  opacity: 0.85;
  transition: opacity 0.15s, transform 0.15s, box-shadow 0.15s;
  &:hover { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
  &--selected {
    opacity: 1;
    box-shadow: 0 0 0 2px var(--background), 0 0 0 4px currentColor;
  }
}
.empty { padding: 1rem; text-align: center; color: var(--muted-foreground); font-size: 0.875rem; }
</style>
