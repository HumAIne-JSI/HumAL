<script setup lang="ts">
import { computed, ref } from 'vue'
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

const showFiltersPanel = ref(false)

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
        <span
          v-if="statusCounts[tab.value] > 0"
          class="filter-bar__tab-count"
        >
          {{ statusCounts[tab.value] }}
        </span>
      </button>
    </div>

    <!-- Search and Filters Row -->
    <div class="filter-bar__controls">
      <!-- Search -->
      <div class="filter-bar__search">
        <Search :size="14" class="filter-bar__search-icon" />
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

      <!-- Filters toggle -->
      <Button
        variant="ghost"
        size="sm"
        @click="showFiltersPanel = !showFiltersPanel"
        :class="{ 'filter-bar__filters-active': hasActiveFilters }"
      >
        <SlidersHorizontal :size="14" />
        Filters
      </Button>

      <!-- Reset Button -->
      <Button
        v-if="hasActiveFilters"
        variant="ghost"
        size="sm"
        @click="$emit('reset')"
      >
        <X :size="14" />
        Clear
      </Button>
    </div>

    <!-- Collapsible Filters -->
    <div v-if="showFiltersPanel" class="filter-bar__panel">
      <Select
        v-if="teams && teams.length > 0"
        :model-value="filters.team || ''"
        :options="teamOptions"
        placeholder="All Teams"
        class="filter-bar__panel-select"
        @update:model-value="$emit('update:team', $event || null)"
      />
      <Select
        :model-value="filters.sortOrder"
        :options="sortOptions"
        class="filter-bar__panel-select"
        @update:model-value="$emit('update:sortOrder', $event as SortOrder)"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--card);
  border-bottom: 1px solid var(--border);

  &__tabs {
    display: flex;
    gap: 0.125rem;
    overflow-x: auto;
    scrollbar-width: thin;

    &::-webkit-scrollbar {
      height: 4px;
    }
  }

  &__tab {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.625rem;
    border: none;
    background: transparent;
    color: var(--muted-foreground);
    font-size: 0.8125rem;
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

      .filter-bar__tab-count {
        opacity: 0.8;
      }
    }
  }

  &__tab-count {
    font-size: 0.75rem;
    opacity: 0.6;
    font-variant-numeric: tabular-nums;
  }

  &__controls {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  &__search {
    position: relative;
    flex: 1;
    min-width: 160px;
    max-width: 280px;
  }

  &__search-icon {
    position: absolute;
    left: 0.625rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--muted-foreground);
    pointer-events: none;
  }

  &__search-input {
    width: 100%;
    padding: 0.375rem 1.75rem 0.375rem 2rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--background);
    font-size: 0.8125rem;
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
    right: 0.375rem;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.125rem;
    height: 1.125rem;
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

  &__filters-active {
    color: var(--primary);
  }

  &__panel {
    display: flex;
    gap: 0.5rem;
    padding-top: 0.25rem;
  }

  &__panel-select {
    min-width: 140px;
  }
}
</style>
