<script setup lang="ts">
import { computed } from 'vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import { Search, X, SlidersHorizontal } from 'lucide-vue-next'
import type { TicketStatus, SortOrder, QueueFilters } from '@/stores/useTicketQueueStore'

export interface FilterBarProps {
  filters: QueueFilters
  statusCounts: Record<TicketStatus | 'all', number>
  teams?: string[]
}

const props = defineProps<FilterBarProps>()

const emit = defineEmits<{
  (e: 'update:status', value: TicketStatus | 'all'): void
  (e: 'update:search', value: string): void
  (e: 'update:team', value: string | null): void
  (e: 'update:sortOrder', value: SortOrder): void
  (e: 'reset'): void
}>()

const statusTabs: { value: TicketStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'unlabeled', label: 'Unlabeled' },
  { value: 'pending-review', label: 'Pending Review' },
  { value: 'auto-classified', label: 'Auto-Classified' },
  { value: 'resolved', label: 'Resolved' },
]

const sortOptions = [
  { value: 'newest', label: 'Newest First' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'confidence-high', label: 'Confidence (High → Low)' },
  { value: 'confidence-low', label: 'Confidence (Low → High)' },
]

const teamOptions = computed(() => {
  if (!props.teams?.length) return []
  return [
    { value: '', label: 'All Teams' },
    ...props.teams.map((t) => ({ value: t, label: t })),
  ]
})

const hasActiveFilters = computed(() => {
  return (
    props.filters.status !== 'all' ||
    props.filters.search.trim() !== '' ||
    props.filters.team !== null
  )
})

function handleSearchInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:search', target.value)
}

function clearSearch() {
  emit('update:search', '')
}
</script>

<template>
  <div class="filter-bar">
    <!-- Status Tabs -->
    <div class="filter-bar__tabs">
      <button
        v-for="tab in statusTabs"
        :key="tab.value"
        :class="[
          'filter-bar__tab',
          { 'filter-bar__tab--active': filters.status === tab.value },
        ]"
        @click="$emit('update:status', tab.value)"
      >
        <span class="filter-bar__tab-label">{{ tab.label }}</span>
        <Badge
          v-if="statusCounts[tab.value] > 0"
          :variant="filters.status === tab.value ? 'default' : 'secondary'"
          size="sm"
        >
          {{ statusCounts[tab.value] }}
        </Badge>
      </button>
    </div>

    <!-- Search and Filters Row -->
    <div class="filter-bar__controls">
      <!-- Search -->
      <div class="filter-bar__search">
        <Search :size="16" class="filter-bar__search-icon" />
        <input
          type="text"
          :value="filters.search"
          placeholder="Search tickets..."
          class="filter-bar__search-input"
          @input="handleSearchInput"
        />
        <button
          v-if="filters.search"
          class="filter-bar__search-clear"
          @click="clearSearch"
        >
          <X :size="14" />
        </button>
      </div>

      <!-- Team Filter -->
      <Select
        v-if="teams && teams.length > 0"
        :model-value="filters.team || ''"
        :options="teamOptions"
        placeholder="All Teams"
        class="filter-bar__team-select"
        @update:model-value="$emit('update:team', $event || null)"
      />

      <!-- Sort -->
      <Select
        :model-value="filters.sortOrder"
        :options="sortOptions"
        class="filter-bar__sort-select"
        @update:model-value="$emit('update:sortOrder', $event as SortOrder)"
      />

      <!-- Reset Button -->
      <Button
        v-if="hasActiveFilters"
        variant="ghost"
        size="sm"
        @click="$emit('reset')"
      >
        <X :size="14" />
        Clear Filters
      </Button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--card);
  border-bottom: 1px solid var(--border);

  &__tabs {
    display: flex;
    gap: 0.25rem;
    overflow-x: auto;
    scrollbar-width: thin;

    &::-webkit-scrollbar {
      height: 4px;
    }
  }

  &__tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border: none;
    background: transparent;
    color: var(--muted-foreground);
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    border-radius: var(--radius);
    transition: all 0.15s ease;

    &:hover {
      background: var(--accent);
      color: var(--accent-foreground);
    }

    &--active {
      background: var(--primary);
      color: var(--primary-foreground);

      &:hover {
        background: var(--primary);
        opacity: 0.9;
      }
    }
  }

  &__controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  &__search {
    position: relative;
    flex: 1;
    min-width: 200px;
    max-width: 320px;
  }

  &__search-icon {
    position: absolute;
    left: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--muted-foreground);
    pointer-events: none;
  }

  &__search-input {
    width: 100%;
    padding: 0.5rem 2rem 0.5rem 2.25rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--background);
    font-size: 0.875rem;
    color: var(--foreground);

    &::placeholder {
      color: var(--muted-foreground);
    }

    &:focus {
      outline: none;
      border-color: var(--ring);
      box-shadow: 0 0 0 2px color-mix(in srgb, var(--ring) 20%, transparent);
    }
  }

  &__search-clear {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.25rem;
    height: 1.25rem;
    border: none;
    background: var(--muted);
    border-radius: 50%;
    color: var(--muted-foreground);
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      background: var(--accent);
      color: var(--foreground);
    }
  }

  &__team-select,
  &__sort-select {
    min-width: 140px;
  }
}
</style>
