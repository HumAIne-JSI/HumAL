<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Progress from '@/components/ui/Progress.vue'
import Select from '@/components/ui/Select.vue'
import Checkbox from '@/components/ui/Checkbox.vue'
import InstanceSelector from '@/components/InstanceSelector.vue'
import MetricsChart from '@/components/MetricsChart.vue'
import {
  useInstances,
  useInstanceInfo,
  useNextInstances,
  useCreateInstance,
  useLabelInstance,
  useSaveModel,
  useDeleteInstance,
} from '@/composables/api/useActiveLearning'
import { useConfig } from '@/composables/api/useConfig'
import { useTeams, useTickets } from '@/composables/api/useData'
import type { NewInstanceRequest, Ticket } from '@/types/api'
import {
  Plus,
  Play,
  Save,
  Trash2,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Check,
  X,
  AlertCircle,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

// URL-synced instance ID
const selectedInstanceId = ref<number>(0)

// Initialize from route query
onMounted(() => {
  const instanceParam = route.query.instance
  if (instanceParam) {
    selectedInstanceId.value = Number(instanceParam)
  }
})

// Sync URL with instance selection
watch(selectedInstanceId, (newId) => {
  if (newId > 0) {
    router.replace({ query: { ...route.query, instance: String(newId) } })
  } else {
    const { instance: _, ...rest } = route.query
    router.replace({ query: rest })
  }
})

// Config data
const { models, strategies, isLoading: configLoading } = useConfig()

// Instance data
const { data: instancesData, refetch: refetchInstances } = useInstances()
const {
  data: instanceInfo,
  isLoading: instanceInfoLoading,
  refetch: refetchInstanceInfo,
} = useInstanceInfo(selectedInstanceId, {
  enabled: computed(() => selectedInstanceId.value > 0),
})

// Batch size for labeling
const batchSize = ref(5)

// Next instances to label
const {
  data: nextInstancesData,
  isLoading: nextInstancesLoading,
  refetch: refetchNextInstances,
} = useNextInstances(selectedInstanceId, batchSize, {
  enabled: computed(() => selectedInstanceId.value > 0),
})

// Get tickets data for the query indices
const queryIndices = computed(() => {
  const indices = nextInstancesData.value?.query_idx ?? []
  return indices.map(String)
})

const { data: ticketsData, isLoading: ticketsLoading } = useTickets(
  selectedInstanceId,
  queryIndices,
  undefined,
  {
    enabled: computed(() => queryIndices.value.length > 0),
  }
)

// Get teams for labeling options
const { data: teamsData } = useTeams(selectedInstanceId)

// Mutations
const createInstanceMutation = useCreateInstance({
  onSuccess: (data) => {
    toast.success('Instance created', {
      description: `Instance #${data.instance_id} created successfully`,
    })
    selectedInstanceId.value = data.instance_id
    refetchInstances()
    showCreateForm.value = false
  },
})

const labelInstanceMutation = useLabelInstance(selectedInstanceId, {
  onSuccess: () => {
    toast.success('Labels saved')
    refetchInstanceInfo()
    refetchNextInstances()
    clearSelections()
  },
})

const saveModelMutation = useSaveModel(selectedInstanceId, {
  onSuccess: () => {
    toast.success('Model saved', {
      description: 'The trained model has been saved successfully',
    })
    refetchInstanceInfo()
  },
})

const deleteInstanceMutation = useDeleteInstance({
  onSuccess: () => {
    toast.success('Instance deleted')
    selectedInstanceId.value = 0
    refetchInstances()
  },
})

// Form state for creating new instance
const showCreateForm = ref(false)
const newInstanceForm = ref<NewInstanceRequest>({
  model_name: '',
  qs_strategy: '',
  class_list: [],
  train_data_path: 'data/al_demo_train_data.csv',
  test_data_path: 'data/al_demo_test_data.csv',
})

// Teams for class list
const { data: teamsForNewInstance, refetch: loadTeamsForNewInstance } = useTeams(
  0,
  computed(() => newInstanceForm.value.train_data_path)
)

// Labeling state
const selectedLabels = ref<Record<string, string>>({})
const bulkLabel = ref('')

const tickets = computed<Ticket[]>(() => ticketsData.value?.tickets ?? [])

// Combined tickets with their query indices for proper iteration
const ticketsWithIndices = computed(() => {
  const indices = nextInstancesData.value?.query_idx ?? []
  return tickets.value
    .map((ticket, index) => ({
      ticket,
      queryIndex: indices[index],
    }))
    .filter((item): item is { ticket: Ticket; queryIndex: number | string } => item.queryIndex != null)
    .map((item) => ({
      ticket: item.ticket,
      queryIndex: String(item.queryIndex),
    }))
})

const labelOptions = computed(() =>
  (teamsData.value?.teams ?? []).map((team) => ({
    value: team,
    label: team,
  }))
)

// Selected labels count for reactivity
const selectedLabelsCount = computed(() => Object.keys(selectedLabels.value).length)

// Computed for instance info
const hasInstance = computed(() => selectedInstanceId.value > 0)

// Get instance metadata from the instances list (has model_name, qs)
const selectedInstanceMeta = computed(() => {
  if (!instancesData.value?.instances || selectedInstanceId.value <= 0) return null
  return instancesData.value.instances[String(selectedInstanceId.value)]
})

// Derive labeled_count from num_labeled array (last element is current count)
const labeledCount = computed(() => {
  const numLabeled = instanceInfo.value?.num_labeled
  if (numLabeled && numLabeled.length > 0) {
    return numLabeled[numLabeled.length - 1]
  }
  return 0
})

const isTraining = computed(() => instanceInfo.value && (instanceInfo.value.num_labeled?.length ?? 0) > 0)
const isTrained = computed(() => instanceInfo.value?.test_accuracy !== undefined || (instanceInfo.value?.f1_scores?.length ?? 0) > 0)
const progressPercent = computed(() => {
  // We don't have total_count from the API, so show percentage based on labeled count
  // If we have labeled data, show a meaningful percentage
  if (labeledCount.value > 0) {
    // Estimate based on typical dataset sizes or just show as "progress made"
    const total = instanceInfo.value?.total_count ?? selectedInstanceMeta.value?.total_count
    if (total) {
      return Math.round((labeledCount.value / total) * 100)
    }
    // Without total, just indicate some progress was made
    return Math.min(labeledCount.value, 100)
  }
  return 0
})

// Model options
const modelOptions = computed(() =>
  (models.value?.models ?? []).map((m) => ({ value: m, label: m }))
)

const strategyOptions = computed(() =>
  (strategies.value?.strategies ?? []).map((s) => ({ value: s, label: s }))
)

// Methods
const clearSelections = () => {
  selectedLabels.value = {}
  bulkLabel.value = ''
}

const getSelectedLabel = (index: string) => {
  return selectedLabels.value[index] ?? ''
}

const isLabelSelected = (index: string) => {
  return index in selectedLabels.value
}

const selectLabel = (index: string, label: string) => {
  selectedLabels.value = { ...selectedLabels.value, [index]: label }
}

const applyBulkLabel = () => {
  if (!bulkLabel.value) return
  const indices = nextInstancesData.value?.query_idx ?? []
  const newLabels: Record<string, string> = { ...selectedLabels.value }
  for (const idx of indices) {
    // Only add valid indices (not null/undefined)
    if (idx != null) {
      newLabels[String(idx)] = bulkLabel.value
    }
  }
  selectedLabels.value = newLabels
}

const submitLabels = () => {
  // Filter out entries with empty labels
  const validEntries = Object.entries(selectedLabels.value).filter(([key, label]) => {
    return key != null && key !== '' && label != null && label !== ''
  })

  if (validEntries.length === 0) {
    toast.error('No labels selected', {
      description: 'Please select labels for at least one ticket',
    })
    return
  }

  // Keep indices as strings if they're not purely numeric (e.g., "R-536988")
  // The API accepts both int and string for query_idx
  const indices = validEntries.map(([key]) => {
    const numKey = Number(key)
    return isNaN(numKey) ? key : numKey
  })
  const labels = validEntries.map(([, label]) => label)

  labelInstanceMutation.mutate({
    query_idx: indices,
    labels: labels,
  })
}

const createInstance = () => {
  if (!newInstanceForm.value.model_name || !newInstanceForm.value.qs_strategy) {
    toast.error('Missing required fields', {
      description: 'Please select a model and query strategy',
    })
    return
  }

  const classes = teamsForNewInstance.value?.teams ?? []
  if (classes.length === 0) {
    toast.error('No classes loaded', {
      description: 'Please load teams first',
    })
    return
  }

  createInstanceMutation.mutate({
    ...newInstanceForm.value,
    class_list: classes,
  })
}

const handleDeleteInstance = () => {
  if (confirm('Are you sure you want to delete this instance? This action cannot be undone.')) {
    deleteInstanceMutation.mutate(selectedInstanceId.value)
  }
}

// Handle instance selector update
const handleInstanceSelect = (value: string) => {
  selectedInstanceId.value = Number(value) || 0
}
</script>

<template>
  <div class="training">
    <header class="training__header">
      <div class="training__header-content">
        <h1 class="training__title">Training</h1>
        <p class="training__subtitle">Create and manage active learning instances</p>
      </div>
      <div class="training__header-actions">
        <InstanceSelector
          :model-value="String(selectedInstanceId || '')"
          placeholder="Select instance..."
          @update:model-value="handleInstanceSelect"
        />
        <Button variant="default" @click="showCreateForm = true">
          <Plus :size="16" />
          New Instance
        </Button>
      </div>
    </header>

    <!-- Create Instance Form -->
    <Card v-if="showCreateForm" class="training__create-form">
      <template #title>Create New Instance</template>
      <template #description>Configure a new active learning instance</template>
      <template #action>
        <Button variant="ghost" size="icon" @click="showCreateForm = false">
          <X :size="16" />
        </Button>
      </template>

      <div class="create-form">
        <div class="create-form__row">
          <div class="create-form__field">
            <label>Model</label>
            <Select
              v-model="newInstanceForm.model_name"
              :options="modelOptions"
              placeholder="Select model..."
              :disabled="configLoading"
            />
          </div>
          <div class="create-form__field">
            <label>Query Strategy</label>
            <Select
              v-model="newInstanceForm.qs_strategy"
              :options="strategyOptions"
              placeholder="Select strategy..."
              :disabled="configLoading"
            />
          </div>
        </div>

        <div class="create-form__row">
          <div class="create-form__field">
            <label>Training Data Path</label>
            <Input v-model="newInstanceForm.train_data_path" placeholder="data/train.csv" />
          </div>
          <div class="create-form__field">
            <label>Test Data Path</label>
            <Input v-model="newInstanceForm.test_data_path" placeholder="data/test.csv" />
          </div>
        </div>

        <div class="create-form__classes">
          <div class="create-form__classes-header">
            <label>Classes (Teams)</label>
            <Button
              variant="outline"
              size="sm"
              @click="loadTeamsForNewInstance"
              :loading="!teamsForNewInstance"
            >
              Load from Data
            </Button>
          </div>
          <div v-if="teamsForNewInstance?.teams?.length" class="create-form__classes-list">
            <Badge v-for="team in teamsForNewInstance.teams" :key="team" variant="secondary">
              {{ team }}
            </Badge>
          </div>
          <p v-else class="create-form__classes-empty">
            Click "Load from Data" to load available teams from the training data
          </p>
        </div>
      </div>

      <template #footer>
        <Button variant="outline" @click="showCreateForm = false">Cancel</Button>
        <Button
          @click="createInstance"
          :loading="createInstanceMutation.isPending.value"
          :disabled="!newInstanceForm.model_name || !newInstanceForm.qs_strategy || !teamsForNewInstance?.teams?.length"
        >
          <Plus :size="16" />
          Create Instance
        </Button>
      </template>
    </Card>

    <!-- No Instance Selected -->
    <div v-else-if="!hasInstance" class="training__empty">
      <AlertCircle :size="48" class="training__empty-icon" />
      <h3>No instance selected</h3>
      <p>Select an existing instance or create a new one to start training</p>
      <Button @click="showCreateForm = true">
        <Plus :size="16" />
        Create New Instance
      </Button>
    </div>

    <!-- Instance Dashboard -->
    <template v-else>
      <!-- Instance Info -->
      <Card class="training__info">
        <template #title>
          <div class="instance-info__header">
            <span>Instance #{{ selectedInstanceId }}</span>
            <Badge :variant="isTrained ? 'success' : 'secondary'">
              {{ isTrained ? 'Trained' : 'In Progress' }}
            </Badge>
          </div>
        </template>
        <template #description>
          {{ selectedInstanceMeta?.model_name ?? instanceInfo?.model_name ?? 'Loading...' }}
          • {{ selectedInstanceMeta?.qs ?? instanceInfo?.qs ?? 'N/A' }}
        </template>
        <template #action>
          <div class="instance-info__actions">
            <Button
              variant="outline"
              size="sm"
              @click="refetchInstanceInfo"
              :loading="instanceInfoLoading"
            >
              <RefreshCw :size="14" />
            </Button>
            <Button
              variant="success"
              size="sm"
              @click="saveModelMutation.mutate(undefined)"
              :loading="saveModelMutation.isPending.value"
              :disabled="labeledCount === 0"
            >
              <Save :size="14" />
              Save Model
            </Button>
            <Button
              variant="destructive"
              size="sm"
              @click="handleDeleteInstance"
              :loading="deleteInstanceMutation.isPending.value"
            >
              <Trash2 :size="14" />
            </Button>
          </div>
        </template>

        <div class="instance-info__content">
          <div class="instance-info__progress">
            <div class="instance-info__progress-header">
              <span>Labeling Progress</span>
              <span>
                {{ labeledCount }} labeled
              </span>
            </div>
            <Progress
              :value="progressPercent"
              :max="100"
              :color="progressPercent >= 80 ? 'success' : progressPercent >= 50 ? 'warning' : 'default'"
            />
          </div>

          <div class="instance-info__metrics">
            <div v-if="instanceInfo?.f1_scores?.length" class="instance-info__metric">
              <span class="instance-info__metric-label">Latest F1 Score</span>
              <Badge variant="info">
                {{ (instanceInfo.f1_scores[instanceInfo.f1_scores.length - 1] * 100).toFixed(1) }}%
              </Badge>
            </div>
            <div v-if="labeledCount > 0" class="instance-info__metric">
              <span class="instance-info__metric-label">Iterations</span>
              <Badge variant="secondary">
                {{ instanceInfo?.num_labeled?.length ?? 0 }}
              </Badge>
            </div>
          </div>

          <!-- F1 Score Chart -->
          <div v-if="instanceInfo?.f1_scores?.length" class="instance-info__chart">
            <h4>F1 Score History</h4>
            <MetricsChart :scores="instanceInfo.f1_scores" label="F1 Score" :height="200" />
          </div>
        </div>
      </Card>

      <!-- Labeling Section -->
      <Card class="training__labeling">
        <template #title>Label Tickets</template>
        <template #description>
          Select labels for the following tickets suggested by the active learning algorithm
        </template>
        <template #action>
          <div class="labeling__controls">
            <div class="labeling__batch-size">
              <label>Batch size:</label>
              <Input
                v-model.number="batchSize"
                type="number"
                :min="1"
                :max="20"
                style="width: 80px"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              @click="refetchNextInstances"
              :loading="nextInstancesLoading"
            >
              <RefreshCw :size="14" />
              Refresh
            </Button>
          </div>
        </template>

        <div class="labeling__content">
          <!-- Bulk label -->
          <div class="labeling__bulk">
            <Select
              v-model="bulkLabel"
              :options="labelOptions"
              placeholder="Apply label to all..."
              size="sm"
            />
            <Button variant="secondary" size="sm" @click="applyBulkLabel" :disabled="!bulkLabel">
              Apply to All
            </Button>
          </div>

          <!-- Loading state -->
          <div v-if="nextInstancesLoading || ticketsLoading" class="labeling__loading">
            Loading tickets...
          </div>

          <!-- No tickets -->
          <div v-else-if="tickets.length === 0" class="labeling__empty">
            <Check :size="32" />
            <p>No more tickets to label at this time</p>
          </div>

          <!-- Tickets list -->
          <div v-else class="labeling__tickets">
            <Card
              v-for="({ ticket, queryIndex }, idx) in ticketsWithIndices"
              :key="`${queryIndex}-${ticket.Ref || idx}`"
              variant="outline"
              padding="sm"
              class="labeling__ticket"
              :class="{ 'labeling__ticket--labeled': isLabelSelected(queryIndex) }"
            >
              <template #title>
                <div class="labeling__ticket-header">
                  <Badge variant="outline">#{{ queryIndex }}</Badge>
                  <span class="labeling__ticket-ref">{{ ticket.Ref }}</span>
                </div>
              </template>

              <div class="labeling__ticket-content">
                <div class="labeling__ticket-field">
                  <strong>Title:</strong>
                  <span>{{ ticket.Title_anon || 'N/A' }}</span>
                </div>
                <div class="labeling__ticket-field">
                  <strong>Description:</strong>
                  <span class="labeling__ticket-description">
                    {{ ticket.Description_anon || 'N/A' }}
                  </span>
                </div>
                <div v-if="ticket['Service->Name']" class="labeling__ticket-field">
                  <strong>Service:</strong>
                  <Badge variant="secondary">{{ ticket['Service->Name'] }}</Badge>
                </div>
              </div>

              <template #footer>
                <div class="labeling__ticket-actions">
                  <Select
                    :model-value="getSelectedLabel(queryIndex)"
                    :options="labelOptions"
                    placeholder="Select label..."
                    size="sm"
                    @update:model-value="selectLabel(queryIndex, $event)"
                  />
                  <Badge
                    v-if="isLabelSelected(queryIndex)"
                    variant="success"
                  >
                    <Check :size="12" />
                  </Badge>
                </div>
              </template>
            </Card>
          </div>
        </div>

        <template #footer>
          <div class="labeling__footer">
            <span class="labeling__count">
              {{ selectedLabelsCount }} of {{ tickets.length }} labeled
            </span>
            <div class="labeling__footer-actions">
              <Button variant="outline" @click="clearSelections" :disabled="selectedLabelsCount === 0">
                Clear
              </Button>
              <Button
                @click="submitLabels"
                :loading="labelInstanceMutation.isPending.value"
                :disabled="selectedLabelsCount === 0"
              >
                <Save :size="16" />
                Submit Labels
              </Button>
            </div>
          </div>
        </template>
      </Card>
    </template>
  </div>
</template>

<style scoped lang="scss">
.training {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    gap: 1rem;
    flex-wrap: wrap;
  }

  &__header-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__title {
    font-size: 1.875rem;
    font-weight: 700;
    margin: 0;
  }

  &__subtitle {
    color: var(--muted-foreground);
    margin: 0;
  }

  &__header-actions {
    display: flex;
    gap: 0.75rem;
    align-items: center;
  }

  &__create-form {
    margin-bottom: 1.5rem;
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
    }

    p {
      margin: 0 0 1.5rem;
      color: var(--muted-foreground);
    }
  }

  &__empty-icon {
    color: var(--muted-foreground);
  }

  &__info {
    margin-bottom: 1.5rem;
  }

  &__labeling {
    margin-bottom: 1.5rem;
  }
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;

  &__row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;

    @media (max-width: 640px) {
      grid-template-columns: 1fr;
    }
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;

    label {
      font-size: 0.875rem;
      font-weight: 500;
    }
  }

  &__classes {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__classes-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    label {
      font-size: 0.875rem;
      font-weight: 500;
    }
  }

  &__classes-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--muted);
    border-radius: var(--radius);
    max-height: 150px;
    overflow-y: auto;
  }

  &__classes-empty {
    font-size: 0.875rem;
    color: var(--muted-foreground);
    padding: 0.75rem;
    background: var(--muted);
    border-radius: var(--radius);
    margin: 0;
  }
}

