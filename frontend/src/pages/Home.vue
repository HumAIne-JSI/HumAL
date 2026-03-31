<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'
import Button from '@/components/ui/Button.vue'
import { useInstances } from '@/composables/api/useActiveLearning'
import { useConfig } from '@/composables/api/useConfig'
import { apiService } from '@/services/api'
import { ref, onMounted } from 'vue'
import {
  Brain,
  Target,
  MessageSquareText,
  Zap,
  Plus,
  ChevronRight,
  Server,
  RefreshCw,
  Activity,
} from 'lucide-vue-next'

const router = useRouter()

// API base URL from environment
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// API health check
const apiStatus = ref<'checking' | 'connected' | 'error'>('checking')

const checkApiHealth = async () => {
  apiStatus.value = 'checking'
  try {
    await apiService.getModels()
    apiStatus.value = 'connected'
  } catch {
    apiStatus.value = 'error'
  }
}

onMounted(() => {
  checkApiHealth()
})

// Fetch data
const { data: instancesData, isLoading: instancesLoading, refetch: refetchInstances } = useInstances()
const { models, strategies, isLoading: configLoading } = useConfig()

// Computed values
const instancesList = computed(() => {
  const instances = instancesData.value?.instances ?? {}
  return Object.entries(instances).map(([id, info]) => ({
    id: Number(id),
    ...info,
  }))
})

const totalInstances = computed(() => instancesList.value.length)
const trainedInstances = computed(
  () => instancesList.value.filter((i) => i.test_accuracy !== undefined).length
)
const availableModels = computed(() => models.value?.models?.length ?? 0)
const availableStrategies = computed(() => strategies.value?.strategies?.length ?? 0)

// Navigation
const navigateTo = (path: string, query?: Record<string, string>) => {
  router.push({ path, query })
}
</script>

