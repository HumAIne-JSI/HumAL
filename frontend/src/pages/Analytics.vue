<script setup lang="ts">
import { computed } from 'vue';
import { toast } from 'vue-sonner';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Select from '@/components/ui/Select.vue';
import Spinner from '@/components/ui/Spinner.vue';
import MetricsChart from '@/components/MetricsChart.vue';
import UserBehaviorDashboard from '@/components/UserBehaviorDashboard.vue';
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry';
import { useModelPerformance } from '@/composables/api/useAnalytics';
import { useInstances } from '@/composables/api/useActiveLearning';
import {
  aggregateResourceEfficiency,
  aggregateSatisfaction,
  aggregateProgramKpis,
  aggregateResolutionEffort,
} from '@/composables/useUserBehaviorAggregator';
import { useInstanceStore } from '@/stores/useInstanceStore';
import { useMockModeStore } from '@/stores/useMockModeStore';
import { useTelemetryStore } from '@/stores/useTelemetryStore';
import type { ProgramKpi } from '@/types/api';
import {
  BarChart3,
  Cpu,
  Gauge,
  HeartPulse,
  Layers,
  Download,
  Target,
} from 'lucide-vue-next';

const telemetry = useBenchmarkTelemetry();
const instanceStore = useInstanceStore();
const mockStore = useMockModeStore();
const telemetryStore = useTelemetryStore();

// Instance list (live only — avoids a backend call in mock mode).
const instancesQuery = useInstances({
  enabled: computed(() => !mockStore.mockEnabled),
} as unknown as { meta?: undefined });

const instanceOptions = computed(() => {
  if (mockStore.mockEnabled) return [{ value: '0', label: 'Sample run (mock)' }];
  const map = instancesQuery.data.value?.instances ?? {};
  const opts = Object.entries(map).map(([id, info]) => ({
    value: id,
    label: `#${id} · ${info.model_name ?? 'model'}${info.qs ? ` · ${info.qs}` : ''}`,
  }));
  return opts.length ? opts : [{ value: '0', label: 'No instances yet' }];
});

const selectedInstanceValue = computed<string>({
  get: () => String(instanceStore.selectedInstanceId || 0),
  set: (v: string) => instanceStore.setInstance(Number(v)),
});
const selectedInstanceId = computed(() => instanceStore.selectedInstanceId);

// Pillar 1 — model performance (real /info in live, sample in mock).
const { info, summary, isLoading: perfLoading } = useModelPerformance(selectedInstanceId);

// Scope the telemetry-derived pillars: mock -> all seed events; live -> the
// selected instance's events (or all when none selected).
const filterInstanceId = computed<number | null>(() =>
  mockStore.mockEnabled ? null : selectedInstanceId.value > 0 ? selectedInstanceId.value : null,
);
const modeEvents = computed(() => telemetryStore.eventsForMode(mockStore.mockEnabled));

// Pillar 2 — resource efficiency.
const resource = computed(() =>
  aggregateResourceEfficiency(modeEvents.value, filterInstanceId.value, {
    f1_scores: info.value?.f1_scores,
    num_labeled: info.value?.num_labeled,
  }),
);
// Pillar 3 — human satisfaction.
const satisfaction = computed(() => aggregateSatisfaction(modeEvents.value, filterInstanceId.value));

// Resolution assistance — operator effort saved on AI-suggested resolutions.
const resolutionEffort = computed(() =>
  aggregateResolutionEffort(modeEvents.value, filterInstanceId.value),
);

// Programme KPIs (AFU objectives) vs targets.
const programKpis = computed(() =>
  aggregateProgramKpis(modeEvents.value, filterInstanceId.value, summary.value),
);
const kpisOnTrack = computed(() => programKpis.value.filter((k) => k.status === 'on_track').length);

function kpiStatusLabel(s: ProgramKpi['status']): string {
  return { on_track: 'On track', at_risk: 'At risk', off_track: 'Off target', no_data: 'No data' }[s];
}
function kpiAttainment(k: ProgramKpi): number {
  if (k.value == null || k.target == null || k.target === 0) return 0;
  const a = k.higher_is_better ? k.value / k.target : k.target / k.value;
  return Math.max(0, Math.min(1, a));
}
function kpiBarWidth(k: ProgramKpi): string {
  return `${(kpiAttainment(k) * 100).toFixed(0)}%`;
}

