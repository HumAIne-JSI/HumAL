<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useId } from 'vue'
import { toast } from 'vue-sonner'
import { AlertCircle, Check, Copy, RefreshCw, Send, Undo2, X } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import Textarea from '@/components/ui/Textarea.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import LoadingPhase, { type LoadingPhaseStep } from '@/components/ui/LoadingPhase.vue'
import ExportButton from '@/components/ExportButton.vue'
import type { AssistedResolution } from '@/composables/api/useResolution'

// Demo-only: teams the operator can reassign the ticket to.
const AVAILABLE_TEAMS = [
  'Network Operations',
  'Hardware Support',
  'Software Support',
  'Security',
  'Database Administration',
  'Cloud Infrastructure',
  'Identity & Access',
  'Service Desk'
]
const COPIED_RESET_MS = 2000

const props = defineProps<{
  result: AssistedResolution | null
  drafting: boolean
  showProgress: boolean
  phase: string
  phases: LoadingPhaseStep[]
  saving: boolean
  undoReason: string | null
  error: string | null
  exportData: object[]
}>()

const response = defineModel<string>('response', { required: true })

const emit = defineEmits<{
  edit: []
  copied: []
  regenerate: []
  undo: []
  'dismiss-undo': []
  'dismiss-error': []
  send: []
  reassign: [team: string]
}>()

const uid = useId()
const headingId = `${uid}-heading`
const editorId = `${uid}-editor`
const reassignId = `${uid}-reassign`

const reassignOpen = ref(false)
const reassignTeam = ref('')
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

const team = computed(() => props.result?.predicted_team ?? '')
const confidencePct = computed(() => Math.round((props.result?.team_confidence ?? 0) * 100))
const votesLabel = computed(() => {
  const count = props.result?.votes_applied ?? 0
  return count > 0 ? `${count} vote${count === 1 ? '' : 's'} used` : 'None used'
})
// While drafting or sending, the draft must not change underneath the request.
const locked = computed(() => props.drafting || props.saving)
const canSend = computed(() => !!props.result && !props.drafting && !!response.value.trim())
const lede = computed(() =>
  props.result
    ? 'Edit the suggested reply, then send it to the team.'
    : 'Finding similar past tickets and drafting a reply…'
)

function onInput(value: string): void {
  response.value = value
  emit('edit')
}

function openReassign(): void {
  reassignTeam.value = team.value
  reassignOpen.value = true
}

function confirmReassign(): void {
  if (reassignTeam.value) emit('reassign', reassignTeam.value)
  reassignOpen.value = false
}

async function copyReply(): Promise<void> {
  try {
    await navigator.clipboard.writeText(response.value)
    copied.value = true
    clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => (copied.value = false), COPIED_RESET_MS)
    emit('copied')
  } catch {
    toast.error('Could not copy the reply')
  }
}

onBeforeUnmount(() => clearTimeout(copiedTimer))
</script>