<template>
  <div class="dashboard">
    <header class="dashboard__header">
      <div class="dashboard__header-content">
        <h1 class="dashboard__title">Dashboard</h1>
        <p class="dashboard__subtitle">
          Welcome to HumAL - Human-in-the-Loop Active Learning Platform
        </p>
      </div>
      <Button variant="outline" size="sm" @click="refetchInstances">
        <RefreshCw :size="14" />
        Refresh
      </Button>
    </header>

    <!-- System Status -->
    <section class="dashboard__section">
      <h2 class="dashboard__section-title">
        <Server :size="18" />
        System Status
      </h2>

      <div class="dashboard__stats-grid">
        <Card variant="outline" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--api">
              <Activity :size="20" />
            </div>
            <div class="stat-card__content">
              <span class="stat-card__label">API Status</span>
              <div class="stat-card__value-row">
                <Badge
                  :variant="
                    apiStatus === 'connected'
                      ? 'success'
                      : apiStatus === 'error'
                        ? 'destructive'
                        : 'warning'
                  "
                >
                  {{
                    apiStatus === 'connected'
                      ? 'Connected'
                      : apiStatus === 'error'
                        ? 'Disconnected'
                        : 'Checking...'
                  }}
                </Badge>
              </div>
            </div>
          </div>
          <template #footer>
            <span class="stat-card__footer">{{ apiBaseUrl }}</span>
          </template>
        </Card>

        <Card variant="outline" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--instances">
              <Brain :size="20" />
            </div>
            <div class="stat-card__content">
              <span class="stat-card__label">Active Instances</span>
              <span class="stat-card__value">
                {{ instancesLoading ? '...' : totalInstances }}
              </span>
            </div>
          </div>
          <template #footer>
            <span class="stat-card__footer">{{ trainedInstances }} trained</span>
          </template>
        </Card>

        <Card variant="outline" padding="sm">
          <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--models">
              <Target :size="20" />
            </div>
            <div class="stat-card__content">
              <span class="stat-card__label">Available Models</span>
              <span class="stat-card__value">
                {{ configLoading ? '...' : availableModels }}
              </span>
            </div>
          </div>
          <template #footer>
            <span class="stat-card__footer">{{ availableStrategies }} strategies</span>
          </template>
        </Card>
      </div>
    </section>

    <!-- Quick Actions -->
    <section class="dashboard__section">
      <h2 class="dashboard__section-title">
        <Zap :size="18" />
        Quick Actions
      </h2>

      <div class="dashboard__actions-grid">
        <Card
          variant="elevated"
          padding="default"
          class="action-card action-card--training"
          @click="navigateTo('/training')"
        >
          <div class="action-card__content">
            <div class="action-card__icon">
              <Brain :size="28" />
            </div>
            <div class="action-card__text">
              <h3 class="action-card__title">Training</h3>
              <p class="action-card__description">
                Create and manage active learning instances, label data, and train models
              </p>
            </div>
            <ChevronRight :size="20" class="action-card__arrow" />
          </div>
        </Card>

        <Card
          variant="elevated"
          padding="default"
          class="action-card action-card--inference"
          @click="navigateTo('/inference')"
        >
          <div class="action-card__content">
            <div class="action-card__icon">
              <Zap :size="28" />
            </div>
            <div class="action-card__text">
              <h3 class="action-card__title">Batch Inference</h3>
              <p class="action-card__description">
                Run predictions on multiple tickets with trained models
              </p>
            </div>
            <ChevronRight :size="20" class="action-card__arrow" />
          </div>
        </Card>

        <Card
          variant="elevated"
          padding="default"
          class="action-card action-card--dispatching"
          @click="navigateTo('/dispatching')"
        >
          <div class="action-card__content">
            <div class="action-card__icon">
              <Target :size="28" />
            </div>
            <div class="action-card__text">
              <h3 class="action-card__title">Dispatching</h3>
              <p class="action-card__description">
                Classify tickets with explainable AI insights and similar ticket lookup
              </p>
            </div>
            <ChevronRight :size="20" class="action-card__arrow" />
          </div>
        </Card>

        <Card
          variant="elevated"
          padding="default"
          class="action-card action-card--resolution"
          @click="navigateTo('/ticket-resolution')"
        >
          <div class="action-card__content">
            <div class="action-card__icon">
              <MessageSquareText :size="28" />
            </div>
            <div class="action-card__text">
              <h3 class="action-card__title">Ticket Resolution</h3>
              <p class="action-card__description">
                Get AI-powered resolution suggestions using RAG-based retrieval
              </p>
            </div>
            <ChevronRight :size="20" class="action-card__arrow" />
          </div>
        </Card>
      </div>
    </section>

    <!-- Instances Overview -->
    <section class="dashboard__section">
      <div class="dashboard__section-header">
        <h2 class="dashboard__section-title">
          <Brain :size="18" />
          Training Instances
        </h2>
        <Button variant="default" size="sm" @click="navigateTo('/training')">
          <Plus :size="14" />
          New Instance
        </Button>
      </div>

      <div v-if="instancesLoading" class="dashboard__loading">Loading instances...</div>

      <div v-else-if="instancesList.length === 0" class="dashboard__empty">
        <Brain :size="48" class="dashboard__empty-icon" />
        <h3>No instances yet</h3>
        <p>Create your first active learning instance to get started</p>
        <Button @click="navigateTo('/training')">
          <Plus :size="16" />
          Create Instance
        </Button>
      </div>

      <div v-else class="dashboard__instances-grid">
        <Card
          v-for="instance in instancesList"
          :key="instance.id"
          variant="outline"
          padding="default"
          class="instance-card"
          @click="navigateTo('/training', { instance: String(instance.id) })"
        >
          <template #title>
            <div class="instance-card__header">
              <span class="instance-card__id">#{{ instance.id }}</span>
              <Badge
                :variant="instance.test_accuracy !== undefined ? 'success' : 'secondary'"
                class="instance-card__status"
              >
                {{ instance.test_accuracy !== undefined ? 'Trained' : 'In Progress' }}
              </Badge>
            </div>
          </template>

          <template #description>
            {{ instance.model_name ?? instance.model ?? 'Unknown Model' }}
            <span class="instance-card__strategy">• {{ instance.qs ?? 'N/A' }}</span>
          </template>

          <div class="instance-card__content">
            <div class="instance-card__progress">
              <div class="instance-card__progress-header">
                <span>Labeled</span>
                <span>
                  {{ instance.labeled_count ?? 0 }} / {{ instance.total_count ?? 0 }}
                </span>
              </div>
              <Progress
                :value="instance.labeled_count ?? 0"
                :max="instance.total_count ?? 1"
                color="default"
              />
            </div>

            <div v-if="instance.f1_scores && instance.f1_scores.length > 0" class="instance-card__metrics">
              <span class="instance-card__metric-label">Latest F1</span>
              <Badge variant="info">
                {{ ((instance.f1_scores[instance.f1_scores.length - 1] ?? 0) * 100).toFixed(1) }}%
              </Badge>
            </div>

            <div v-if="instance.test_accuracy !== undefined" class="instance-card__metrics">
              <span class="instance-card__metric-label">Test Accuracy</span>
              <Badge variant="success">
                {{ (instance.test_accuracy * 100).toFixed(1) }}%
              </Badge>
            </div>
          </div>

          <template #footer>
            <Button variant="ghost" size="sm" class="instance-card__action">
              Open
              <ChevronRight :size="14" />
            </Button>
          </template>
        </Card>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
  }

  &__header-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__title {
    font-size: 1.875rem;
    font-weight: 700;
    color: var(--foreground);
    margin: 0;
  }

  &__subtitle {
    color: var(--muted-foreground);
    margin: 0;
  }

  &__section {
    margin-bottom: 2.5rem;
  }

  &__section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  &__section-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--foreground);
    margin: 0 0 1rem;
  }

  &__stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
  }

  &__actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  &__instances-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
  }

  &__loading {
    text-align: center;
    padding: 3rem;
    color: var(--muted-foreground);
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    background: var(--muted);
    border-radius: var(--radius);

    h3 {
      margin: 1rem 0 0.5rem;
      font-size: 1.125rem;
    }

    p {
      margin: 0 0 1.5rem;
      color: var(--muted-foreground);
    }
  }

  &__empty-icon {
    color: var(--muted-foreground);
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;

  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius);

    &--api {
      background: color-mix(in oklch, var(--success) 15%, transparent);
      color: var(--success);
    }

    &--instances {
      background: color-mix(in oklch, var(--primary) 15%, transparent);
      color: var(--primary);
    }

    &--models {
      background: color-mix(in oklch, var(--info) 15%, transparent);
      color: var(--info);
    }
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__label {
    font-size: 0.75rem;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &__value {
    font-size: 1.5rem;
    font-weight: 700;
  }

  &__value-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__footer {
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }
}

