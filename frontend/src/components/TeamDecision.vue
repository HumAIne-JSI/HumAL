<script setup lang="ts">
import { computed, nextTick, ref, useId, watch } from 'vue'
import { AlertTriangle, Coffee, HelpCircle } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Select from '@/components/ui/Select.vue'
import TeamGuide from '@/components/TeamGuide.vue'
import { SUGGESTION_SHORTCUT_COUNT } from '@/composables/useKeyboardNavigation'
import type { LabelerFeedbackType, TopKPrediction } from '@/types/api'

export interface TeamDecisionSubmit {
  team: string
  // 1-based rank of the chosen model suggestion; null when the team overrides the model.
  predictionRank: number | null
}

const props = withDefaults(
  defineProps<{
    teams?: string[]
    predictions?: TopKPrediction[]
    pending?: boolean
    disabled?: boolean
    isTired?: boolean
    isDifficult?: boolean
  }>(),
  {
    predictions: () => [],
    pending: false,
    disabled: false,
    isTired: false,
    isDifficult: false
  }
)

const emit = defineEmits<{
  (e: 'submit', payload: TeamDecisionSubmit): void
  (e: 'feedback', type: LabelerFeedbackType): void
}>()

const headingId = useId()
const radioName = useId()
const selectedTeam = ref('')
const touched = ref(false)
// Bridges the gap between a commit and the parent reporting `pending`.
const submitted = ref(false)
const teamSelectRef = ref<InstanceType<typeof Select> | null>(null)
const assignButtonRef = ref<InstanceType<typeof Button> | null>(null)

const hasPredictions = computed(() => props.predictions.length > 0)
const defaultTeam = computed(() => props.predictions[0]?.label ?? '')
const isLocked = computed(() => props.disabled || props.pending || submitted.value)
const canCommit = computed(() => Boolean(selectedTeam.value) && !isLocked.value)
const teamOptions = computed(() =>
  (props.teams ?? []).map((team) => ({ value: team, label: team }))
)

const selectedRank = computed(() => {
  const index = props.predictions.findIndex((p) => p.label === selectedTeam.value)
  return index === -1 ? null : index + 1
})
const isOverride = computed(() => Boolean(selectedTeam.value) && selectedRank.value === null)

// The search only shows teams outside the suggestions; picking a suggested
// team there checks its row instead.
const otherTeam = computed({
  get: () => (isOverride.value ? selectedTeam.value : ''),
  set: (team: string) => chooseAndFocusAssign(team)
})

const rankCaption = computed(() => {
  if (!hasPredictions.value || !selectedTeam.value) return ''
  if (selectedRank.value === null) return 'Overrides model'
  return selectedRank.value === 1 ? 'Top suggestion' : `Suggestion ${selectedRank.value}`
})

// Follow the model's top pick (it can be refined after the first paint)
// until the user makes a choice of their own.
watch(
  defaultTeam,
  (team) => {
    if (!touched.value) selectedTeam.value = team
  },
  { immediate: true }
)

watch(
  () => props.pending,
  (isPending, wasPending) => {
    if (wasPending && !isPending) submitted.value = false
  }
)

function formatPercent(probability: number) {
  return `${(probability * 100).toFixed(1)}%`
}

function meterWidth(probability: number) {
  return `${Math.min(Math.max(probability, 0), 1) * 100}%`
}

function choose(team: string) {
  if (isLocked.value || !team) return
  touched.value = true
  selectedTeam.value = team
}

function chooseAndFocusAssign(team: string) {
  choose(team)
  // Select hands focus back to its trigger first; move it on to the commit.
  nextTick(() => (assignButtonRef.value?.$el as HTMLElement | undefined)?.focus())
}

function selectRank(rank: number): boolean {
  const suggestion = props.predictions[rank - 1]
  if (!suggestion || isLocked.value) return false
  choose(suggestion.label)
  return true
}

function focusTeamSearch() {
  if (isLocked.value || !teamSelectRef.value) return
  ;(teamSelectRef.value.$el as HTMLElement).scrollIntoView({ block: 'nearest' })
  teamSelectRef.value.open()
}

function commit() {
  if (isLocked.value) return
  // Nothing staged yet: point the user at the team search instead.
  if (!selectedTeam.value) return focusTeamSearch()
  touched.value = true
  submitted.value = true
  emit('submit', { team: selectedTeam.value, predictionRank: selectedRank.value })
}

function preventRepeatedCommit(event: KeyboardEvent) {
  if (!event.repeat) return
  event.preventDefault()
  event.stopPropagation()
}