const hasModelData = computed(() => (info.value?.f1_scores?.length ?? 0) > 0);
const classes = computed<string[]>(() => (info.value?.classes ?? []).map(String));
const latestPerClassF1 = computed<number[]>(() => {
  const rows = info.value?.f1_per_class ?? [];
  return rows.length ? rows[rows.length - 1]! : [];
});
const latestConfusion = computed<number[][]>(() => {
  const cms = info.value?.confusion_matrices ?? [];
  return cms.length ? cms[cms.length - 1]! : [];
});

const trendMeta = computed(() => {
  switch (summary.value.f1_trend) {
    case 'improving':
      return { label: '▲ improving', trend: 'improving' };
    case 'declining':
      return { label: '▼ declining', trend: 'declining' };
    case 'stable':
      return { label: '● stable', trend: 'stable' };
    default:
      return { label: '—', trend: 'na' };
  }
});

const scoreEfficiencyLabel = computed(() => {
  const s = resource.value.samples_to_f1_80;
  if (s != null) return `${s} labels`;
  return resource.value.decisions_per_hour != null
    ? `${resource.value.decisions_per_hour}/h`
    : '—';
});

// ---------- formatters ----------
function fmtPct(v?: number | null, digits = 1): string {
  if (v == null) return '—';
  return `${(v * 100).toFixed(digits)}%`;
}
function fmtNum(v?: number | null): string {
  if (v == null) return '—';
  return v.toLocaleString();
}
function fmtMs(v?: number | null): string {
  if (v == null) return '—';
  if (v < 1000) return `${Math.round(v)} ms`;
  return `${(v / 1000).toFixed(2)} s`;
}
function fmtSec(v?: number | null): string {
  if (v == null) return '—';
  if (v < 60) return `${v.toFixed(1)}s`;
  if (v < 3600) return `${(v / 60).toFixed(1)} min`;
  return `${(v / 3600).toFixed(1)} h`;
}
function fmtPp(v?: number | null): string {
  if (v == null) return '—';
  const pp = v * 100;
  return `${pp >= 0 ? '+' : ''}${pp.toFixed(1)} pp`;
}

function exportSnapshot() {
  const snapshot = {
    generated_at: new Date().toISOString(),
    resolution_effort: resolutionEffort.value,
    mode: mockStore.mockEnabled ? 'mock' : 'live',
    instance_id: selectedInstanceId.value || null,
    programme_kpis: programKpis.value,
    model_performance: { summary: summary.value, info: info.value ?? null },
    resource_efficiency: resource.value,
    human_satisfaction: satisfaction.value,
  };
  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `benchmark_${mockStore.mockEnabled ? 'mock' : 'live'}_${selectedInstanceId.value || 0}.json`;
  link.click();
  URL.revokeObjectURL(url);
  toast.success('Benchmark snapshot exported');
  telemetry.recordLab('export', 'Mdl', {
    page: 'analytics',
    instance_id: selectedInstanceId.value || null,
    format: 'json',
  });
}
</script>

