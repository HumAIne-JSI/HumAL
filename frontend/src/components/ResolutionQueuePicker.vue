<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { Inbox, PenLine, RefreshCw, Trash2, X } from 'lucide-vue-next'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useLabeledTicketsStore, type LabeledTicket } from '@/stores/useLabeledTicketsStore'

defineProps<{
  selectedRef?: string
}>()

const emit = defineEmits<{
  select: [ticket: LabeledTicket]
  'write-ticket': []
}>()

const labeledStore = useLabeledTicketsStore()
const searchId = useId()
const teamId = useId()

const search = ref('')
const teamFilter = ref('')
const confirmingClear = ref(false)

const tickets = computed(() => labeledStore.tickets)

const teams = computed(() => {
  const set = new Set<string>()
  for (const ticket of tickets.value) {
    if (ticket.label) set.add(ticket.label)
  }
  return Array.from(set).sort()
})

const filteredTickets = computed(() => {
  const query = search.value.trim().toLowerCase()
  return tickets.value.filter((ticket) => {
    if (teamFilter.value && ticket.label !== teamFilter.value) return false
    return !query || matchesQuery(ticket, query)
  })
})

function matchesQuery(ticket: LabeledTicket, query: string): boolean {
  return [ticket.ref, ticket.title, ticket.description, ticket.label].some((field) =>
    field.toLowerCase().includes(query)
  )
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function clearAll(): void {
  labeledStore.clear()
  confirmingClear.value = false
}

function resetFilters(): void {
  search.value = ''
  teamFilter.value = ''
}
</script>

<template>
  <div class="queue">
    <div v-if="!tickets.length" class="queue-empty">
      <span class="queue-empty__icon" aria-hidden="true"><Inbox :size="20" /></span>
      <p class="queue-empty__title">No labeled tickets yet</p>
      <p class="queue-empty__text">
        Tickets you label in the Smart Assign queue appear here, ready to resolve.
      </p>
      <div class="queue-empty__actions">
        <Button variant="outline" size="sm" type="button" @click="emit('write-ticket')">
          <PenLine :size="14" />
          Enter ticket details instead
        </Button>
        <Button variant="ghost" size="sm" type="button" @click="labeledStore.reload()">
          <RefreshCw :size="14" />
          Refresh
        </Button>
      </div>
    </div>

    <template v-else>
      <div class="queue__toolbar">
        <div class="queue__field queue__field--search">
          <label :for="searchId" class="sr-only">Search queued tickets</label>
          <Input :id="searchId" v-model="search" placeholder="Search ref, title, team…" />
        </div>
        <div class="queue__field">
          <label :for="teamId" class="sr-only">Filter by team</label>
          <select :id="teamId" v-model="teamFilter" class="queue__select">
            <option value="">All teams</option>
            <option v-for="team in teams" :key="team" :value="team">{{ team }}</option>
          </select>
        </div>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          aria-label="Refresh list"
          title="Refresh list"
          @click="labeledStore.reload()"
        >
          <RefreshCw :size="15" />
        </Button>
      </div>

      <div v-if="!filteredTickets.length" class="queue-empty queue-empty--compact">
        <p class="queue-empty__text">No tickets match your filter.</p>
        <Button variant="ghost" size="sm" type="button" @click="resetFilters">Reset filters</Button>
      </div>

      <ul v-else class="queue__list">
        <li
          v-for="ticket in filteredTickets"
          :key="ticket.ref"
          class="queue-item"
          :class="{ 'queue-item--active': selectedRef === ticket.ref }"
        >
          <button
            type="button"
            class="queue-item__main"
            :aria-current="selectedRef === ticket.ref ? 'true' : undefined"
            @click="emit('select', ticket)"
          >
            <span class="queue-item__meta">
              <span class="queue-item__ref">{{ ticket.ref }}</span>
              <Badge variant="secondary">{{ ticket.label }}</Badge>
              <Badge v-if="ticket.mock" variant="outline">demo</Badge>
              <span class="queue-item__time">{{ formatTime(ticket.timestamp) }}</span>
            </span>
            <span class="queue-item__title">{{ ticket.title || 'Untitled ticket' }}</span>
            <span v-if="ticket.description" class="queue-item__desc">{{ ticket.description }}</span>
          </button>
          <Button
            variant="ghost"
            size="icon"
            type="button"
            class="queue-item__remove"
            :aria-label="`Remove ${ticket.ref} from the list`"
            title="Remove from list"
            @click="labeledStore.remove(ticket.ref)"
          >
            <X :size="14" />
          </Button>
        </li>
      </ul>

      <div class="queue__footer">
        <span class="queue__count">
          {{ filteredTickets.length }} of {{ tickets.length }} ticket{{
            tickets.length === 1 ? '' : 's'
          }}
        </span>
        <div v-if="confirmingClear" class="queue__confirm" role="group" aria-label="Confirm clear">
          <span>Remove all tickets from the list?</span>
          <Button variant="ghost" size="sm" type="button" @click="confirmingClear = false">
            Cancel
          </Button>
          <Button variant="destructive" size="sm" type="button" @click="clearAll">Clear list</Button>
        </div>
        <Button v-else variant="ghost" size="sm" type="button" @click="confirmingClear = true">
          <Trash2 :size="14" />
          Clear list
        </Button>
      </div>
    </template>
  </div>
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

.queue {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.queue__toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.queue__field {
  flex: 0 0 11rem;
  min-width: 0;

  &--search {
    flex: 1 1 auto;
  }
}

.queue__select {
  width: 100%;
  height: 2.25rem;
  padding: 0 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--input-background);
  font-family: inherit;
  font-size: 0.875rem;
  color: inherit;

  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 1px;
  }
}

