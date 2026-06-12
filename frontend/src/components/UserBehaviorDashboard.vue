<script setup lang="ts">
/**
 * UserBehaviorDashboard â€” shows analytics that explain *how the user works*
 * and *whether the AI is helping* â€” derived from the al_events table that
 * we already populate via the telemetry composable.
 *
 * Sections:
 *   1. Overview stat cards.
 *   2. AI impact: confirm vs override vs abstain, aided vs manual decision time.
 *   3. Confidence vs acceptance: stacked horizontal bar by confidence bucket.
 *   4. XAI lift: with vs without explanation.
 *   5. Event timeline: line chart of activity per minute.
 *   6. Page engagement: bar chart of time spent per page.
 *   7. Ticket heatmap: top tickets by interaction count.
 *   8. Funnel: select -> inspect explanation -> label.
 */
import { computed, ref } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from 'chart.js'
import { Line, Bar, Doughnut } from 'vue-chartjs'
import Card from '@/components/ui/Card.vue'
import Select from '@/components/ui/Select.vue'
import {
  useUserBehaviorOverview,
  useUserBehaviorAIImpact,
  useUserBehaviorXaiEngagement,
  useUserBehaviorPageEngagement,
  useUserBehaviorTicketHeatmap,
  useUserBehaviorTimeline,
  useUserBehaviorFunnel,
} from '@/composables/api/useAnalytics'
import { useInstanceStore } from '@/stores/useInstanceStore'
import { useMockModeStore } from '@/stores/useMockModeStore'
import { useTelemetryStore } from '@/stores/useTelemetryStore'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

const instanceStore = useInstanceStore()
const mockStore = useMockModeStore()
const telemetryStore = useTelemetryStore()
const scope = ref<'all' | 'current'>('all')

const instanceId = computed<number | null>(() =>
  scope.value === 'current' && instanceStore.selectedInstanceId > 0
    ? instanceStore.selectedInstanceId
    : null,
)

const { data: overview } = useUserBehaviorOverview(instanceId)
const { data: aiImpact } = useUserBehaviorAIImpact(instanceId)
const { data: xai } = useUserBehaviorXaiEngagement(instanceId)
const { data: pageEng } = useUserBehaviorPageEngagement(instanceId)
const { data: heatmap } = useUserBehaviorTicketHeatmap(instanceId, 20)
const { data: timeline } = useUserBehaviorTimeline(instanceId, 60)
const { data: funnel } = useUserBehaviorFunnel(instanceId)

const scopeOptions = computed(() => [
  { value: 'all', label: 'All instances' },
  {
    value: 'current',
    label: instanceStore.selectedInstanceId > 0
      ? `Instance #${instanceStore.selectedInstanceId}`
      : 'Selected instance',
  },
])

// ---------- formatters ----------
function fmtNumber(n?: number | null): string {
  if (n == null) return 'â€”'
  return n.toLocaleString()
}
function fmtSeconds(s?: number | null): string {
  if (s == null) return 'â€”'
  if (s < 60) return `${s.toFixed(1)}s`
  if (s < 3600) return `${(s / 60).toFixed(1)} min`
  return `${(s / 3600).toFixed(1)} h`
}
function fmtPercent(rate?: number | null): string {
  if (rate == null) return 'â€”'
  return `${(rate * 100).toFixed(1)}%`
}
function fmtDateTime(iso?: string | null): string {
  if (!iso) return 'â€”'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

// ---------- chart datasets ----------
const decisionDonutData = computed(() => {
  const d = aiImpact.value
  return {
    labels: ['Confirm', 'Override', 'Abstain'],
    datasets: [
      {
        data: [d?.confirm_count ?? 0, d?.override_count ?? 0, d?.abstain_count ?? 0],
        backgroundColor: ['#22c55e', '#f97316', '#94a3b8'],
        borderWidth: 0,
      },
    ],
  }
})
const donutOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } },
}

const decisionTimeBarData = computed(() => {
  const d = aiImpact.value
  return {
    labels: ['AI-aided', 'Manual'],
    datasets: [
      {
        label: 'Mean decision time (s)',
        data: [d?.mean_decision_time_aided_s ?? 0, d?.mean_decision_time_manual_s ?? 0],
        backgroundColor: ['#3b82f6', '#a3a3a3'],
        borderRadius: 4,
      },
    ],
  }
})