<template>
  <div class="analytics">
    <header class="analytics__header">
      <div class="analytics__header-content">
        <h1 class="analytics__title">
          <BarChart3 class="w-8 h-8" />
          Performance Overview
        </h1>
        <p class="analytics__subtitle">
          A clear view of AI quality, effort, and team satisfaction
        </p>
      </div>
      <div class="analytics__header-actions">
        <span class="bs-mode" :class="mockStore.mockEnabled ? 'bs-mode--mock' : 'bs-mode--live'">
          {{ mockStore.mockEnabled ? 'Demo data' : 'Live data' }}
        </span>
        <div class="bs-instance">
          <Layers class="w-4 h-4" />
          <Select
            :modelValue="selectedInstanceValue"
            :options="instanceOptions"
            @update:modelValue="(v) => (selectedInstanceValue = String(v))"
          />
        </div>
        <Button variant="outline" size="sm" @click="exportSnapshot">
          <Download class="w-4 h-4" /> Export
        </Button>
      </div>
    </header>

    <!-- Programme KPIs vs AFU targets -->
    <section id="programme-kpis" class="bs-section">
      <h2 class="section-title">
        <Target class="w-5 h-5" /> Key results vs targets
        <span class="kpi-summary">{{ kpisOnTrack }}/{{ programKpis.length }} on track</span>
      </h2>
      <div class="kpi-grid">
        <div
          v-for="k in programKpis"
          :key="k.id"
          class="kpi-card"
          :data-status="k.status"
        >
          <div class="kpi-card__top">
            <span class="kpi-card__label">{{ k.label }}</span>
            <span class="kpi-card__badge" :data-status="k.status">{{ kpiStatusLabel(k.status) }}</span>
          </div>
          <div class="kpi-card__value">{{ k.value != null ? fmtPct(k.value) : '—' }}</div>
          <div class="kpi-card__bar">
            <span class="kpi-card__fill" :style="{ width: kpiBarWidth(k) }" />
          </div>
          <div class="kpi-card__meta">
            <span class="kpi-card__target">
              Target {{ k.higher_is_better ? '≥' : '≤' }} {{ fmtPct(k.target) }}
            </span>
            <span class="kpi-card__src">{{ k.source }}</span>
          </div>
          <p class="kpi-card__hint">{{ k.hint }}</p>
          <p v-if="!k.instrumented" class="kpi-card__note">Not yet instrumented</p>
        </div>
      </div>
    </section>

    <!-- Scorecard: one headline KPI per pillar -->
    <section class="bs-scorecard">
      <Card variant="elevated" padding="default">
        <div class="bs-score">
          <div class="bs-score__icon bs-score__icon--model"><Gauge class="w-5 h-5" /></div>
          <div class="bs-score__body">
            <span class="bs-score__label">Model performance</span>
            <span class="bs-score__value">{{ fmtPct(summary.latest_f1) }}</span>
            <span class="bs-score__hint">
              Quality score ·
              <span class="bs-trend" :data-trend="trendMeta.trend">{{ trendMeta.label }}</span>
            </span>
          </div>
        </div>
      </Card>
      <Card variant="elevated" padding="default">
        <div class="bs-score">
          <div class="bs-score__icon bs-score__icon--resource"><Cpu class="w-5 h-5" /></div>
          <div class="bs-score__body">
            <span class="bs-score__label">Resource efficiency</span>
            <span class="bs-score__value">{{ scoreEfficiencyLabel }}</span>
            <span class="bs-score__hint">to reach 0.80 quality</span>
          </div>
        </div>
      </Card>
      <Card variant="elevated" padding="default">
        <div class="bs-score">
          <div class="bs-score__icon bs-score__icon--satisfaction"><HeartPulse class="w-5 h-5" /></div>
          <div class="bs-score__body">
            <span class="bs-score__label">Human satisfaction</span>
            <span class="bs-score__value">{{ fmtPct(satisfaction.satisfaction_index) }}</span>
            <span class="bs-score__hint">agreement {{ fmtPct(satisfaction.acceptance_rate) }}</span>
          </div>
        </div>
      </Card>
    </section>

    <nav class="bs-nav">
      <a href="#programme-kpis">Key results</a>
      <a href="#pillar-model">Model performance</a>
      <a href="#pillar-resource">Resource efficiency</a>
      <a href="#pillar-satisfaction">Human satisfaction</a>
    </nav>

    <!-- Pillar 1 — Model performance -->
    <section id="pillar-model" class="bs-section">
      <h2 class="section-title"><Gauge class="w-5 h-5" /> Model performance</h2>
      <div v-if="perfLoading" class="analytics__loading">
        <Spinner label="Loading model metrics…" />
      </div>
      <div v-else-if="!hasModelData" class="analytics__empty">
        <template v-if="mockStore.mockEnabled">No sample data available.</template>
        <template v-else>Select a project with training history to see AI metrics.</template>
      </div>
      <template v-else>
        <div class="bs-metric-row">
          <div class="bs-metric">
            <span class="bs-metric__label">Quality score</span>
            <span class="bs-metric__value">{{ fmtPct(summary.latest_f1) }}</span>
          </div>
          <div class="bs-metric">
            <span class="bs-metric__label">Accuracy</span>
            <span class="bs-metric__value">{{ fmtPct(summary.latest_accuracy) }}</span>
          </div>
          <div class="bs-metric">
            <span class="bs-metric__label">Ranking score</span>
            <span class="bs-metric__value">{{ fmtPct(summary.latest_auroc) }}</span>
          </div>
          <div class="bs-metric">
            <span class="bs-metric__label">Quality gain</span>
            <span class="bs-metric__value">{{ fmtPp(summary.f1_improvement) }}</span>
          </div>
          <div class="bs-metric">
            <span class="bs-metric__label">Uncertainty ↓</span>
            <span class="bs-metric__value">
              {{ summary.entropy_reduction != null ? summary.entropy_reduction.toFixed(2) : '—' }}
            </span>
          </div>
          <div class="bs-metric">
            <span class="bs-metric__label">Labeled</span>
            <span class="bs-metric__value">{{ fmtNum(summary.total_labeled) }}</span>
          </div>
        </div>

        <div class="bs-grid-2">
          <Card padding="default">
            <template #title>Quality score over training rounds</template>
            <div class="bs-chart">
              <MetricsChart :scores="info?.f1_scores ?? []" label="Quality score" :height="220" />
            </div>
          </Card>
          <Card padding="default">
            <template #title>Accuracy over training rounds</template>
            <div class="bs-chart">
              <MetricsChart :scores="info?.accuracies ?? []" label="Accuracy" :height="220" />
            </div>
          </Card>
        </div>

        <!-- <div class="bs-grid-2">
          <Card v-if="latestPerClassF1.length" padding="default">
            <template #title>Quality score by category</template>
            <ul class="bs-bars">
              <li v-for="(f1v, i) in latestPerClassF1" :key="i" class="bs-bar">
                <span class="bs-bar__label">{{ classes[i] ?? 'category ' + i }}</span>
                <span class="bs-bar__track">
                  <span class="bs-bar__fill" :style="{ width: f1v * 100 + '%' }" />
                </span>
                <span class="bs-bar__val">{{ fmtPct(f1v) }}</span>
              </li>
            </ul>
          </Card>
          <Card v-if="latestConfusion.length" padding="default">
            <template #title>Prediction breakdown</template>
            <div class="bs-cm-wrap">
              <table class="bs-cm">
                <thead>
                  <tr>
                    <th></th>
                    <th v-for="(c, i) in classes" :key="i">{{ c }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, r) in latestConfusion" :key="r">
                    <th>{{ classes[r] ?? r }}</th>
                    <td v-for="(cell, c) in row" :key="c" :class="{ 'bs-cm__diag': r === c }">
                      {{ cell }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div> -->
      </template>
    </section>

    <!-- Pillar 2 — Resource efficiency -->
    <section id="pillar-resource" class="bs-section">
      <h2 class="section-title"><Cpu class="w-5 h-5" /> Resource efficiency</h2>
      <div class="bs-grid-3">
        <Card padding="default">
          <template #title>Labeling effort</template>
          <ul class="kv-list">
            <li><span>Labels → 0.70 quality</span><strong>{{ fmtNum(resource.samples_to_f1_70) }}</strong></li>
            <li><span>Labels → 0.80 quality</span><strong>{{ fmtNum(resource.samples_to_f1_80) }}</strong></li>
            <li><span>Labels → 0.90 quality</span><strong>{{ fmtNum(resource.samples_to_f1_90) }}</strong></li>
            <li>
              <span>Quality gain / 100 labels</span><strong>{{ fmtPp(resource.f1_gain_per_100_labels) }}</strong>
            </li>
            <li><span>Total labels</span><strong>{{ fmtNum(resource.labels_total) }}</strong></li>
          </ul>
        </Card>
        <Card padding="default">
          <template #title>Human effort</template>
          <ul class="kv-list">
            <li><span>Total human time</span><strong>{{ fmtSec(resource.total_human_seconds) }}</strong></li>
            <li>
              <span>Mean decision time</span><strong>{{ fmtSec(resource.mean_decision_seconds) }}</strong>
            </li>
            <li>
              <span>Throughput</span>
              <strong>{{ resource.decisions_per_hour != null ? resource.decisions_per_hour + ' /h' : '—' }}</strong>
            </li>
          </ul>
        </Card>
        <Card padding="default">
          <template #title>AI response time</template>
          <ul class="kv-list">
            <li><span>Average AI response</span><strong>{{ fmtMs(resource.mean_ai_latency_ms) }}</strong></li>
            <li><span>Slower responses (p95)</span><strong>{{ fmtMs(resource.p95_ai_latency_ms) }}</strong></li>
            <li><span>Average prediction</span><strong>{{ fmtMs(resource.mean_predict_latency_ms) }}</strong></li>
            <li><span>Average explanation</span><strong>{{ fmtMs(resource.mean_xai_latency_ms) }}</strong></li>
            <li><span>Response samples</span><strong>{{ fmtNum(resource.ai_latency_samples) }}</strong></li>
          </ul>
        </Card>
        <Card padding="default">
          <template #title>Resolution assistance</template>
          <ul class="kv-list">
            <li>
              <span>Suggestions used</span><strong>{{ fmtNum(resolutionEffort.resolutions_used) }}</strong>
            </li>
            <li><span>Used verbatim</span><strong>{{ fmtPct(resolutionEffort.verbatim_rate) }}</strong></li>
            <li>
              <span>Mean edit ratio</span><strong>{{ fmtPct(resolutionEffort.mean_edit_ratio) }}</strong>
            </li>
            <li><span>Effort saved</span><strong>{{ fmtPct(resolutionEffort.effort_saved) }}</strong></li>
            <li>
              <span>Mean review time</span><strong>{{ fmtSec(resolutionEffort.mean_review_seconds) }}</strong>
            </li>
          </ul>
        </Card>
      </div>
    </section>

    <!-- Pillar 3 — Human satisfaction -->
    <section id="pillar-satisfaction" class="bs-section">
      <h2 class="section-title"><HeartPulse class="w-5 h-5" /> Human satisfaction</h2>
      <div class="bs-grid-3">
        <Card padding="default">
          <template #title>Decision quality</template>
          <ul class="kv-list">
            <li><span>Confirmations</span><strong>{{ fmtNum(satisfaction.confirm_count) }}</strong></li>
            <li><span>Corrections</span><strong>{{ fmtNum(satisfaction.override_count) }}</strong></li>
            <li><span>Skips</span><strong>{{ fmtNum(satisfaction.abstain_count) }}</strong></li>
            <li><span>Agreement rate</span><strong>{{ fmtPct(satisfaction.acceptance_rate) }}</strong></li>
            <li><span>Correction rate</span><strong>{{ fmtPct(satisfaction.override_rate) }}</strong></li>
          </ul>
        </Card>
        <Card padding="default">
          <template #title>Reported friction</template>
          <ul class="kv-list">
            <li><span>Fatigue flags</span><strong>{{ fmtNum(satisfaction.tired_count) }}</strong></li>
            <li><span>Difficult tickets</span><strong>{{ fmtNum(satisfaction.difficult_count) }}</strong></li>
            <li><span>“I don't know”</span><strong>{{ fmtNum(satisfaction.idk_count) }}</strong></li>
            <li>
              <span>Flagged decisions</span><strong>{{ fmtPct(satisfaction.flagged_decision_rate) }}</strong>
            </li>
          </ul>
        </Card>
        <Card padding="default">
          <template #title>Satisfaction index</template>
          <div class="bs-gauge">
            <span class="bs-gauge__value">{{ fmtPct(satisfaction.satisfaction_index) }}</span>
            <span class="bs-gauge__hint">agreement, lowered by reported friction</span>
          </div>
        </Card>
      </div>

      <h3 class="bs-subtitle">Engagement &amp; interaction detail</h3>
      <UserBehaviorDashboard :embedded="true" :instance-id="filterInstanceId" />
    </section>
  </div>
</template>

<style scoped lang="scss">
.analytics { padding: 1.5rem; max-width: 1400px; margin: 0 auto; }
.analytics__header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;
  position: sticky; top: 0; z-index: 5;
  background: var(--background);
  padding: 0.75rem 0; border-bottom: 1px solid var(--border);
}
.analytics__title { display: flex; align-items: center; gap: 0.5rem; font-size: 1.5rem; font-weight: 700; margin: 0; }
.analytics__subtitle { color: var(--muted-foreground); margin: 0.25rem 0 0; }
.analytics__header-actions { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }

