<script setup lang="ts">
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import { useCreateInstance } from '@/composables/api/useActiveLearning'
import { useConfig } from '@/composables/api/useConfig'
import { useTeams } from '@/composables/api/useData'
import { useInstanceStore } from '@/stores/useInstanceStore'
import { useBenchmarkTelemetry } from '@/composables/useBenchmarkTelemetry'
import type { NewInstanceRequest } from '@/types/api'
import { Plus, RefreshCw, X } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'

const router = useRouter()
const instanceStore = useInstanceStore()
const telemetry = useBenchmarkTelemetry()

const { models, strategies, isLoading: configLoading } = useConfig()

const newInstanceForm = ref<NewInstanceRequest>({
  model_name: '',
  qs_strategy: '',
  class_list: [],
  train_data_path: 'data/al_demo_train_data.csv',
  test_data_path: 'data/al_demo_test_data.csv',
})

const teamsForNewInstanceEnabled = ref(false)
const {
  data: teamsForNewInstance,
  isFetching: teamsForNewInstanceLoading,
  isError: teamsForNewInstanceError,
  refetch: refetchTeamsForNewInstance,
} = useTeams(
  0,
  computed(() => newInstanceForm.value.train_data_path),
  { enabled: teamsForNewInstanceEnabled },
)
const loadTeamsForNewInstance = () => {
  teamsForNewInstanceEnabled.value = true
  refetchTeamsForNewInstance()
}

const manualClasses = ref<string[]>([])
const manualClassInput = ref('')

const KNOWN_TEAMS = [
  '(BF) Employee Platform (SAP SF)',
  '(BF) Information Security Office',
  '(CF) Client Compliance',
  '(GI-CF) Robot Process Automation',
  '(GI-CF) Security & RPA',
  '(GI-CyberSec) Cybersecurity',
  '(GI-CyberSec) Security Operation Center',
  '(GI-IaaS) Admin - IT Purchase Problem Management',
  '(GI-IaaS) Admin - License & Asset Management',
  '(GI-IaaS) Admin - Local IT purchase',
  '(GI-IaaS) Azure Data Center',
  '(GI-IaaS) Backend Application Srv. & Project Support',
  '(GI-IaaS) Backend M365 (2nd level)',
  '(GI-IaaS) Backend System Management (2nd level)',
  '(GI-IaaS) Cloud Services',
  '(GI-IaaS) Development Platform',
  '(GI-IaaS) Network Cloud (Azure, Remote Access)',
  '(GI-IaaS) Network On-Prem (LAN,WLAN,WAN 2nd level)',
  '(GI-SaaS) BI & SuccessFactors',
  '(GI-SaaS) Marketing, Communications & Web',
  '(GI-SaaS) SAP & Synertrade',
  '(GI-SaaS) Salesforce',
  '(GI-SM) PMS',
  '(GI-SM) Service Desk',
  '(GI-UX) Account Management',
  '(GI-UX) Application',
  '(GI-UX) File & Print',
  '(GI-UX) Group',
  '(GI-UX) MAC OS',
  '(GI-UX) Mobile Device Management',
  '(GI-UX) Network Access',
  '(GI-UX) Office365 & MS-Teams',
  '(GI-UX) System Management & Anti Virus',
  '(GI-UX) Unified Communication',
  '(GI-UX) Windows',
  '(LF) Facilities Iberia',
  '(LF) IT Office Access Italy',
  '{GI-SM} Team Communication',
]

const loadKnownTeams = () => {
  manualClasses.value = [
    ...manualClasses.value,
    ...KNOWN_TEAMS.filter((t) => !manualClasses.value.includes(t)),
  ]
}

const addManualClass = () => {
  const name = manualClassInput.value.trim()
  if (name && !manualClasses.value.includes(name) && !allClasses.value.includes(name)) {
    manualClasses.value = [...manualClasses.value, name]
  }
  manualClassInput.value = ''
}
const removeManualClass = (name: string) => {
  manualClasses.value = manualClasses.value.filter((c) => c !== name)
}

const allClasses = computed(() => {
  const loaded = teamsForNewInstance.value?.teams ?? []
  return [...new Set([...loaded, ...manualClasses.value])]
})

const modelOptions = computed(() =>
  (models.value?.models ?? []).map((m) => ({ value: m, label: m })),
)

const strategyOptions = computed(() =>
  (strategies.value?.strategies ?? []).map((s) => ({ value: s, label: s })),
)

const createInstanceMutation = useCreateInstance({
  onSuccess: (data) => {
    toast.success('Instance created', {
      description: `Instance #${data.instance_id} created successfully`,
    })
    instanceStore.setInstance(data.instance_id)
    router.push({ path: '/queue', query: { instance: String(data.instance_id) } })
  },
})

const createInstance = () => {
  if (!newInstanceForm.value.model_name || !newInstanceForm.value.qs_strategy) {
    toast.error('Missing required fields', {
      description: 'Please select a model and query strategy',
    })
    return
  }
  if (allClasses.value.length === 0) {
    toast.error('No classes loaded', {
      description: 'Please load teams from data or add them manually',
    })
    return
  }
  telemetry.recordLab('create_instance', 'Mdl', {
    page: 'new_instance',
    model_name: newInstanceForm.value.model_name,
    qs_strategy: newInstanceForm.value.qs_strategy,
    class_count: allClasses.value.length,
  })
  createInstanceMutation.mutate({
    ...newInstanceForm.value,
    class_list: allClasses.value,
  })
}