const confidenceBucketData = computed(() => {
  const buckets = aiImpact.value?.confidence_buckets ?? []
  return {
    labels: buckets.map((b) => b.label),
    datasets: [
      {
        label: 'Confirm',
        data: buckets.map((b) => b.confirm),
        backgroundColor: '#22c55e',
        stack: 'decisions',
      },
      {
        label: 'Override',
        data: buckets.map((b) => b.override),
        backgroundColor: '#f97316',
        stack: 'decisions',
      },
      {
        label: 'Abstain',
        data: buckets.map((b) => b.abstain),
        backgroundColor: '#94a3b8',
        stack: 'decisions',
      },
    ],
  }
})
const stackedBarOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: { legend: { position: 'bottom' } },
  scales: {
    x: { stacked: true, beginAtZero: true },
    y: { stacked: true },
  },
}

const horizontalBarOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true } },
}

const timelineChartData = computed(() => {
  const bins = timeline.value?.bins ?? []
  return {
    labels: bins.map((b) => {
      try {
        return new Date(b.bucket_start).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        })
      } catch {
        return b.bucket_start
      }
    }),
    datasets: [
      {
        label: 'Events',
        data: bins.map((b) => b.count),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.15)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
      },
    ],
  }
})
const timelineOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
}

const pageEngagementChartData = computed(() => {
  const pages = pageEng.value?.pages ?? []
  return {
    labels: pages.map((p) => p.page),
    datasets: [
      {
        label: 'Total time (s)',
        data: pages.map((p) => p.total_duration_s),
        backgroundColor: '#6366f1',
        borderRadius: 4,
      },
    ],
  }
})

// ---------- derived values ----------
const xaiLift = computed<number | null>(() => {
  const w = xai.value?.acceptance_rate_with_xai
  const wo = xai.value?.acceptance_rate_without_xai
  if (w == null || wo == null) return null
  return w - wo
})
const decisionTimeSaved = computed<number | null>(() => {
  const d = aiImpact.value?.decision_time_delta_s
  return d != null && d > 0 ? d : null
})

function resetMockEvents() {
  telemetryStore.reseed()
}
function clearMockEvents() {
  telemetryStore.clear()
}
</script>