.bs-mode {
  font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;
  padding: 0.2rem 0.55rem; border-radius: 9999px; border: 1px solid var(--border);
  &--mock { color: hsl(38, 92%, 40%); background: color-mix(in srgb, hsl(38, 92%, 50%) 12%, transparent); }
  &--live { color: hsl(142, 71%, 32%); background: color-mix(in srgb, hsl(142, 76%, 36%) 12%, transparent); }
}
.bs-instance { display: flex; align-items: center; gap: 0.4rem; min-width: 220px; }

.analytics__loading { display: flex; align-items: center; justify-content: center; gap: 0.75rem; padding: 2.5rem; color: var(--muted-foreground); }
.analytics__empty { padding: 2rem; color: var(--muted-foreground); text-align: center; border: 1px dashed var(--border); border-radius: var(--radius); }

.section-title { display: flex; align-items: center; gap: 0.5rem; font-size: 1.05rem; font-weight: 700; margin: 0 0 0.9rem; }

/* Programme KPIs */
.kpi-summary {
  margin-left: auto; font-size: 0.75rem; font-weight: 600; color: var(--muted-foreground);
  border: 1px solid var(--border); border-radius: 9999px; padding: 0.15rem 0.6rem;
}
.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;
}
.kpi-card {
  border: 1px solid var(--border); border-left-width: 4px; border-radius: var(--radius);
  background: var(--card); padding: 0.85rem 1rem; display: flex; flex-direction: column; gap: 0.35rem;
  &[data-status='on_track'] { border-left-color: hsl(142, 71%, 42%); }
  &[data-status='at_risk'] { border-left-color: hsl(38, 92%, 50%); }
  &[data-status='off_track'] { border-left-color: hsl(0, 72%, 55%); }
  &[data-status='no_data'] { border-left-color: var(--border); }
}
.kpi-card__top { display: flex; align-items: flex-start; justify-content: space-between; gap: 0.5rem; }
.kpi-card__label { font-size: 0.82rem; font-weight: 600; line-height: 1.25; }
.kpi-card__badge {
  flex-shrink: 0; font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
  padding: 0.12rem 0.45rem; border-radius: 9999px;
  &[data-status='on_track'] { color: hsl(142, 71%, 30%); background: color-mix(in srgb, hsl(142, 76%, 36%) 15%, transparent); }
  &[data-status='at_risk'] { color: hsl(38, 92%, 35%); background: color-mix(in srgb, hsl(38, 92%, 50%) 18%, transparent); }
  &[data-status='off_track'] { color: hsl(0, 72%, 45%); background: color-mix(in srgb, hsl(0, 72%, 55%) 15%, transparent); }
  &[data-status='no_data'] { color: var(--muted-foreground); background: var(--muted); }
}
.kpi-card__value { font-size: 1.7rem; font-weight: 800; line-height: 1; }
.kpi-card__bar { height: 0.4rem; background: var(--muted); border-radius: 9999px; overflow: hidden; }
.kpi-card__fill { display: block; height: 100%; border-radius: 9999px; background: var(--primary); }
.kpi-card[data-status='on_track'] .kpi-card__fill { background: hsl(142, 71%, 42%); }
.kpi-card[data-status='at_risk'] .kpi-card__fill { background: hsl(38, 92%, 50%); }
.kpi-card[data-status='off_track'] .kpi-card__fill { background: hsl(0, 72%, 55%); }
.kpi-card__meta { display: flex; justify-content: space-between; gap: 0.5rem; font-size: 0.72rem; color: var(--muted-foreground); }
.kpi-card__hint { font-size: 0.72rem; color: var(--muted-foreground); margin: 0; line-height: 1.3; }
.kpi-card__note {
  font-size: 0.68rem; font-weight: 600; color: hsl(38, 92%, 38%); margin: 0;
}

