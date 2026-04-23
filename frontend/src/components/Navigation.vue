<template>
  <div class="sidebar-wrapper">
    <aside class="sidebar">
      <div class="sidebar__header">
        <h1 class="sidebar__title">IT Ticket Manager</h1>
        <p class="sidebar__subtitle">AI-Powered Ticket System</p>
      </div>

      <div class="sidebar__instance">
        <label class="sidebar__instance-label">Active Instance</label>
        <InstanceSelector
          :model-value="String(instanceStore.selectedInstanceId || '')"
          placeholder="Select instance..."
          size="sm"
          @update:model-value="handleInstanceChange"
        />
      </div>

      <nav class="sidebar__nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="sidebar__link"
          :class="{ 'sidebar__link--active': isActive(item.path) }"
        >
          <component :is="item.icon" class="sidebar__icon" />
          <span class="sidebar__label">{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar__footer">
        <MockToggle />
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { navItems } from '../router'
import InstanceSelector from './InstanceSelector.vue'
import MockToggle from './MockToggle.vue'
import { useInstanceStore } from '@/stores/useInstanceStore'

const route = useRoute()
const instanceStore = useInstanceStore()

const handleInstanceChange = (value: string) => {
  instanceStore.setInstance(value)
}

const isActive = (path: string): boolean => {
  return route.path === path
}
</script>

<style lang="scss" scoped>
.sidebar-wrapper {
  position: relative;
  display: flex;
  width: 16rem;
  flex-shrink: 0;
}

.sidebar {
  display: flex;
  flex-direction: column;
  width: 16rem;
  min-width: 16rem;
  background-color: var(--sidebar);
  border-right: 1px solid var(--sidebar-border);
  &__header {
    padding: 1.5rem;
    border-bottom: 1px solid var(--sidebar-border);
  }

  &__title {
    font-size: 1.25rem;
    font-weight: var(--font-weight-medium);
    color: var(--sidebar-foreground);
    margin: 0;
    white-space: nowrap;
  }

  &__subtitle {
    font-size: 0.875rem;
    color: var(--muted-foreground);
    margin: 0.25rem 0 0;
    white-space: nowrap;
  }

  &__instance {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--sidebar-border);
  }

  &__instance-label {
    display: block;
    font-size: 0.75rem;
    font-weight: var(--font-weight-medium);
    color: var(--muted-foreground);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &__nav {
    flex: 1;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: var(--radius);
    text-decoration: none;
    color: var(--sidebar-foreground);
    transition: background-color 0.15s, color 0.15s;
    white-space: nowrap;

    &:hover {
      background-color: var(--sidebar-accent);
    }

    &--active {
      background-color: var(--sidebar-accent);
      color: var(--sidebar-primary);
    }
  }

  &__icon {
    width: 1.25rem;
    height: 1.25rem;
    flex-shrink: 0;
  }

  &__label {
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
  }

  &__footer {
    padding: 1rem;
    border-top: 1px solid var(--sidebar-border);
  }
}
</style>
