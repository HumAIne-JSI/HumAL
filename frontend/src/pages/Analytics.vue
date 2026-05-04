<script setup lang="ts">
import { ref, computed } from 'vue';
import { toast } from 'vue-sonner';
import Card from '@/components/ui/Card.vue';
import Badge from '@/components/ui/Badge.vue';
import Button from '@/components/ui/Button.vue';
import Checkbox from '@/components/ui/Checkbox.vue';
import SessionCard from '@/components/SessionCard.vue';
import ScriptTimeline from '@/components/ScriptTimeline.vue';
import EffectViewer from '@/components/EffectViewer.vue';
import {
  useAnalyticsOverview,
  useSessions,
  useSession,
  useSampleData,
  setUseSampleData,
} from '@/composables/api/useAnalytics';
import type { AgentId, BenchmarkSessionSummary, ScriptEntry } from '@/types/api';
import {
  BarChart3,
  Activity,
  Layers,
  Users,
  Box,
  Download,
  RefreshCw,
  ChevronRight,
  Filter,
  X,
} from 'lucide-vue-next';

const sampleDataEnabled = computed({
  get: () => useSampleData.value,
  set: (val: boolean) => setUseSampleData(val),
});

const selectedSimId = ref<string>('');
const agentFilter = ref<AgentId | null>(null);
const selectedEntryIndex = ref<number | null>(null);

const { data: overview, isLoading: overviewLoading } = useAnalyticsOverview();
const { data: sessions, isLoading: sessionsLoading } = useSessions();
const sessionEnabled = computed(() => !!selectedSimId.value);
const { data: session, isLoading: sessionLoading } = useSession(selectedSimId, {
  enabled: sessionEnabled,
});

const isLoading = computed(() => overviewLoading.value || sessionsLoading.value);

const selectedEntry = computed<ScriptEntry | null>(() => {
  if (selectedEntryIndex.value == null || !session.value) return null;
  return session.value.script[selectedEntryIndex.value] ?? null;
});

// Derived metrics from the current session script
const derivedMetrics = computed(() => {
  if (!session.value) return null;
  const script = session.value.script;
  const totalEvents = script.length;
  const eventsByAgent: Record<string, number> = {};
  const latencySumByAgent: Record<string, { sum: number; n: number }> = {};
  let totalHumanDuration = 0;
  for (const e of script) {
    eventsByAgent[e.agent] = (eventsByAgent[e.agent] || 0) + 1;
    if (e.latency_ms != null) {
      const bucket = (latencySumByAgent[e.agent] ||= { sum: 0, n: 0 });
      bucket.sum += e.latency_ms;
      bucket.n += 1;
    }
    if (e.duration_s != null) totalHumanDuration += e.duration_s;
  }
  const meanLatencyByAgent: Record<string, number> = {};
  for (const [k, v] of Object.entries(latencySumByAgent)) {
    meanLatencyByAgent[k] = Math.round(v.sum / v.n);
  }
  return { totalEvents, eventsByAgent, meanLatencyByAgent, totalHumanDuration };
});

function selectSession(s: BenchmarkSessionSummary) {
  selectedSimId.value = s.sim_id;
  selectedEntryIndex.value = null;
  agentFilter.value = null;
}

function selectEntry(_entry: ScriptEntry, index: number) {
  selectedEntryIndex.value = index;
}

function toggleAgentFilter(agent: AgentId) {
  agentFilter.value = agentFilter.value === agent ? null : agent;
}

function clearSelection() {
  selectedSimId.value = '';
  selectedEntryIndex.value = null;
  agentFilter.value = null;
}