// Returns true when it undid a user choice, so Esc can fall through otherwise.
function reset(): boolean {
  if (isLocked.value) return false
  const changed = touched.value && selectedTeam.value !== defaultTeam.value
  touched.value = false
  selectedTeam.value = defaultTeam.value
  return changed
}

function handleChoicesKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    commit()
  } else if (event.key.startsWith('Arrow')) {
    // Native radio roving must not also move through the ticket queue.
    event.stopPropagation()
  }
}

defineExpose({ selectRank, focusTeamSearch, commit, reset })
</script>

<template>
  <form
    class="team-decision"
    :class="{ 'team-decision--locked': isLocked }"
    :aria-labelledby="headingId"
    :aria-busy="pending"
    @keydown.enter.capture="preventRepeatedCommit"
    @submit.prevent="commit"
  >
    <header class="team-decision__header">
      <h3 :id="headingId" class="team-decision__heading">
        {{ hasPredictions ? 'Route to team' : 'Assign team' }}
      </h3>
      <TeamGuide :teams="teams" @select="chooseAndFocusAssign" />
    </header>

    <div
      v-if="hasPredictions"
      class="team-decision__choices"
      role="radiogroup"
      aria-label="Model suggestions"
      @keydown="handleChoicesKeydown"
    >
      <label
        v-for="(suggestion, index) in predictions"
        :key="suggestion.label"
        class="team-decision__choice"
        :class="{ 'is-selected': suggestion.label === selectedTeam }"
      >
        <input
          type="radio"
          class="team-decision__radio"
          :name="radioName"
          :value="suggestion.label"
          :checked="suggestion.label === selectedTeam"
          :disabled="isLocked"
          @change="choose(suggestion.label)"
        />
        <span class="team-decision__choice-body">
          <span class="team-decision__choice-line">
            <span class="team-decision__team">{{ suggestion.label }}</span>
            <span class="team-decision__confidence">
              {{ formatPercent(suggestion.probability) }}
            </span>
          </span>
          <span class="team-decision__meter" aria-hidden="true">
            <span
              class="team-decision__meter-fill"
              :style="{ width: meterWidth(suggestion.probability) }"
            />
          </span>
        </span>
        <kbd v-if="index < SUGGESTION_SHORTCUT_COUNT" class="team-decision__kbd" aria-hidden="true">
          {{ index + 1 }}
        </kbd>
      </label>
    </div>

    <label
      class="team-decision__other"
      :class="{ 'is-override': hasPredictions && isOverride }"
      :data-track-region="hasPredictions ? 'reassign_select' : undefined"
    >
      <span class="team-decision__other-label">{{ hasPredictions ? 'Another team' : 'Team' }}</span>
      <Select
        ref="teamSelectRef"
        v-model="otherTeam"
        class="team-decision__select"
        :options="teamOptions"
        :placeholder="hasPredictions ? 'Search all teams...' : 'Search teams...'"
        size="sm"
        :disabled="isLocked"
      />
      <kbd class="team-decision__kbd" aria-hidden="true">/</kbd>
    </label>

    <div class="team-decision__commit">
      <p class="team-decision__summary" aria-live="polite">
        <template v-if="selectedTeam">
          <span>Assign to <strong>{{ selectedTeam }}</strong></span>
          <span
            v-if="rankCaption"
            class="team-decision__chip"
            :class="{ 'team-decision__chip--override': isOverride }"
          >
            {{ rankCaption }}
          </span>
        </template>
        <span v-else>Choose a team to continue</span>
      </p>
      <Button
        ref="assignButtonRef"
        type="submit"
        size="sm"
        class="team-decision__assign"
        data-track-region="confirm_button"
        :disabled="!canCommit"
        :loading="pending"
      >
        Assign
        <kbd class="team-decision__kbd team-decision__kbd--on-primary" aria-hidden="true">↵</kbd>
      </Button>
    </div>

    <div class="team-decision__extras" data-track-region="labeler_feedback">
      <div class="team-decision__flags" role="group" aria-label="Flags sent with this label">
        <Button
          type="button"
          :variant="isTired ? 'secondary' : 'ghost'"
          size="sm"
          :disabled="isLocked"
          :aria-pressed="isTired"
          @click="emit('feedback', 'I_AM_TIRED')"
        >
          <Coffee :size="14" />
          Tired
        </Button>
        <Button
          type="button"
          :variant="isDifficult ? 'secondary' : 'ghost'"
          size="sm"
          :disabled="isLocked"
          :aria-pressed="isDifficult"
          @click="emit('feedback', 'DIFFICULT_TICKET')"
        >
          <AlertTriangle :size="14" />
          Difficult
        </Button>
        <span class="team-decision__flags-hint">sent with this label</span>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        class="team-decision__skip"
        :disabled="isLocked"
        @click="emit('feedback', 'I_DONT_KNOW')"
      >
        <HelpCircle :size="14" />
        Skip &mdash; I don't know
      </Button>
    </div>
  </form>