/* Scorecard */
.bs-scorecard {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 1rem; margin-bottom: 1.25rem;
}
.bs-score { display: flex; align-items: center; gap: 0.9rem; }
.bs-score__icon {
  width: 3rem; height: 3rem; border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0;
  &--model { background: hsl(221, 83%, 53%); }
  &--resource { background: hsl(262, 83%, 58%); }
  &--satisfaction { background: hsl(330, 81%, 55%); }
}
.bs-score__body { display: flex; flex-direction: column; min-width: 0; }
.bs-score__label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.03em; color: var(--muted-foreground); }
.bs-score__value { font-size: 1.6rem; font-weight: 800; line-height: 1.1; }
.bs-score__hint { font-size: 0.75rem; color: var(--muted-foreground); margin-top: 0.15rem; }
.bs-trend {
  font-weight: 600;
  &[data-trend='improving'] { color: hsl(142, 71%, 40%); }
  &[data-trend='declining'] { color: hsl(0, 72%, 55%); }
  &[data-trend='stable'] { color: hsl(38, 92%, 45%); }
  &[data-trend='na'] { color: var(--muted-foreground); }
}

/* In-page anchor nav */
.bs-nav {
  display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem;
  a {
    font-size: 0.8rem; font-weight: 500; color: var(--muted-foreground);
    padding: 0.35rem 0.75rem; border: 1px solid var(--border); border-radius: 9999px;
    text-decoration: none; transition: color 0.15s, border-color 0.15s;
    &:hover { color: var(--primary); border-color: var(--primary); }
  }
}

