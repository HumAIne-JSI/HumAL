<script setup lang="ts">
import { ref, computed } from 'vue'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Checkbox from '@/components/ui/Checkbox.vue'
import MetricsChart from '@/components/MetricsChart.vue'
import DecisionTimeline from '@/components/DecisionTimeline.vue'
import SessionCard from '@/components/SessionCard.vue'
import {
  useAnalyticsOverview,
  useSessions,
  useSessionDecisions,
  useSessionLabeling,
  useSessionPerformance,
  useSessionDistribution,
  useSampleData,
  setUseSampleData,
} from '@/composables/api/useAnalytics'
import type { SessionSummary, Decision } from '@/types/api'
import {
  BarChart3,
  Activity,
  Tag,
  Clock,
  TrendingUp,
  Target,
  Users,
  Layers,
  Download,
  RefreshCw,
  ChevronRight,
  Info,
} from 'lucide-vue-next'

// Sample data toggle
const sampleDataEnabled = computed({
  get: () => useSampleData.value,
  set: (val: boolean) => setUseSampleData(val),
})

// Selected session for detail view
const selectedSessionId = ref<string>('')

// Data fetching
const { data: overview, isLoading: overviewLoading } = useAnalyticsOverview()
const { data: sessions, isLoading: sessionsLoading } = useSessions()

// Session detail data (only fetched when session selected)
const sessionDetailEnabled = computed(() => !!selectedSessionId.value)

const { data: sessionDecisions, isLoading: decisionsLoading } = useSessionDecisions(
  selectedSessionId,
  { enabled: sessionDetailEnabled }
)
const { data: sessionLabeling, isLoading: labelingLoading } = useSessionLabeling(
  selectedSessionId,
  { enabled: sessionDetailEnabled }
)
const { data: sessionPerformance, isLoading: performanceLoading } = useSessionPerformance(
  selectedSessionId,
  { enabled: sessionDetailEnabled }
)
const { data: sessionDistribution, isLoading: distributionLoading } = useSessionDistribution(
  selectedSessionId,
  { enabled: sessionDetailEnabled }
)

// Selected session summary
const selectedSession = computed(() => {
  if (!selectedSessionId.value || !sessions.value) return null
  return sessions.value.find(s => s.session_id === selectedSessionId.value) ?? null
})

// Loading state
const isLoading = computed(() => overviewLoading.value || sessionsLoading.value)
const isDetailLoading = computed(() => 
  decisionsLoading.value || labelingLoading.value || performanceLoading.value || distributionLoading.value
)

// Handle session selection
function selectSession(session: SessionSummary) {
  selectedSessionId.value = session.session_id
}

// Handle decision click
function handleDecisionSelect(decision: Decision) {
  toast.info(`Decision at t=${decision.t}s`, {
    description: `${decision.action}: ${JSON.stringify(decision.payload).slice(0, 100)}...`,
  })
}

// Clear selection
function clearSelection() {
  selectedSessionId.value = ''
}

// Format number with locale
function formatNumber(num: number | undefined): string {
  if (num === undefined) return 'N/A'
  return num.toLocaleString()
}

// Format percentage
function formatPercent(num: number | undefined): string {
  if (num === undefined) return 'N/A'
  return `${(num * 100).toFixed(1)}%`
}