<template>
  <div class="user-behavior" data-track-region="user_behavior_dashboard">
    <header class="user-behavior__header">
      <div>
        <h2 class="user-behavior__title">User Behavior</h2>
        <p class="user-behavior__subtitle">
          What the team is doing in the app and how the AI is affecting their work.
        </p>
      </div>
      <div class="user-behavior__controls">
        <div v-if="mockStore.mockEnabled" class="user-behavior__mock">
          <span class="user-behavior__mock-tag">Mock mode</span>
          <span class="user-behavior__mock-count">
            {{ telemetryStore.events.length.toLocaleString() }} local events
          </span>
          <button
            type="button"
            class="user-behavior__mock-btn"
            data-track-click="reset_demo_events"
            @click="resetMockEvents"
          >
            Reset demo
          </button>
          <button
            type="button"
            class="user-behavior__mock-btn user-behavior__mock-btn--ghost"
            data-track-click="clear_demo_events"
            @click="clearMockEvents"
          >
            Clear
          </button>
        </div>
        <div class="user-behavior__scope">
          <label>Scope</label>
          <Select :modelValue="scope" :options="scopeOptions" @update:modelValue="(v) => (scope = v as any)" />
        </div>
      </div>
    </header>

    <!-- Overview stat cards -->
    <section class="overview-grid">
      <Card variant="elevated" padding="sm">
        <div class="stat">
          <span class="stat__label">Total events</span>
          <span class="stat__value">{{ fmtNumber(overview?.total_events) }}</span>
        </div>
      </Card>
      <Card variant="elevated" padding="sm">
        <div class="stat">
          <span class="stat__label">Tickets touched</span>
          <span class="stat__value">{{ fmtNumber(overview?.unique_tickets_touched) }}</span>
        </div>
      </Card>
      <Card variant="elevated" padding="sm">
        <div class="stat">
          <span class="stat__label">Active time</span>
          <span class="stat__value">{{ fmtSeconds(overview?.total_active_seconds) }}</span>
        </div>
      </Card>
      <Card variant="elevated" padding="sm">
        <div class="stat">
          <span class="stat__label">Mean decision</span>
          <span class="stat__value">{{ fmtSeconds(overview?.mean_decision_seconds) }}</span>
        </div>
      </Card>
    </section>

    <!-- AI impact -->
    <section class="grid-2">
      <Card padding="default">
        <template #title>Decisions</template>
        <template #description>
          Acceptance rate: {{ fmtPercent(aiImpact?.acceptance_rate) }}
        </template>
        <div class="chart-box chart-box--sm">
          <Doughnut :data="decisionDonutData" :options="donutOptions" />
        </div>
      </Card>

      <Card padding="default">
        <template #title>Decision time: AI-aided vs manual</template>
        <template #description>
          <span v-if="decisionTimeSaved != null">
            AI saves ~{{ fmtSeconds(decisionTimeSaved) }} per ticket on average.
          </span>
          <span v-else>Not enough data to compare yet.</span>
        </template>
        <div class="chart-box chart-box--sm">
          <Bar :data="decisionTimeBarData" :options="horizontalBarOptions" />
        </div>
      </Card>
    </section>

    <!-- Confidence vs acceptance -->
    <section>
      <Card padding="default">
        <template #title>Confidence vs label decision</template>
        <template #description>
          Each bar shows how the team labelled the model's predictions in that
          confidence range. High-confidence overrides may indicate
          mis-calibration.
        </template>
        <div class="chart-box chart-box--md">
          <Bar :data="confidenceBucketData" :options="stackedBarOptions" />
        </div>
      </Card>
    </section>

    <!-- XAI engagement -->
    <section class="grid-2">
      <Card padding="default">
        <template #title>XAI lift</template>
        <template #description>
          <span v-if="xaiLift != null">
            With XAI: {{ fmtPercent(xai?.acceptance_rate_with_xai) }} vs without:
            {{ fmtPercent(xai?.acceptance_rate_without_xai) }}
            <strong>({{ xaiLift >= 0 ? '+' : '' }}{{ (xaiLift * 100).toFixed(1) }} pp)</strong>
          </span>
          <span v-else>Need more decisions to compute lift.</span>
        </template>
        <ul class="kv-list">
          <li>
            <span>Decisions with XAI</span>
            <strong>{{ fmtNumber(xai?.decisions_with_xai) }}</strong>
          </li>
          <li>
            <span>Decisions without XAI</span>
            <strong>{{ fmtNumber(xai?.decisions_without_xai) }}</strong>
          </li>
          <li>
            <span>Mean time with XAI</span>
            <strong>{{ fmtSeconds(xai?.mean_decision_time_with_xai_s) }}</strong>
          </li>
          <li>
            <span>Mean time without XAI</span>
            <strong>{{ fmtSeconds(xai?.mean_decision_time_without_xai_s) }}</strong>
          </li>
        </ul>
      </Card>

      <Card padding="default">
        <template #title>Decision funnel</template>
        <template #description>
          What fraction of opened tickets reach a label, with or without an
          explanation along the way.
        </template>
        <ol class="funnel">
          <li class="funnel__step">
            <span class="funnel__label">Selected</span>
            <span class="funnel__count">{{ fmtNumber(funnel?.selected) }}</span>
          </li>
          <li class="funnel__step funnel__step--narrow">
            <span class="funnel__label">Inspected explanation</span>
            <span class="funnel__count">
              {{ fmtNumber(funnel?.inspected_explanation) }}
              <small>({{ fmtPercent(funnel?.select_to_explanation_rate) }})</small>
            </span>
          </li>
          <li class="funnel__step funnel__step--narrowest">
            <span class="funnel__label">Labeled</span>
            <span class="funnel__count">
              {{ fmtNumber(funnel?.labeled) }}
              <small>({{ fmtPercent(funnel?.select_to_label_rate) }})</small>
            </span>
          </li>
        </ol>
      </Card>
    </section>

    <!-- Timeline -->
    <section>
      <Card padding="default">
        <template #title>Activity timeline</template>
        <template #description>Events per minute across the period.</template>
        <div class="chart-box chart-box--md">
          <Line :data="timelineChartData" :options="timelineOptions" />
        </div>
      </Card>
    </section>

    <!-- Page engagement + heatmap -->
    <section class="grid-2">
      <Card padding="default">
        <template #title>Time per page</template>
        <template #description>Where the team is spending their day.</template>
        <div class="chart-box chart-box--sm">
          <Bar :data="pageEngagementChartData" :options="horizontalBarOptions" />
        </div>
      </Card>

      <Card padding="default">
        <template #title>Most-engaged tickets</template>
        <template #description>
          Top tickets by total interaction count â€” useful to spot hard cases the
          team revisits repeatedly.
        </template>
        <div class="heatmap-table-wrap">
          <table class="heatmap-table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th class="num">Interactions</th>
                <th class="num">Total time</th>
                <th>Last seen</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in heatmap?.entries ?? []" :key="row.ticket_ref">
                <td>{{ row.ticket_ref }}</td>
                <td class="num">{{ fmtNumber(row.interaction_count) }}</td>
                <td class="num">{{ fmtSeconds(row.total_seconds) }}</td>
                <td>{{ fmtDateTime(row.last_seen_at) }}</td>
              </tr>
              <tr v-if="!heatmap?.entries?.length">
                <td colspan="4" class="empty">No ticket interactions yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  </div>