<template>
  <section class="draft" :aria-labelledby="headingId" :aria-busy="drafting">
    <header class="draft__header">
      <h2 :id="headingId" class="draft__heading" data-stage-heading tabindex="-1">
        Review the draft
      </h2>
      <p class="draft__lede">{{ lede }}</p>
    </header>

    <Transition name="draft-fade">
      <LoadingPhase
        v-if="showProgress"
        class="draft__progress"
        :current-phase="phase"
        :phases="phases"
      />
    </Transition>

    <dl v-if="result" class="meta">
      <div class="meta__item meta__item--team">
        <dt>Suggested team</dt>
        <dd v-if="!reassignOpen" class="meta__team">
          <span>{{ team }}</span>
          <button type="button" class="meta__link" :disabled="locked" @click="openReassign">
            Reassign
          </button>
        </dd>
        <dd v-else class="reassign">
          <label :for="reassignId" class="sr-only">Team</label>
          <select :id="reassignId" v-model="reassignTeam" class="reassign__select">
            <option v-for="name in AVAILABLE_TEAMS" :key="name" :value="name">{{ name }}</option>
          </select>
          <Button
            size="sm"
            type="button"
            :disabled="!reassignTeam || locked"
            @click="confirmReassign"
          >
            <Check :size="14" />
            Confirm
          </Button>
          <Button variant="ghost" size="sm" type="button" @click="reassignOpen = false">
            Cancel
          </Button>
        </dd>
      </div>
      <div class="meta__item">
        <dt>Category</dt>
        <dd>{{ result.classification }}</dd>
      </div>
      <div class="meta__item">
        <dt>Certainty</dt>
        <dd class="meta__certainty">
          <Progress :value="confidencePct" :max="100" />
          <span>{{ confidencePct }}%</span>
        </dd>
      </div>
      <div class="meta__item">
        <dt>Past feedback</dt>
        <dd>{{ votesLabel }}</dd>
      </div>
    </dl>

    <div class="editor">
      <div class="editor__head">
        <label :for="editorId" class="editor__label">Suggested reply</label>
        <span v-if="result" class="editor__count">{{ response.length }} characters</span>
      </div>
      <SkeletonCard v-if="!result" class="editor__skeleton" :title="false" :lines="7" />
      <div v-else class="editor__body" :class="{ 'editor__body--busy': drafting }">
        <Textarea
          :id="editorId"
          :model-value="response"
          class="editor__textarea"
          :rows="10"
          :disabled="locked"
          @update:model-value="onInput"
        />
        <span v-if="drafting" class="editor__busy">Drafting a new reply…</span>
      </div>
    </div>

    <div v-if="undoReason" class="notice" role="status">
      <Undo2 :size="15" aria-hidden="true" />
      <span class="notice__text">{{ undoReason }}</span>
      <Button variant="outline" size="sm" type="button" :disabled="locked" @click="emit('undo')">
        Undo
      </Button>
      <Button
        variant="ghost"
        size="icon"
        type="button"
        aria-label="Dismiss"
        @click="emit('dismiss-undo')"
      >
        <X :size="14" />
      </Button>
    </div>

    <div v-if="error" class="notice notice--error" role="alert">
      <AlertCircle :size="15" aria-hidden="true" />
      <span class="notice__text">
        <strong>Couldn't regenerate.</strong> {{ error }} Your current draft is unchanged.
      </span>
      <Button
        variant="ghost"
        size="icon"
        type="button"
        aria-label="Dismiss"
        @click="emit('dismiss-error')"
      >
        <X :size="14" />
      </Button>
    </div>

    <footer class="draft__actions">
      <div class="draft__secondary">
        <Button variant="outline" type="button" :disabled="!canSend" @click="copyReply">
          <Check v-if="copied" :size="16" />
          <Copy v-else :size="16" />
          {{ copied ? 'Copied' : 'Copy' }}
        </Button>
        <Button
          variant="outline"
          type="button"
          :disabled="!result || saving"
          :loading="drafting && !!result"
          @click="emit('regenerate')"
        >
          <RefreshCw :size="16" />
          Regenerate
        </Button>
        <ExportButton :data="exportData" filename="resolution_result" :disabled="!result" />
      </div>
      <Button
        class="draft__send"
        type="button"
        :disabled="!canSend"
        :loading="saving"
        @click="emit('send')"
      >
        <Send :size="16" />
        {{ team ? `Send to ${team}` : 'Send to team' }}
      </Button>
      <span class="sr-only" aria-live="polite">{{ copied ? 'Reply copied' : '' }}</span>
    </footer>
  </section>
</template>

<style scoped lang="scss">
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.draft {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
}

.draft__heading {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.01em;

  &:focus {
    outline: none;
  }
}

.draft__lede {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.draft__progress {
  padding: 0.875rem 1rem;
  border-radius: var(--radius);
  background: var(--muted);
}

.meta {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin: 0;
  padding: 1rem 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);

  dt {
    margin-bottom: 0.375rem;
    font-size: 0.6875rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted-foreground);
  }

  dd {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 500;
    overflow-wrap: anywhere;
  }
}

.meta .meta__team {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.25rem 0.625rem;
  font-size: 1.0625rem;
  font-weight: 600;
}

.meta__link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted-foreground);
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;

  &:hover {
    color: var(--foreground);
  }

  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 2px;
    border-radius: 2px;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.meta__certainty {
  display: flex;
  align-items: center;
  gap: 0.625rem;

  span {
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
}

.reassign {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.375rem;
}

.reassign__select {
  flex: 1 1 10rem;
  min-width: 0;
  height: 2rem;
  padding: 0 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--input-background);
  font-family: inherit;
  font-size: 0.8125rem;
  color: inherit;
}

.editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.editor__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
}

.editor__label {
  font-size: 0.875rem;
  font-weight: 500;
}

.editor__count {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  font-variant-numeric: tabular-nums;
}

.editor__body {
  position: relative;
}

.editor__textarea {
  min-height: 14rem;
  max-height: max(12rem, var(--draft-editor-max, 50vh));
  overflow-y: auto;
  padding: 0.875rem 1rem;
  font-family: inherit;
  font-size: 0.9375rem;
  line-height: 1.6;
}

.editor__busy {
  position: absolute;
  top: 0.625rem;
  right: 0.625rem;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  background: var(--primary);
  color: var(--primary-foreground);
  font-size: 0.75rem;
  font-weight: 500;
}

.notice {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.5rem 0.5rem 0.875rem;
  border-radius: var(--radius);
  background: var(--muted);
  font-size: 0.875rem;

  &--error {
    background: var(--destructive-muted);
    color: var(--destructive-muted-foreground);
  }

  svg {
    flex-shrink: 0;
  }
}

.notice__text {
  flex: 1;
}

.draft__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.draft__secondary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.draft-fade-enter-active,
.draft-fade-leave-active {
  transition: opacity 0.2s ease;
}

.draft-fade-enter-from,
.draft-fade-leave-to {
  opacity: 0;
}

@media (max-width: 720px) {
  .meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .meta__item--team {
    grid-column: 1 / -1;
  }
}

@media (max-width: 640px) {
  .draft {
    padding: 1.125rem;
  }

  .draft__secondary,
  .draft__send {
    flex: 1 1 100%;
  }

  .draft__secondary > * {
    flex: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .draft-fade-enter-active,
  .draft-fade-leave-active {
    transition: none;
  }
}
</style>