.instance-info {
  &__header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  &__actions {
    display: flex;
    gap: 0.5rem;
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    margin-top: 1rem;
  }

  &__progress {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__progress-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.875rem;
  }

  &__metrics {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
  }

  &__metric {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__metric-label {
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }

  &__chart {
    margin-top: 0.5rem;

    h4 {
      font-size: 0.875rem;
      font-weight: 500;
      margin: 0 0 0.75rem;
    }
  }
}

.labeling {
  &__controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  &__batch-size {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-top: 1rem;
  }

  &__bulk {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    padding: 0.75rem;
    background: var(--muted);
    border-radius: var(--radius);
  }

  &__loading {
    text-align: center;
    padding: 2rem;
    color: var(--muted-foreground);
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 2rem;
    color: var(--muted-foreground);
  }

  &__tickets {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__ticket {
    transition: border-color 0.15s ease;

    &--labeled {
      border-color: var(--success);
    }
  }

  &__ticket-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  &__ticket-ref {
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }

  &__ticket-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin: 0.75rem 0;
  }

  &__ticket-field {
    display: flex;
    gap: 0.5rem;
    font-size: 0.875rem;

    strong {
      flex-shrink: 0;
      width: 80px;
      color: var(--muted-foreground);
    }
  }

  &__ticket-description {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__ticket-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
  }

  &__footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }

  &__count {
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }

  &__footer-actions {
    display: flex;
    gap: 0.5rem;
  }
}
</style>