const onModelChange = (value: string) => {
  newInstanceForm.value.model_name = value
  telemetry.recordLab('change_model', 'Mdl', { page: 'new_instance', model_name: value })
}

const onStrategyChange = (value: string) => {
  newInstanceForm.value.qs_strategy = value
  telemetry.recordLab('change_strategy', 'Mdl', { page: 'new_instance', qs_strategy: value })
}
</script>

<template>
  <div class="training" data-track-region="new_instance_page">
    <header class="training__header">
      <div class="training__header-content">
        <h1 class="training__title">New Instance</h1>
        <p class="training__subtitle">
          Configure a new active learning instance. You will be redirected to the queue once it is ready.
        </p>
      </div>
    </header>

    <Card class="training__create-form">
      <template #title>Create Instance</template>
      <template #description>Pick a model, query strategy, and the classes to label.</template>

      <div class="create-form">
        <div class="create-form__row">
          <div class="create-form__field">
            <label>Model</label>
            <Select
              :modelValue="newInstanceForm.model_name"
              @update:modelValue="onModelChange"
              :options="modelOptions"
              placeholder="Select model..."
              :disabled="configLoading"
            />
          </div>
          <div class="create-form__field">
            <label>Query Strategy</label>
            <Select
              :modelValue="newInstanceForm.qs_strategy"
              @update:modelValue="onStrategyChange"
              :options="strategyOptions"
              placeholder="Select strategy..."
              :disabled="configLoading"
            />
          </div>
        </div>

        <div class="create-form__row">
          <div class="create-form__field">
            <label>Training Data Path</label>
            <Input
              v-model="newInstanceForm.train_data_path"
              placeholder="data/train.csv"
            />
          </div>
          <div class="create-form__field">
            <label>Test Data Path</label>
            <Input
              v-model="newInstanceForm.test_data_path"
              placeholder="data/test.csv"
            />
          </div>
        </div>

        <div class="create-form__classes">
          <div class="create-form__classes-header">
            <label>Classes (Teams)</label>
            <div style="display: flex; gap: 0.5rem;">
              <Button
                variant="outline"
                size="sm"
                @click="loadTeamsForNewInstance"
                :loading="teamsForNewInstanceLoading"
              >
                Load from Data
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="loadKnownTeams"
                :disabled="allClasses.length >= KNOWN_TEAMS.length"
              >
                Load Known Teams
              </Button>
            </div>
          </div>
          <div
            v-if="allClasses.length"
            class="create-form__classes-list"
          >
            <Badge
              v-for="team in allClasses"
              :key="team"
              variant="secondary"
            >
              {{ team }}
              <button
                v-if="manualClasses.includes(team)"
                class="create-form__class-remove"
                @click.stop="removeManualClass(team)"
                title="Remove"
              >
                <X :size="12" />
              </button>
            </Badge>
          </div>
          <div
            v-if="teamsForNewInstanceError"
            class="create-form__classes-empty"
            style="color: var(--destructive)"
          >
            Failed to load teams from data.
            <Button
              variant="outline"
              size="sm"
              @click="loadTeamsForNewInstance"
              :loading="teamsForNewInstanceLoading"
              style="margin-left: 0.5rem;"
            >
              <RefreshCw :size="14" />
              Retry
            </Button>
          </div>
          <p v-else-if="!allClasses.length" class="create-form__classes-empty">
            Click "Load from Data" or add classes manually below
          </p>
          <div class="create-form__manual-input">
            <Input
              v-model="manualClassInput"
              placeholder="Type a team name..."
              @keydown.enter.prevent="addManualClass"
            />
            <Button
              variant="outline"
              size="sm"
              @click="addManualClass"
              :disabled="!manualClassInput.trim()"
            >
              <Plus :size="14" />
              Add
            </Button>
          </div>
        </div>
      </div>

      <template #footer>
        <Button
          @click="createInstance"
          :loading="createInstanceMutation.isPending.value"
          :disabled="
            !newInstanceForm.model_name ||
            !newInstanceForm.qs_strategy ||
            !allClasses.length
          "
        >
          <Plus :size="16" />
          Create Instance
        </Button>
      </template>
    </Card>
  </div>
</template>

<style scoped lang="scss">
.training {
  max-width: 1000px;
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

  &__create-form {
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
    max-height: 200px;
    overflow-y: auto;
  }

  &__classes-empty {
    font-size: 0.875rem;
    color: var(--muted-foreground);
    padding: 0.75rem;
    background: var(--muted);
    border-radius: var(--radius);
    margin: 0;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  &__manual-input {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
    align-items: center;
  }

  &__class-remove {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-left: 0.25rem;
    padding: 0;
    border: none;
    background: transparent;
    color: inherit;
    cursor: pointer;
    opacity: 0.7;

    &:hover {
      opacity: 1;
    }
  }
}
</style>