</template>

<style scoped lang="scss">
.team-decision {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  &__heading {
    margin: 0;
    color: var(--muted-foreground);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  &__choices {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  &__choice {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 0.75rem;
    min-height: 2.75rem;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--card);
    cursor: pointer;
    transition:
      border-color 0.15s ease,
      background-color 0.15s ease;

    &:hover {
      border-color: color-mix(in oklch, var(--primary) 35%, var(--border));
    }

    &.is-selected {
      border-color: var(--primary);
      background: color-mix(in oklch, var(--primary) 5%, var(--card));
    }
  }

  &__radio {
    width: 1rem;
    height: 1rem;
    margin: 0;
    accent-color: var(--primary);
    cursor: inherit;

    &:focus-visible {
      outline: 2px solid var(--ring);
      outline-offset: 2px;
    }
  }

  &__choice-body {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
    min-width: 0;
  }

  &__choice-line {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
    min-width: 0;
  }

  &__team {
    color: var(--foreground);
    font-size: 0.8125rem;
    font-weight: 600;
    overflow-wrap: anywhere;
  }

  &__confidence {
    flex-shrink: 0;
    color: var(--muted-foreground);
    font-size: 0.75rem;
    font-variant-numeric: tabular-nums;
  }

  &__meter {
    display: block;
    height: 2px;
    overflow: hidden;
    border-radius: 999px;
    background: var(--muted);
  }

  &__meter-fill {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: var(--muted-foreground);
    transition: background-color 0.15s ease;
  }

  &__choice.is-selected &__meter-fill {
    background: var(--primary);
  }

  &__other {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 0.75rem;
  }

  &__other-label {
    color: var(--muted-foreground);
    font-size: 0.75rem;
    font-weight: var(--font-weight-medium);
    white-space: nowrap;
  }

  &__other.is-override :deep(.select-trigger) {
    border-color: var(--warning);
  }

  &__kbd {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.25rem;
    height: 1.25rem;
    padding: 0 0.3rem;
    border: 1px solid var(--border);
    border-radius: 0.3rem;
    background: var(--muted);
    color: var(--muted-foreground);
    font-family: ui-monospace, monospace;
    font-size: 0.6875rem;
    font-weight: 600;
    line-height: 1;
  }

  &__kbd--on-primary {
    border-color: color-mix(in oklch, var(--primary-foreground) 35%, transparent);
    background: transparent;
    color: inherit;
  }

  &__commit {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem 0.75rem;
    margin-top: 0.125rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border);
  }

  &__summary {
    display: flex;
    flex: 1 1 14rem;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.375rem 0.5rem;
    min-width: 0;
    margin: 0;
    color: var(--muted-foreground);
    font-size: 0.8125rem;

    strong {
      color: var(--foreground);
      font-weight: 600;
      overflow-wrap: anywhere;
    }
  }

  &__chip {
    display: inline-flex;
    align-items: center;
    height: 1.25rem;
    padding: 0 0.5rem;
    border-radius: 999px;
    background: var(--muted);
    color: var(--muted-foreground);
    font-size: 0.6875rem;
    font-weight: 600;
    white-space: nowrap;
  }

  &__chip--override {
    background: var(--warning-muted);
    color: var(--warning-muted-foreground);
  }

  &__assign {
    min-width: 7rem;
  }

  &__extras {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.25rem 0.75rem;
    margin-top: -0.25rem;
  }

  &__flags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.25rem;
  }

  &__flags-hint {
    margin-left: 0.25rem;
    color: var(--muted-foreground);
    font-size: 0.6875rem;
  }

  &__skip {
    color: var(--muted-foreground);
  }

  &--locked &__choice {
    cursor: not-allowed;
    opacity: 0.7;
  }
}

@media (max-width: 640px) {
  .team-decision__assign {
    flex: 1 1 100%;
  }
}

@media (hover: none) {
  .team-decision__kbd {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .team-decision__choice,
  .team-decision__meter-fill {
    transition: none;
  }
}
</style>
