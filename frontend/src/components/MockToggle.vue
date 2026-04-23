<template>
  <button
    class="mock-toggle"
    :class="{ 'mock-toggle--active': mockStore.mockEnabled }"
    :title="mockStore.mockEnabled ? 'Using mock data — click to use real API' : 'Using real API — click to use mock data'"
    @click="mockStore.toggle()"
  >
    <Database v-if="!mockStore.mockEnabled" class="mock-toggle__icon" />
    <FlaskConical v-else class="mock-toggle__icon" />
    <span class="mock-toggle__label">
      {{ mockStore.mockEnabled ? 'Mock' : 'Live' }}
    </span>
    <span
      class="mock-toggle__dot"
      :class="mockStore.mockEnabled ? 'mock-toggle__dot--mock' : 'mock-toggle__dot--live'"
    />
  </button>
</template>

<script setup lang="ts">
import { Database, FlaskConical } from 'lucide-vue-next'
import { useMockModeStore } from '@/stores/useMockModeStore'

const mockStore = useMockModeStore()
</script>

<style lang="scss" scoped>
.mock-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
  border: 1px solid var(--sidebar-border);
  background-color: var(--sidebar-accent);
  color: var(--sidebar-foreground);
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium);
  transition: background-color 0.15s, border-color 0.15s;
  width: 100%;

  &:hover {
    background-color: color-mix(in srgb, var(--sidebar-accent) 80%, var(--sidebar-foreground) 20%);
  }

  &--active {
    border-color: #f59e0b;
    background-color: color-mix(in srgb, var(--sidebar-accent) 85%, #f59e0b 15%);
  }

  &__icon {
    width: 0.875rem;
    height: 0.875rem;
    flex-shrink: 0;
  }

  &__label {
    flex: 1;
    text-align: left;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &__dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    flex-shrink: 0;

    &--live {
      background-color: #16a34a;
    }

    &--mock {
      background-color: #f59e0b;
    }
  }
}
</style>
