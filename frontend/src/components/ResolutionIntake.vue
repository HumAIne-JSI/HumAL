<script setup lang="ts">
import { computed, nextTick, ref, useId } from 'vue'
import { AlertCircle, ArrowLeft, FileText, Inbox, Link2, Sparkles } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Textarea from '@/components/ui/Textarea.vue'
import ResolutionQueuePicker from '@/components/ResolutionQueuePicker.vue'
import ResolutionAdvancedOptions from '@/components/ResolutionAdvancedOptions.vue'
import { useLabeledTicketsStore, type LabeledTicket } from '@/stores/useLabeledTicketsStore'

type IntakeTab = 'queue' | 'details'

const props = defineProps<{
  disabled?: boolean
  hasDraft?: boolean
  error?: string | null
  queueRef?: string
  queueTeam?: string
}>()

const title = defineModel<string>('title', { required: true })
const description = defineModel<string>('description', { required: true })
const instanceId = defineModel<number>('instanceId', { required: true })
const topK = defineModel<number>('topK', { required: true })
const category = defineModel<string>('category', { required: true })
const subcategory = defineModel<string>('subcategory', { required: true })

const emit = defineEmits<{
  generate: []
  clear: []
  'pick-ticket': [ticket: LabeledTicket]
  'unlink-ticket': []
  'back-to-draft': []
}>()

const labeledStore = useLabeledTicketsStore()
const uid = useId()
const titleId = `${uid}-title`
const descriptionId = `${uid}-description`
const headingId = `${uid}-heading`

const TABS: { id: IntakeTab; label: string; icon: typeof Inbox }[] = [
  { id: 'queue', label: 'From queue', icon: Inbox },
  { id: 'details', label: 'Ticket details', icon: FileText }
]

const queueCount = computed(() => labeledStore.tickets.length)
const hasInput = computed(() => !!(title.value.trim() || description.value.trim()))
const canClear = computed(() => hasInput.value || !!props.queueRef)
const canGenerate = computed(() => hasInput.value && !props.disabled)
const shortcutKey = /Mac|iPhone|iPad/i.test(navigator.userAgent) ? '⌘' : 'Ctrl'

const activeTab = ref<IntakeTab>(initialTab())

function initialTab(): IntakeTab {
  if (hasInput.value || props.queueRef) return 'details'
  return labeledStore.tickets.length ? 'queue' : 'details'
}

const tabId = (id: IntakeTab) => `${uid}-tab-${id}`
const panelId = (id: IntakeTab) => `${uid}-panel-${id}`

function selectTab(id: IntakeTab, focus = false): void {
  activeTab.value = id
  if (focus) nextTick(() => document.getElementById(tabId(id))?.focus())
}

function onTabKeydown(event: KeyboardEvent): void {
  const keys: Record<string, number> = { ArrowRight: 1, ArrowLeft: -1 }
  const index = TABS.findIndex((tab) => tab.id === activeTab.value)
  let next = -1
  if (event.key in keys) next = (index + keys[event.key]! + TABS.length) % TABS.length
  else if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = TABS.length - 1
  if (next < 0) return
  event.preventDefault()
  selectTab(TABS[next]!.id, true)
}

function onPick(ticket: LabeledTicket): void {
  emit('pick-ticket', ticket)
  selectTab('details', true)
}

function requestGenerate(): void {
  if (canGenerate.value) emit('generate')
}

function onDetailsKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter' || !(event.ctrlKey || event.metaKey)) return
  event.preventDefault()
  requestGenerate()
}
</script>

