<script setup lang="ts">
import type { ScriptEntry } from '@/types/api';

defineProps<{ entry: ScriptEntry | null }>();
</script>

<template>
  <div v-if="entry" class="effect-viewer">
    <div class="effect-viewer__header">
      <span class="effect-viewer__agent">{{ entry.agent }}</span>
      <span class="effect-viewer__action">{{ entry.action }}</span>
      <span class="effect-viewer__arrow">→</span>
      <span class="effect-viewer__object">{{ entry.object }}</span>
    </div>
    <dl class="effect-viewer__meta">
      <div><dt>t</dt><dd>{{ entry.t.toFixed(3) }}s</dd></div>
      <div v-if="entry.latency_ms != null"><dt>latency</dt><dd>{{ entry.latency_ms }}ms</dd></div>
      <div v-if="entry.duration_s != null"><dt>duration</dt><dd>{{ entry.duration_s.toFixed(2) }}s</dd></div>
      <div v-if="entry.interaction_id"><dt>interaction</dt><dd>{{ entry.interaction_id }}</dd></div>
    </dl>
    <pre class="effect-viewer__json">{{ JSON.stringify(entry.effect, null, 2) }}</pre>
  </div>
  <div v-else class="effect-viewer effect-viewer--empty">
    Select an event on the timeline to inspect its effect
  </div>
</template>

<style scoped lang="scss">
.effect-viewer {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.85rem;
  &--empty {
    color: var(--muted-foreground);
    text-align: center;
    padding: 1.5rem 1rem;
  }
}
.effect-viewer__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}
.effect-viewer__agent { font-family: monospace; color: var(--primary); }
.effect-viewer__action { color: var(--foreground); }
.effect-viewer__arrow { color: var(--muted-foreground); }
.effect-viewer__object { font-family: monospace; color: var(--foreground); }
.effect-viewer__meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.5rem;
  margin: 0;
  div { display: flex; flex-direction: column; }
  dt { font-size: 0.65rem; color: var(--muted-foreground); text-transform: uppercase; }
  dd { font-family: monospace; font-size: 0.8rem; margin: 0; }
}
.effect-viewer__json {
  background: var(--muted);
  border-radius: 0.375rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  font-family: monospace;
  overflow: auto;
  max-height: 240px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
