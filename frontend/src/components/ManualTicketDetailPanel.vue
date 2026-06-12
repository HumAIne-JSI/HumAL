<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Select from '@/components/ui/Select.vue'
import type { QueueTicket } from '@/stores/useTicketQueueStore'
import { X, FileText, Check, CheckCircle, ChevronRight } from 'lucide-vue-next'

export interface ManualTicketDetailPanelProps {
  ticket: QueueTicket | null
  teams?: string[]
}

const props = withDefaults(defineProps<ManualTicketDetailPanelProps>(), {})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', team: string): void
  (e: 'next'): void
}>()

const selectedTeam = ref<string>('')
const showLabeledFlash = ref(false)
const labeledTeamName = ref('')

const teamOptions = computed(() => {
  if (!props.teams?.length) return []
  return props.teams.map((t) => ({ value: t, label: t }))
})

function handleConfirm() {
  if (!selectedTeam.value) return
  const team = selectedTeam.value
  labeledTeamName.value = team
  showLabeledFlash.value = true
  emit('confirm', team)
  selectedTeam.value = ''
}

function formatDate(date: Date): string {
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

watch(
  () => props.ticket?.id,
  (newId, oldId) => {
    if (newId !== oldId) {
      selectedTeam.value = ''
      showLabeledFlash.value = false
      labeledTeamName.value = ''
    }
  },
)
</script>

<template>
  <Transition name="detail-fade" mode="out-in">
    <div class="manual-detail" v-if="ticket" :key="ticket.id" data-track-region="ticket_detail">
      <!-- Labeled Flash -->
      <Transition name="flash-fade">
        <div v-if="showLabeledFlash" class="manual-detail__labeled-flash">
          <CheckCircle :size="20" />
          <span>Labeled &mdash; {{ labeledTeamName }}</span>
        </div>
      </Transition>

      <!-- Header -->
      <header class="manual-detail__header">
        <div class="manual-detail__header-row">
          <div class="manual-detail__header-left">
            <span class="manual-detail__ref">{{ ticket.ref }}</span>
            <span class="manual-detail__ref-sep">&middot;</span>
            <Badge v-if="ticket.team" variant="secondary">{{ ticket.team }}</Badge>
            <Badge v-if="ticket.category" variant="outline">{{ ticket.category }}</Badge>
            <span class="manual-detail__time">{{ formatDate(ticket.timestamp) }}</span>
          </div>
          <div class="manual-detail__header-right">
            <Button variant="ghost" size="icon" @click="$emit('next')" title="Next ticket">
              <ChevronRight :size="16" />
            </Button>
            <Button variant="ghost" size="icon" @click="$emit('close')">
              <X :size="16" />
            </Button>
          </div>
        </div>
        <h2 class="manual-detail__title">{{ ticket.title }}</h2>
      </header>

      <!-- Content: just body + label picker, no AI aids -->
      <div class="manual-detail__content">
        <p class="manual-detail__description">{{ ticket.description }}</p>

        <section class="manual-detail__label" data-track-region="label_picker">
          <label class="manual-detail__label-heading">Assign team</label>
          <div class="manual-detail__label-row">
            <Select
              v-model="selectedTeam"
              :options="teamOptions"
              placeholder="Select team..."
              size="sm"
            />
            <Button
              variant="default"
              size="sm"
              :disabled="!selectedTeam"
              data-track-region="confirm_button"
              @click="handleConfirm"
            >
              <Check :size="14" />
              Confirm
            </Button>
          </div>
        </section>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else key="empty" class="manual-detail manual-detail--empty">
      <div class="manual-detail__empty-state">
        <FileText :size="40" class="manual-detail__empty-icon" />
        <p>Select a ticket to view details</p>
      </div>
    </div>
  </Transition>
</template>

<style scoped lang="scss">
.manual-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
  border-left: 1px solid var(--border);
  overflow: hidden;

  &--empty {
    align-items: center;
    justify-content: center;
  }

  &__header {
    padding: 0.625rem 1rem;
    background: var(--card);
    border-bottom: 1px solid var(--border);
  }

  &__header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.375rem;
  }

  &__header-left {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
    min-width: 0;
  }

  &__header-right {
    display: flex;
    align-items: center;
    gap: 0.125rem;
    flex-shrink: 0;
  }

  &__ref {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--muted-foreground);
    text-transform: uppercase;
  }

  &__ref-sep {
    color: var(--muted-foreground);
    font-size: 0.75rem;
  }

  &__time {
    font-size: 0.75rem;
    color: var(--muted-foreground);
  }

  &__title {
    margin: 0;
    font-size: 1.0625rem;
    font-weight: 600;
    color: var(--foreground);
    line-height: 1.35;
  }

  &__content {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__description {
    margin: 0;
    font-size: 0.9375rem;
    line-height: 1.65;
    color: var(--foreground);
    white-space: pre-wrap;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
  }

  &__label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__label-heading {
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  &__label-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }

  &__labeled-flash {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: color-mix(in srgb, var(--success, #22c55e) 12%, var(--card));
    color: var(--success, #22c55e);
    font-size: 0.8125rem;
    font-weight: 600;
    border-bottom: 1px solid color-mix(in srgb, var(--success, #22c55e) 20%, var(--border));
  }

  &__empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    color: var(--muted-foreground);
    text-align: center;
  }

  &__empty-icon {
    opacity: 0.4;
  }
}

.detail-fade-enter-active,
.detail-fade-leave-active {
  transition: opacity 0.15s ease;
}
.detail-fade-enter-from,
.detail-fade-leave-to {
  opacity: 0;
}

.flash-fade-enter-active,
.flash-fade-leave-active {
  transition: opacity 0.2s ease;
}
.flash-fade-enter-from,
.flash-fade-leave-to {
  opacity: 0;
}
</style>