// Export session data
function exportSession() {
  if (!sessionDecisions.value) return
  
  const data = JSON.stringify(sessionDecisions.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `session_${selectedSessionId.value}.json`
  link.click()
  URL.revokeObjectURL(url)
  
  toast.success('Session exported', {
    description: `Downloaded session_${selectedSessionId.value}.json`,
  })
}
</script>

<template>
  <div class="analytics">
    <!-- Header -->
    <header class="analytics__header">
      <div class="analytics__header-content">
        <h1 class="analytics__title">
          <BarChart3 class="w-8 h-8" />
          Analytics
        </h1>
        <p class="analytics__subtitle">Session logs, metrics, and performance insights</p>
      </div>
      <div class="analytics__header-actions">
        <label class="sample-toggle">
          <Checkbox v-model="sampleDataEnabled" />
          <span>Sample Data</span>
        </label>
        <Button
          v-if="selectedSessionId"
          variant="outline"
          size="sm"
          @click="exportSession"
        >
          <Download class="w-4 h-4" />
          Export
        </Button>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="isLoading" class="analytics__loading">
      <RefreshCw class="w-6 h-6 animate-spin" />
      <span>Loading analytics...</span>
    </div>

    <template v-else>
      <!-- Overview Cards -->
      <section class="analytics__overview">
        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--primary">
              <Layers class="w-5 h-5" />
            </div>
            <div class="stat-card__content">
              <span class="stat-card__label">Sessions</span>
              <span class="stat-card__value">{{ formatNumber(overview?.total_sessions) }}</span>
            </div>
          </div>
        </Card>

        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--success">
              <Tag class="w-5 h-5" />
            </div>
            <div class="stat-card__content">
              <span class="stat-card__label">Total Labels</span>
              <span class="stat-card__value">{{ formatNumber(overview?.total_labels) }}</span>
            </div>
          </div>
        </Card>

        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--info">
              <TrendingUp class="w-5 h-5" />
            </div>
            <div class="stat-card__content">
              <span class="stat-card__label">Avg F1 Score</span>
              <span class="stat-card__value">{{ formatPercent(overview?.avg_f1_score) }}</span>
            </div>
          </div>
        </Card>

        <Card variant="elevated" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--warning">
              <Target class="w-5 h-5" />
            </div>
            <div class="stat-card__content">
              <span class="stat-card__label">Best Strategy</span>
              <span class="stat-card__value stat-card__value--small">
                {{ overview?.most_efficient_strategy ?? 'N/A' }}
              </span>
            </div>
          </div>
        </Card>
      </section>

      <!-- Main Content -->
      <div class="analytics__content">
        <!-- Sessions List -->
        <section class="analytics__sessions">
          <h2 class="section-title">Sessions</h2>
          <div v-if="sessions?.length" class="sessions-grid">
            <SessionCard
              v-for="session in sessions"
              :key="session.session_id"
              :session="session"
              :selected="session.session_id === selectedSessionId"
              @select="selectSession"
            />
          </div>
          <div v-else class="analytics__empty">
            <Info class="w-8 h-8 text-muted-foreground" />
            <p>No sessions found</p>
          </div>
        </section>

        <!-- Session Detail -->
        <section v-if="selectedSession" class="analytics__detail">
          <div class="detail-header">
            <h2 class="section-title">
              Session Details
              <Badge variant="outline" class="ml-2">{{ selectedSessionId }}</Badge>
            </h2>
            <Button variant="ghost" size="sm" @click="clearSelection">
              Clear
            </Button>
          </div>

          <!-- Loading detail -->
          <div v-if="isDetailLoading" class="detail-loading">
            <RefreshCw class="w-5 h-5 animate-spin" />
            <span>Loading session details...</span>
          </div>

          <template v-else>
            <!-- Metrics Row -->
            <div class="detail-metrics">
              <Card padding="sm">
                <template #title>Labeling Metrics</template>
                <div class="metrics-grid">
                  <div class="metric-item">
                    <span class="metric-item__label">Total Labels</span>
                    <span class="metric-item__value">{{ sessionLabeling?.total_labels }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-item__label">Avg Duration</span>
                    <span class="metric-item__value">{{ sessionLabeling?.avg_duration_per_label_s?.toFixed(1) }}s</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-item__label">Throughput</span>
                    <span class="metric-item__value">{{ sessionLabeling?.throughput_per_hour?.toFixed(0) }}/hr</span>
                  </div>
                </div>
              </Card>

              <Card padding="sm">
                <template #title>Class Distribution</template>
                <div class="distribution-bars">
                  <div
                    v-for="(count, className) in sessionDistribution?.class_counts"
                    :key="String(className)"
                    class="distribution-bar"
                  >
                    <div class="distribution-bar__header">
                      <span class="distribution-bar__label">{{ className }}</span>
                      <span class="distribution-bar__count">{{ count }}</span>
                    </div>
                    <div class="distribution-bar__track">
                      <div
                        class="distribution-bar__fill"
                        :style="{ width: `${sessionDistribution?.class_percentages?.[String(className)] ?? 0}%` }"
                      ></div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <!-- Performance Chart -->
            <Card v-if="sessionPerformance?.f1_scores?.length" padding="default">
              <template #title>Model Performance</template>
              <template #description>F1 score progression over training iterations</template>
              <MetricsChart
                :scores="sessionPerformance.f1_scores"
                label="F1 Score"
                :height="200"
              />
            </Card>

            <!-- Decision Timeline -->
            <Card v-if="sessionDecisions?.decisions?.length" padding="default">
              <template #title>Decision Timeline</template>
              <template #description>
                {{ sessionDecisions.decisions.length }} events in this session
              </template>
              <DecisionTimeline
                :decisions="sessionDecisions.decisions"
                :show-payload="true"
                @select="handleDecisionSelect"
              />
            </Card>
          </template>
        </section>

        <!-- No Session Selected -->
        <section v-else class="analytics__no-selection">
          <div class="no-selection-content">
            <ChevronRight class="w-8 h-8 text-muted-foreground" />
            <p>Select a session to view details</p>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.analytics {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.analytics__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.analytics__header-content {
  flex: 1;
  min-width: 200px;
}

.analytics__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--foreground);
  margin: 0;
}

.analytics__subtitle {
  color: var(--muted-foreground);
  margin: 0.25rem 0 0;
}

.analytics__header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sample-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--muted-foreground);
  cursor: pointer;

  &:hover {
    color: var(--foreground);
  }
}

.analytics__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem;
  color: var(--muted-foreground);
}

.analytics__overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.stat-card__icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;

  &--primary {
    background-color: hsl(221, 83%, 53%);
  }

  &--success {
    background-color: hsl(142, 76%, 36%);
  }

  &--info {
    background-color: hsl(199, 89%, 48%);
  }

  &--warning {
    background-color: hsl(38, 92%, 50%);
  }
}

.stat-card__content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.stat-card__label {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.stat-card__value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;

  &--small {
    font-size: 1rem;
  }
}

.analytics__content {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.5rem;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.analytics__sessions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--foreground);
  margin: 0 0 0.5rem;
  display: flex;
  align-items: center;
}

.sessions-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.analytics__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--muted-foreground);
  text-align: center;
}

.analytics__detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--muted-foreground);
}

.detail-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.metric-item__label {
  font-size: 0.7rem;
  color: var(--muted-foreground);
  text-transform: uppercase;
}

.metric-item__value {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--foreground);
}

.distribution-bars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.distribution-bar__header {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
}

.distribution-bar__label {
  font-weight: 500;
}

.distribution-bar__count {
  color: var(--muted-foreground);
}

.distribution-bar__track {
  height: 0.375rem;
  background-color: var(--muted);
  border-radius: 9999px;
  overflow: hidden;
}

.distribution-bar__fill {
  height: 100%;
  background-color: var(--primary);
  border-radius: 9999px;
  transition: width 0.3s ease;
}

.analytics__no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.no-selection-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--muted-foreground);
}
</style>