<template>
  <section class="intake" :aria-labelledby="headingId">
    <header class="intake__header">
      <div class="intake__intro">
        <h2 :id="headingId" class="intake__heading" data-stage-heading tabindex="-1">
          Which ticket are you resolving?
        </h2>
        <p class="intake__lede">Pick one from the queue or enter the details yourself.</p>
      </div>
      <Button
        v-if="hasDraft"
        variant="outline"
        size="sm"
        type="button"
        @click="emit('back-to-draft')"
      >
        <ArrowLeft :size="14" />
        Back to draft
      </Button>
    </header>

    <div class="tabs" role="tablist" aria-label="Ticket source">
      <button
        v-for="tab in TABS"
        :id="tabId(tab.id)"
        :key="tab.id"
        type="button"
        role="tab"
        class="tabs__tab"
        :class="{ 'tabs__tab--active': activeTab === tab.id }"
        :aria-selected="activeTab === tab.id"
        :aria-controls="panelId(tab.id)"
        :tabindex="activeTab === tab.id ? 0 : -1"
        @click="selectTab(tab.id)"
        @keydown="onTabKeydown"
      >
        <component :is="tab.icon" class="tabs__icon" :size="15" aria-hidden="true" />
        {{ tab.label }}
        <span v-if="tab.id === 'queue'" class="tabs__count">{{ queueCount }}</span>
      </button>
    </div>

    <div
      v-show="activeTab === 'queue'"
      :id="panelId('queue')"
      role="tabpanel"
      :aria-labelledby="tabId('queue')"
      class="intake__panel"
    >
      <ResolutionQueuePicker
        :selected-ref="queueRef"
        @select="onPick"
        @write-ticket="selectTab('details', true)"
      />
    </div>

    <div
      v-show="activeTab === 'details'"
      :id="panelId('details')"
      role="tabpanel"
      :aria-labelledby="tabId('details')"
      class="intake__panel"
      @keydown="onDetailsKeydown"
    >
      <div v-if="queueRef" class="linked">
        <Link2 :size="16" class="linked__icon" aria-hidden="true" />
        <p class="linked__text">
          Queue ticket <strong>{{ queueRef }}</strong>, routed to <strong>{{ queueTeam }}</strong>.
          The team label guides the suggestions.
        </p>
        <Button variant="ghost" size="sm" type="button" @click="emit('unlink-ticket')">
          Unlink
        </Button>
      </div>

      <div class="field">
        <label :for="titleId" class="field__label">Title</label>
        <Input
          :id="titleId"
          v-model="title"
          placeholder="e.g. Cannot access the shared drive after a password reset"
          :disabled="disabled"
        />
      </div>

      <div class="field">
        <label :for="descriptionId" class="field__label">Description</label>
        <Textarea
          :id="descriptionId"
          v-model="description"
          class="field__description"
          placeholder="What happened, what the user already tried, any error messages…"
          :rows="5"
          :disabled="disabled"
        />
      </div>

      <ResolutionAdvancedOptions
        v-model:instance-id="instanceId"
        v-model:top-k="topK"
        v-model:category="category"
        v-model:subcategory="subcategory"
        :disabled="disabled"
      />

      <div v-if="error" class="intake__error" role="alert">
        <AlertCircle :size="16" aria-hidden="true" />
        <p><strong>Couldn't generate a solution.</strong> {{ error }}</p>
      </div>

      <footer class="intake__footer">
        <Button
          v-if="canClear"
          variant="ghost"
          type="button"
          :disabled="disabled"
          @click="emit('clear')"
        >
          Clear
        </Button>
        <span v-else class="intake__hint">Add a title or description to continue.</span>
        <div class="intake__submit">
          <span class="intake__shortcut" aria-hidden="true">
            <kbd>{{ shortcutKey }}</kbd> + <kbd>Enter</kbd>
          </span>
          <Button
            type="button"
            :disabled="!hasInput"
            :loading="disabled"
            :aria-keyshortcuts="`${shortcutKey === '⌘' ? 'Meta' : 'Control'}+Enter`"
            @click="requestGenerate"
          >
            <Sparkles :size="16" />
            Generate solution
          </Button>
        </div>
      </footer>
    </div>
  </section>
</template>

<style scoped lang="scss">
.intake {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
}

.intake__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.intake__heading {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.01em;

  &:focus {
    outline: none;
  }
}

.intake__lede {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.tabs {
  display: inline-flex;
  align-self: flex-start;
  gap: 0.25rem;
  padding: 0.25rem;
  border-radius: var(--radius);
  background: var(--muted);
}

.tabs__tab {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4375rem 0.875rem;
  border: 0;
  border-radius: calc(var(--radius) - 3px);
  background: transparent;
  color: var(--muted-foreground);
  font: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;

  &:hover {
    color: var(--foreground);
  }

  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 1px;
  }

  &--active {
    background: var(--card);
    color: var(--foreground);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  }
}

.tabs__count {
  min-width: 1.25rem;
  padding: 0 0.375rem;
  border-radius: 999px;
  background: var(--background);
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
  text-align: center;

  .tabs__tab--active & {
    background: var(--primary);
    color: var(--primary-foreground);
  }
}

.intake__panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.linked {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.5rem 0.625rem 0.875rem;
  border-radius: var(--radius);
  background: var(--info-muted);
  color: var(--info-muted-foreground);
}

.linked__icon {
  flex-shrink: 0;
}

.linked__text {
  flex: 1;
  margin: 0;
  font-size: 0.8125rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.field__label {
  font-size: 0.875rem;
  font-weight: 500;
}

.field__description {
  min-height: 7.5rem;
  max-height: 40vh;
  overflow-y: auto;
  font-family: inherit;
}

.intake__error {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.75rem 0.875rem;
  border-radius: var(--radius);
  background: var(--destructive-muted);
  color: var(--destructive-muted-foreground);
  font-size: 0.875rem;

  svg {
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  p {
    margin: 0;
  }
}

.intake__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.intake__hint {
  font-size: 0.8125rem;
  color: var(--muted-foreground);
}

.intake__submit {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: auto;
}

.intake__shortcut {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  white-space: nowrap;

  kbd {
    padding: 0.0625rem 0.375rem;
    border: 1px solid var(--border);
    border-bottom-width: 2px;
    border-radius: 4px;
    background: var(--background);
    font-family: inherit;
    font-size: 0.6875rem;
  }
}

@media (max-width: 640px) {
  .intake {
    padding: 1.125rem;
  }

  .intake__header {
    flex-direction: column;
  }

  .tabs {
    align-self: stretch;

    .tabs__tab {
      flex: 1 1 auto;
      justify-content: center;
      padding-inline: 0.5rem;
    }

    .tabs__icon {
      display: none;
    }
  }

  .intake__shortcut {
    display: none;
  }

  .intake__submit {
    flex: 1 1 100%;

    :deep(.btn) {
      width: 100%;
    }
  }
}

@media (prefers-reduced-motion: reduce) {
  .tabs__tab {
    transition: none;
  }
}
</style>