.action-card {
  cursor: pointer;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow:
      0 4px 12px rgba(0, 0, 0, 0.1),
      0 2px 4px rgba(0, 0, 0, 0.06);
  }

  &__content {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: var(--radius);
    flex-shrink: 0;
  }

  &--training &__icon {
    background: color-mix(in oklch, var(--primary) 15%, transparent);
    color: var(--primary);
  }

  &--inference &__icon {
    background: color-mix(in oklch, var(--success) 15%, transparent);
    color: var(--success);
  }

  &--dispatching &__icon {
    background: color-mix(in oklch, var(--warning) 15%, transparent);
    color: var(--warning);
  }

  &--resolution &__icon {
    background: color-mix(in oklch, var(--info) 15%, transparent);
    color: var(--info);
  }

  &__text {
    flex: 1;
    min-width: 0;
  }

  &__title {
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 0.25rem;
  }

  &__description {
    font-size: 0.875rem;
    color: var(--muted-foreground);
    margin: 0;
    line-height: 1.4;
  }

  &__arrow {
    color: var(--muted-foreground);
    flex-shrink: 0;
  }
}

.instance-card {
  cursor: pointer;
  transition:
    transform 0.15s ease,
    border-color 0.15s ease;

  &:hover {
    border-color: var(--primary);
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  &__id {
    font-weight: 600;
  }

  &__status {
    font-size: 0.75rem;
  }

  &__strategy {
    color: var(--muted-foreground);
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  &__progress {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  &__progress-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__metrics {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  &__metric-label {
    color: var(--muted-foreground);
  }

  &__action {
    margin-left: auto;
  }
}
</style>