</template>

<style scoped lang="scss">
.user-behavior {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.user-behavior__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  flex-wrap: wrap;
}
.user-behavior__title { margin: 0; font-size: 1.25rem; font-weight: 600; }
.user-behavior__subtitle { margin: 0.25rem 0 0; color: var(--muted-foreground); font-size: 0.875rem; }
.user-behavior__controls {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  flex-wrap: wrap;
}
.user-behavior__mock {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border: 1px dashed var(--border);
  border-radius: 0.5rem;
  background: color-mix(in srgb, var(--muted) 30%, transparent);
  font-size: 0.8rem;
}
.user-behavior__mock-tag {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted-foreground);
}
.user-behavior__mock-count {
  color: var(--muted-foreground);
}
.user-behavior__mock-btn {
  appearance: none;
  border: 1px solid var(--border);
  background: var(--background);
  color: inherit;
  padding: 0.25rem 0.6rem;
  border-radius: 0.375rem;
  font-size: 0.8rem;
  cursor: pointer;
  &:hover { background: var(--muted); }
  &--ghost { background: transparent; }
}
.user-behavior__scope {
  display: flex; flex-direction: column; gap: 0.25rem;
  label { font-size: 0.75rem; color: var(--muted-foreground); }
  min-width: 12rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}
.stat {
  display: flex; flex-direction: column; gap: 0.25rem;
  &__label { font-size: 0.75rem; color: var(--muted-foreground); text-transform: uppercase; letter-spacing: 0.04em; }
  &__value { font-size: 1.5rem; font-weight: 600; }
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 1rem;
}

.chart-box {
  position: relative;
  width: 100%;
  &--sm { height: 240px; }
  &--md { height: 320px; }
}

.kv-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 0.4rem;
  li {
    display: flex; justify-content: space-between; align-items: baseline;
    font-size: 0.9rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
  }
  li:last-child { border-bottom: none; }
}

.funnel {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 0.5rem;
  counter-reset: funnel;
}
.funnel__step {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--muted, #f1f5f9);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  font-weight: 500;
  &--narrow { width: 85%; margin-left: auto; margin-right: auto; }
  &--narrowest { width: 70%; margin-left: auto; margin-right: auto; }
  small { color: var(--muted-foreground); font-weight: 400; margin-left: 0.4rem; }
}

.heatmap-table-wrap {
  max-height: 360px;
  overflow-y: auto;
}
.heatmap-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  th, td {
    text-align: left;
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid var(--border);
  }
  th { font-weight: 600; color: var(--muted-foreground); position: sticky; top: 0; background: var(--background); }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  td.empty { text-align: center; color: var(--muted-foreground); padding: 1.5rem 0; }
}
</style>
