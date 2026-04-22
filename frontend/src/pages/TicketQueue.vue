<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import InstanceSelector from '@/components/InstanceSelector.vue'
import TicketFilterBar from '@/components/TicketFilterBar.vue'
import TicketListItem from '@/components/TicketListItem.vue'
import TicketDetailPanel from '@/components/TicketDetailPanel.vue'
import { useTicketQueue } from '@/composables/api/useTicketQueue'
import { useKeyboardNavigation, formatShortcutKey } from '@/composables/useKeyboardNavigation'
import { useInstanceStore } from '@/stores/useInstanceStore'
import { useMockData, setUseMockData } from '@/composables/useMockTickets'
import type { TicketStatus, SortOrder } from '@/stores/useTicketQueueStore'
import {
  Inbox,
  RefreshCw,
  CheckSquare,
  CheckCircle,
  X,
  Keyboard,
  AlertCircle,
  Sparkles,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const instanceStore = useInstanceStore()

// Use store's instance ID
const selectedInstanceId = computed({
  get: () => instanceStore.selectedInstanceId,
  set: (value: number) => instanceStore.setInstance(value),
})

// Initialize from route query
onMounted(() => {
  const instanceParam = route.query.instance
  if (instanceParam) {
    instanceStore.setInstance(Number(instanceParam))
  }
})

// Sync URL with instance selection
watch(
  () => instanceStore.selectedInstanceId,
  (newId) => {
    if (newId > 0) {
      router.replace({ query: { ...route.query, instance: String(newId) } })
    }
  }
)

// Ticket queue composable
const {
  store,
  isLoading,
  isMockMode,
  tickets,
  selectedTicket,
  statusCounts,
  teams,
  refresh,
  selectTicket,
  selectNext,
  selectPrevious,
  toggleBulkSelect,
  selectAllVisible,
  clearBulkSelection,
  setFilter,
  resetFilters,
  labelTicket,
  isLabeling,
  bulkLabel,
  isBulkLabeling,
  filters,
  hasBulkSelection,
  bulkSelectedTickets,
} = useTicketQueue({
  instanceId: selectedInstanceId,
  autoFetch: true,
})

// Keyboard navigation
const {
  shortcuts,
  isHelpOpen,
  registerNavigationShortcuts,
  openHelp,
  closeHelp,
} = useKeyboardNavigation()

// Register keyboard shortcuts
registerNavigationShortcuts({
  onNext: () => {
    if (selectNext()) {
      // Scrolled to next
    }
  },
  onPrev: () => {
    if (selectPrevious()) {
      // Scrolled to previous
    }
  },
  onClose: () => {
    if (hasBulkSelection.value) {
      clearBulkSelection()
    } else if (selectedTicket.value) {
      selectTicket(null)
    }
  },
  onConfirm: () => {
    // Will be handled by detail panel
  },
  onToggleBulk: () => {
    if (selectedTicket.value) {
      toggleBulkSelect(selectedTicket.value.id)
    }
  },
  onSelectAll: () => {
    selectAllVisible()
  },
  onHelp: () => {
    openHelp()
  },
  onTeamAssign: (index: number) => {
    if (teams.value[index] && selectedTicket.value) {
      handleReassign(teams.value[index])
    }
  },
})

// Handle confirm prediction
function handleConfirm(team: string) {
  if (!selectedTicket.value) return

  labelTicket(
    { ticketId: selectedTicket.value.id, label: team },
    {
      onSuccess: () => {
        setTimeout(() => selectNext(), 600)
      },
      onError: () => {
        toast.error('Failed to label ticket')
      },
    }
  )
}

// Handle reassign
function handleReassign(team: string) {
  if (!selectedTicket.value) return

  labelTicket(
    { ticketId: selectedTicket.value.id, label: team },
    {
      onSuccess: () => {
        setTimeout(() => selectNext(), 600)
      },
      onError: () => {
        toast.error('Failed to reassign ticket')
      },
    }
  )
}

// Bulk action inline feedback
const bulkFeedback = ref<string | null>(null)
let bulkFeedbackTimer: ReturnType<typeof setTimeout> | undefined

// Handle bulk approve
function handleBulkApprove() {
  if (!hasBulkSelection.value) return

  const ticketIds = bulkSelectedTickets.value.map((t) => t.id)
  const defaultTeam = teams.value[0] || 'Default Team'

  bulkLabel(
    { ticketIds, label: defaultTeam },
    {
      onSuccess: () => {
        bulkFeedback.value = `${ticketIds.length} tickets assigned to ${defaultTeam}`
        clearTimeout(bulkFeedbackTimer)
        bulkFeedbackTimer = setTimeout(() => {
          bulkFeedback.value = null
        }, 2500)
      },
      onError: () => {
        toast.error('Bulk action failed')
      },
    }
  )
}

// Toggle mock data mode
function toggleMockData() {
  setUseMockData(!useMockData.value)
  refresh()
}

// Grouped shortcuts by category for help modal
const groupedShortcuts = computed(() => {
  const groups: Record<string, typeof shortcuts.value> = {
    navigation: [],
    actions: [],
    bulk: [],
    general: [],
  }
  for (const shortcut of shortcuts.value) {
    const category = shortcut.category || 'general'
    if (!groups[category]) groups[category] = []
    groups[category].push(shortcut)
  }
  return groups
})
</script>

<template>
  <div class="ticket-queue">
    <!-- Header -->
    <header class="ticket-queue__header">
      <div class="ticket-queue__header-left">
        <h1 class="ticket-queue__title">
          <Inbox :size="24" />
          Ticket Queue
        </h1>
        <Badge v-if="isMockMode" variant="warning">
          <Sparkles :size="12" />
          Mock Data
        </Badge>
      </div>

      <div class="ticket-queue__header-actions">
        <InstanceSelector
          :model-value="String(selectedInstanceId || '')"
          placeholder="Select instance..."
          @update:model-value="(v) => instanceStore.setInstance(v)"
        />

        <Button variant="ghost" size="sm" @click="toggleMockData">
          {{ isMockMode ? 'Use API' : 'Use Mock' }}
        </Button>

        <Button variant="outline" size="sm" @click="refresh" :disabled="isLoading">
          <RefreshCw :size="14" :class="{ 'animate-spin': isLoading }" />
          Refresh
        </Button>

        <Button variant="ghost" size="icon" @click="openHelp" title="Keyboard shortcuts">
          <Keyboard :size="16" />
        </Button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="ticket-queue__main">
      <!-- Left Panel: Ticket List -->
      <div class="ticket-queue__list-panel">
        <!-- Filter Bar -->
        <TicketFilterBar
          :filters="filters"
          :status-counts="statusCounts"
          :teams="teams"
          @update:status="(v) => setFilter('status', v)"
          @update:search="(v) => setFilter('search', v)"
          @update:team="(v) => setFilter('team', v)"
          @update:sort-order="(v) => setFilter('sortOrder', v)"
          @reset="resetFilters"
        />

        <!-- Bulk Actions Bar -->
        <Transition name="bulk-bar">
        <div v-if="hasBulkSelection" class="ticket-queue__bulk-bar">
          <span class="ticket-queue__bulk-count">
            <CheckSquare :size="14" />
            {{ bulkSelectedTickets.length }} selected
          </span>
          <div class="ticket-queue__bulk-actions">
            <Button variant="default" size="sm" @click="handleBulkApprove" :disabled="isBulkLabeling">
              Approve All
            </Button>
            <Button variant="ghost" size="sm" @click="clearBulkSelection">
              <X :size="14" />
              Clear
            </Button>
          </div>
        </div>
        </Transition>

        <!-- Bulk Feedback Banner -->
        <Transition name="bulk-bar">
          <div v-if="bulkFeedback" class="ticket-queue__bulk-feedback">
            <CheckCircle :size="14" />
            {{ bulkFeedback }}
          </div>
        </Transition>

        <!-- Loading State -->
        <div v-if="isLoading" class="ticket-queue__loading">
          <Progress :value="undefined" />
          <span>Loading tickets...</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="tickets.length === 0" class="ticket-queue__empty">
          <Inbox :size="48" class="ticket-queue__empty-icon" />
          <h3>No tickets found</h3>
          <p v-if="filters.status !== 'all' || filters.search">
            Try adjusting your filters
          </p>
          <p v-else>
            No tickets are available for this instance
          </p>
        </div>

        <!-- Ticket List -->
        <div v-else class="ticket-queue__list">
          <TransitionGroup name="ticket-list" tag="div">
            <TicketListItem
              v-for="ticket in tickets"
              :key="ticket.id"
              :ticket="ticket"
              :selected="selectedTicket?.id === ticket.id"
              :bulk-selected="store.bulkSelection.has(ticket.id)"
              :show-bulk-checkbox="hasBulkSelection"
              :recently-labeled="store.recentlyLabeled.has(ticket.id)"
              @select="selectTicket(ticket.id)"
              @toggle-bulk="toggleBulkSelect(ticket.id)"
            />
          </TransitionGroup>
        </div>
      </div>

      <!-- Right Panel: Detail View -->
      <div class="ticket-queue__detail-panel">
        <TicketDetailPanel
          :ticket="selectedTicket"
          :instance-id="selectedInstanceId"
          :teams="teams"
          :show-xai="true"
          @close="selectTicket(null)"
          @confirm="handleConfirm"
          @reassign="handleReassign"
          @next="selectNext"
        />
      </div>
    </div>

    <!-- Keyboard Shortcuts Modal -->
    <Teleport to="body">
      <div v-if="isHelpOpen" class="shortcuts-modal" @click.self="closeHelp">
        <div class="shortcuts-modal__content">
          <header class="shortcuts-modal__header">
            <h2>
              <Keyboard :size="20" />
              Keyboard Shortcuts
            </h2>
            <Button variant="ghost" size="icon" @click="closeHelp">
              <X :size="18" />
            </Button>
          </header>

          <div class="shortcuts-modal__body">
            <div
              v-for="(shortcuts, category) in groupedShortcuts"
              :key="category"
              class="shortcuts-modal__group"
            >
              <h3 class="shortcuts-modal__group-title">{{ category }}</h3>
              <div class="shortcuts-modal__list">
                <div
                  v-for="shortcut in shortcuts"
                  :key="shortcut.key"
                  class="shortcuts-modal__item"
                >
                  <kbd class="shortcuts-modal__key">{{ formatShortcutKey(shortcut) }}</kbd>
                  <span class="shortcuts-modal__desc">{{ shortcut.description }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped lang="scss">
.ticket-queue {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1rem;
    background: var(--card);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  &__header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
  }

  &__header-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__main {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  &__list-panel {
    display: flex;
    flex-direction: column;
    width: 40%;
    min-width: 320px;
    max-width: 500px;
    border-right: 1px solid var(--border);
    background: var(--card);
  }

  &__bulk-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 1rem;
    background: color-mix(in srgb, var(--info) 10%, var(--card));
    border-bottom: 1px solid var(--border);
  }

  &__bulk-count {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--foreground);
  }

  &__bulk-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__bulk-feedback {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    padding: 0.5rem 1rem;
    background: color-mix(in srgb, var(--success, #22c55e) 10%, var(--card));
    color: var(--success, #22c55e);
    font-size: 0.8125rem;
    font-weight: 500;
    border-bottom: 1px solid var(--border);
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem 1rem;
    color: var(--muted-foreground);
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 3rem 1rem;
    text-align: center;
    color: var(--muted-foreground);

    &-icon {
      opacity: 0.5;
      margin-bottom: 0.5rem;
    }

    h3 {
      margin: 0;
      font-size: 1rem;
      font-weight: 600;
      color: var(--foreground);
    }

    p {
      margin: 0;
      font-size: 0.875rem;
    }
  }

  &__list {
    flex: 1;
    overflow-y: auto;
    position: relative;
  }

  &__detail-panel {
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }
}

// Keyboard shortcuts modal
.shortcuts-modal {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);

  &__content {
    width: 100%;
    max-width: 480px;
    max-height: 80vh;
    background: var(--card);
    border-radius: var(--radius);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    overflow: hidden;
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border);

    h2 {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin: 0;
      font-size: 1.125rem;
      font-weight: 600;
    }
  }

  &__body {
    padding: 1rem 1.25rem;
    overflow-y: auto;
    max-height: calc(80vh - 60px);
  }

  &__group {
    &:not(:last-child) {
      margin-bottom: 1.5rem;
    }
  }

  &__group-title {
    margin: 0 0 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted-foreground);
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  &__key {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 2rem;
    padding: 0.25rem 0.5rem;
    background: var(--muted);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-family: ui-monospace, monospace;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--foreground);
  }

  &__desc {
    font-size: 0.875rem;
    color: var(--muted-foreground);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// Responsive
@media (max-width: 768px) {
  .ticket-queue {
    &__main {
      flex-direction: column;
    }

    &__list-panel {
      width: 100%;
      max-width: none;
      max-height: 50vh;
      border-right: none;
      border-bottom: 1px solid var(--border);
    }

    &__detail-panel {
      flex: 1;
    }
  }
}

// Ticket list TransitionGroup
.ticket-list-enter-active,
.ticket-list-leave-active {
  transition: all 0.3s ease;
}
.ticket-list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.ticket-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
.ticket-list-leave-active {
  position: absolute;
  width: 100%;
}
.ticket-list-move {
  transition: transform 0.3s ease;
}

// Bulk bar transition
.bulk-bar-enter-active,
.bulk-bar-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.bulk-bar-enter-from,
.bulk-bar-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.bulk-bar-enter-to,
.bulk-bar-leave-from {
  max-height: 60px;
}
</style>