.queue__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: min(26rem, 55vh);
  margin: 0;
  padding: 0 0.25rem 0 0;
  overflow-y: auto;
  list-style: none;
}

.queue-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
  transition:
    border-color 0.15s ease,
    background-color 0.15s ease;

  &:hover {
    border-color: var(--ring);
  }

  &--active {
    border-color: var(--primary);
    box-shadow: inset 3px 0 0 var(--primary);
  }
}

.queue-item__main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
  padding: 0.75rem 0.5rem 0.75rem 0.875rem;
  border: 0;
  border-radius: var(--radius);
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;

  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: -2px;
  }
}

.queue-item__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.queue-item__ref {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.75rem;
  font-weight: 600;
}

.queue-item__time {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--muted-foreground);
  white-space: nowrap;
}

.queue-item__title {
  font-size: 0.9375rem;
  font-weight: 500;
  word-break: break-word;
}

.queue-item__desc {
  display: -webkit-box;
  overflow: hidden;
  font-size: 0.8125rem;
  color: var(--muted-foreground);
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.queue-item__remove {
  flex-shrink: 0;
  margin: 0.375rem 0.375rem 0 0;
  color: var(--muted-foreground);
}

.queue__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  min-height: 2rem;
}

.queue__count {
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

.queue__confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
}

.queue-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  padding: 2.5rem 1rem;
  text-align: center;

  &--compact {
    padding: 1.5rem 1rem;
  }
}

.queue-empty__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  margin-bottom: 0.25rem;
  border-radius: 999px;
  background: var(--muted);
  color: var(--muted-foreground);
}

.queue-empty__title {
  margin: 0;
  font-weight: 600;
}

.queue-empty__text {
  max-width: 22rem;
  margin: 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.queue-empty__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

@media (max-width: 560px) {
  .queue__toolbar {
    flex-wrap: wrap;
  }

  .queue__field--search {
    flex-basis: 100%;
  }

  .queue__field {
    flex: 1 1 auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .queue-item {
    transition: none;
  }
}
</style>