function exportSession() {
  if (!session.value) return;
  const data = JSON.stringify(session.value, null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${session.value.sim_id}.json`;
  link.click();
  URL.revokeObjectURL(url);
  toast.success('Benchmark exported', { description: `${session.value.sim_id}.json` });
}

function fmtNumber(n: number | undefined): string {
  if (n === undefined || n === null) return 'N/A';
  return n.toLocaleString();
}
</script>

<template>
  <div class="analytics">
    <header class="analytics__header">
      <div class="analytics__header-content">
        <h1 class="analytics__title">
          <BarChart3 class="w-8 h-8" />
          Benchmarking Suite
        </h1>
        <p class="analytics__subtitle">Tracks every agent action across the app for ML evaluation</p>
      </div>
      <div class="analytics__header-actions">
        <label class="sample-toggle">
          <Checkbox v-model="sampleDataEnabled" />
          <span>Sample Data</span>
        </label>
        <Button v-if="selectedSimId && session" variant="outline" size="sm" @click="exportSession">
          <Download class="w-4 h-4" /> Export JSON
        </Button>
      </div>
    </header>

    <div v-if="isLoading" class="analytics__loading">
      <RefreshCw class="w-6 h-6 animate-spin" />
      <span>Loading benchmark sessions...</span>
    </div>

    <template v-else>
      <!-- Overview cards -->
      <section class="analytics__overview">
        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--primary"><Layers class="w-5 h-5" /></div>
            <div class="stat-card__content">
              <span class="stat-card__label">Sessions</span>
              <span class="stat-card__value">{{ fmtNumber(overview?.total_sessions) }}</span>
            </div>
          </div>
        </Card>
        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--success"><Activity class="w-5 h-5" /></div>
            <div class="stat-card__content">
              <span class="stat-card__label">Active</span>
              <span class="stat-card__value">{{ fmtNumber(overview?.active_sessions) }}</span>
            </div>
          </div>
        </Card>
        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--info"><Box class="w-5 h-5" /></div>
            <div class="stat-card__content">
              <span class="stat-card__label">Events</span>
              <span class="stat-card__value">{{ fmtNumber(overview?.total_events) }}</span>
            </div>
          </div>
        </Card>
        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--warning"><Users class="w-5 h-5" /></div>
            <div class="stat-card__content">
              <span class="stat-card__label">Avg events/session</span>
              <span class="stat-card__value">{{ overview?.avg_events_per_session ?? 'N/A' }}</span>
            </div>
          </div>
        </Card>
      </section>

      <div class="analytics__content">
        <!-- Session list -->
        <section class="analytics__sessions">
          <h2 class="section-title">Sessions</h2>
          <div v-if="sessions?.length" class="sessions-grid">
            <SessionCard
              v-for="s in sessions"
              :key="s.sim_id"
              :session="s"
              :selected="s.sim_id === selectedSimId"
              @select="selectSession"
            />
          </div>
          <div v-else class="analytics__empty">No sessions yet</div>
        </section>

        <!-- Detail -->
        <section v-if="session" class="analytics__detail">
          <div class="detail-header">
            <h2 class="section-title">{{ session.sim_id }}</h2>
            <Button variant="ghost" size="sm" @click="clearSelection">
              <X class="w-4 h-4" /> Close
            </Button>
          </div>

          <div v-if="sessionLoading" class="detail-loading">
            <RefreshCw class="w-5 h-5 animate-spin" /><span>Loading...</span>
          </div>

          <template v-else>
            <!-- Environment panel -->
            <Card padding="default">
              <template #title>Environment</template>
              <div class="kv-grid">
                <div><dt>id</dt><dd>{{ session.environment.id }}</dd></div>
                <div><dt>class</dt><dd>{{ session.environment.class }}</dd></div>
                <div v-for="(v, k) in session.environment.attributes" :key="k">
                  <dt>{{ k }}</dt><dd>{{ v }}</dd>
                </div>
              </div>
            </Card>

            <!-- Agents panel -->
            <Card padding="default">
              <template #title>
                <div class="agents-panel-title">
                  <span>Agents</span>
                  <span v-if="agentFilter" class="agents-panel-filter">
                    <Filter class="w-3 h-3" /> filter: {{ agentFilter }}
                    <button class="agents-panel-clear" @click="agentFilter = null">×</button>
                  </span>
                </div>
              </template>
              <div class="agents-grid">
                <button
                  v-for="a in session.agents"
                  :key="a.id"
                  class="agent-pill"
                  :class="{ 'agent-pill--active': agentFilter === a.id }"
                  @click="toggleAgentFilter(a.id)"
                >
                  <div class="agent-pill__head">
                    <span class="agent-pill__id">{{ a.id }}</span>
                    <Badge variant="outline" class="text-[10px]">{{ a.model }}</Badge>
                    <span class="agent-pill__count">
                      {{ derivedMetrics?.eventsByAgent[a.id] ?? 0 }} events
                    </span>
                  </div>
                  <div class="agent-pill__affordances">
                    <span v-for="aff in a.affordances" :key="aff" class="affordance-chip">{{ aff }}</span>
                  </div>
                </button>
              </div>
            </Card>

            <!-- Objects panel -->
            <Card padding="default">
              <template #title>Objects</template>
              <div class="objects-grid">
                <div v-for="o in session.objects" :key="o.id" class="object-card">
                  <div class="object-card__head">
                    <span class="object-card__id">{{ o.id }}</span>
                    <span v-if="o.attributes.kind" class="object-card__kind">{{ o.attributes.kind }}</span>
                  </div>
                  <div class="object-card__affordances">
                    <span v-for="aff in o.affordances" :key="aff" class="affordance-chip">{{ aff }}</span>
                  </div>
                </div>
              </div>
            </Card>

            <!-- Script timeline + effect viewer -->
            <div class="timeline-grid">
              <Card padding="default">
                <template #title>Script Timeline</template>
                <ScriptTimeline
                  :entries="session.script"
                  :agent-filter="agentFilter"
                  :selected-index="selectedEntryIndex"
                  @select="selectEntry"
                />
              </Card>
              <Card padding="default">
                <template #title>Effect</template>
                <EffectViewer :entry="selectedEntry" />
              </Card>
            </div>

            <!-- Derived metrics -->
            <Card v-if="derivedMetrics" padding="default">
              <template #title>Derived Metrics</template>
              <div class="metrics-row">
                <div class="metric-block">
                  <span class="metric-label">Total events</span>
                  <span class="metric-value">{{ derivedMetrics.totalEvents }}</span>
                </div>
                <div class="metric-block">
                  <span class="metric-label">Total human time</span>
                  <span class="metric-value">{{ derivedMetrics.totalHumanDuration.toFixed(1) }}s</span>
                </div>
                <div
                  v-for="(ms, agent) in derivedMetrics.meanLatencyByAgent"
                  :key="agent"
                  class="metric-block"
                >
                  <span class="metric-label">avg latency · {{ agent }}</span>
                  <span class="metric-value">{{ ms }}ms</span>
                </div>
              </div>
            </Card>
          </template>
        </section>

        <section v-else class="analytics__no-selection">
          <ChevronRight class="w-8 h-8 text-muted-foreground" />
          <p>Select a session to inspect its environment, agents, objects and script timeline</p>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.analytics { padding: 1.5rem; max-width: 1400px; margin: 0 auto; }
.analytics__header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;
}
.analytics__title { display: flex; align-items: center; gap: 0.5rem; font-size: 1.5rem; font-weight: 700; margin: 0; }
.analytics__subtitle { color: var(--muted-foreground); margin: 0.25rem 0 0; }
.analytics__header-actions { display: flex; align-items: center; gap: 0.75rem; }
.sample-toggle { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; cursor: pointer; }

.analytics__loading { display: flex; align-items: center; justify-content: center; gap: 0.75rem; padding: 4rem; color: var(--muted-foreground); }

.analytics__overview {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem; margin-bottom: 1.5rem;
}
.stat-card { display: flex; align-items: center; gap: 0.75rem; }
.stat-card__icon {
  width: 2.5rem; height: 2.5rem; border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center; color: white;
  &--primary { background: hsl(221, 83%, 53%); }
  &--success { background: hsl(142, 76%, 36%); }
  &--info    { background: hsl(199, 89%, 48%); }
  &--warning { background: hsl(38, 92%, 50%); }
}
.stat-card__content { display: flex; flex-direction: column; min-width: 0; }
.stat-card__label { font-size: 0.7rem; color: var(--muted-foreground); text-transform: uppercase; }
.stat-card__value { font-size: 1.25rem; font-weight: 700; }

.analytics__content {
  display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem;
  @media (max-width: 900px) { grid-template-columns: 1fr; }
}
.section-title { font-size: 1rem; font-weight: 600; margin: 0 0 0.5rem; }
.analytics__sessions { display: flex; flex-direction: column; gap: 1rem; }
.sessions-grid { display: flex; flex-direction: column; gap: 0.75rem; }
.analytics__empty { padding: 2rem; color: var(--muted-foreground); text-align: center; }

.analytics__detail { display: flex; flex-direction: column; gap: 1rem; }
.detail-header { display: flex; justify-content: space-between; align-items: center; }
.detail-loading { display: flex; align-items: center; gap: 0.5rem; padding: 2rem; color: var(--muted-foreground); }

.kv-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.5rem;
  div { display: flex; flex-direction: column; }
  dt { font-size: 0.65rem; color: var(--muted-foreground); text-transform: uppercase; }
  dd { font-family: monospace; font-size: 0.8rem; margin: 0; word-break: break-word; }
}

.agents-panel-title { display: flex; align-items: center; gap: 0.5rem; }
.agents-panel-filter { display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.7rem; color: var(--muted-foreground); }
.agents-panel-clear { background: none; border: none; cursor: pointer; color: inherit; font-size: 1rem; line-height: 1; padding: 0 0.25rem; }
.agents-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem; }
.agent-pill {
  text-align: left;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.5rem;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.15s;
  &:hover { border-color: var(--primary); transform: translateY(-1px); }
  &--active { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 8%, transparent); }
}
.agent-pill__head { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.agent-pill__id { font-family: monospace; font-weight: 700; }
.agent-pill__count { font-size: 0.7rem; color: var(--muted-foreground); margin-left: auto; }
.agent-pill__affordances { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.5rem; }

.affordance-chip {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  background: var(--muted);
  border-radius: 9999px;
  font-family: monospace;
  color: var(--muted-foreground);
}

.objects-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem; }
.object-card { padding: 0.5rem; border: 1px solid var(--border); border-radius: var(--radius); }
.object-card__head { display: flex; align-items: center; gap: 0.5rem; }
.object-card__id { font-family: monospace; font-weight: 700; }
.object-card__kind { font-size: 0.7rem; color: var(--muted-foreground); }
.object-card__affordances { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.5rem; }

.timeline-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 1rem;
  @media (max-width: 1200px) { grid-template-columns: 1fr; }
}

.metrics-row { display: flex; flex-wrap: wrap; gap: 1rem; }
.metric-block { display: flex; flex-direction: column; min-width: 120px; }
.metric-label { font-size: 0.65rem; color: var(--muted-foreground); text-transform: uppercase; }
.metric-value { font-size: 1.1rem; font-weight: 600; }

.analytics__no-selection {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.5rem; min-height: 300px; color: var(--muted-foreground);
}
</style>