/* Pillar sections */
.bs-section { margin-bottom: 2.25rem; scroll-margin-top: 90px; }
.bs-subtitle { font-size: 0.95rem; font-weight: 600; margin: 1.5rem 0 0.75rem; color: var(--foreground); }

.bs-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1rem;
  @media (max-width: 900px) { grid-template-columns: 1fr; } }
.bs-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
  @media (max-width: 900px) { grid-template-columns: 1fr; } }

.bs-metric-row {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem; margin-bottom: 1rem;
}
.bs-metric {
  display: flex; flex-direction: column; padding: 0.6rem 0.75rem;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--card);
}
.bs-metric__label { font-size: 0.65rem; text-transform: uppercase; color: var(--muted-foreground); }
.bs-metric__value { font-size: 1.2rem; font-weight: 700; }

.bs-chart { position: relative; height: 240px; }

.kv-list {
  list-style: none; margin: 0; padding: 0;
  li {
    display: flex; justify-content: space-between; align-items: center; gap: 1rem;
    padding: 0.4rem 0; border-bottom: 1px dashed var(--border);
    &:last-child { border-bottom: none; }
    span { color: var(--muted-foreground); font-size: 0.85rem; }
    strong { font-variant-numeric: tabular-nums; }
  }
}

.bs-bars { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.6rem; }
.bs-bar { display: grid; grid-template-columns: 90px 1fr 48px; align-items: center; gap: 0.6rem; }
.bs-bar__label { font-size: 0.8rem; color: var(--muted-foreground); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bs-bar__track { height: 0.55rem; background: var(--muted); border-radius: 9999px; overflow: hidden; }
.bs-bar__fill { display: block; height: 100%; background: hsl(221, 83%, 53%); border-radius: 9999px; }
.bs-bar__val { font-size: 0.8rem; font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }

.bs-cm-wrap { overflow-x: auto; }
.bs-cm {
  border-collapse: collapse; font-size: 0.8rem; width: 100%;
  th, td { border: 1px solid var(--border); padding: 0.35rem 0.55rem; text-align: center; }
  th { color: var(--muted-foreground); font-weight: 600; background: var(--muted); }
  td { font-variant-numeric: tabular-nums; }
  .bs-cm__diag { background: color-mix(in srgb, hsl(142, 76%, 36%) 22%, transparent); font-weight: 700; }
}

.bs-gauge { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.4rem; padding: 1rem 0; }
.bs-gauge__value { font-size: 2.4rem; font-weight: 800; color: hsl(330, 81%, 50%); line-height: 1; }
.bs-gauge__hint { font-size: 0.75rem; color: var(--muted-foreground); text-align: center; }
</style>
