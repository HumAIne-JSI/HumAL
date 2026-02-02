<template>
  <div class="sidebar-wrapper">
    <aside
      :class="[
        'sidebar',
        { 'sidebar--collapsed': !isOpen }
      ]"
    >
      <div class="sidebar__header">
        <h1 class="sidebar__title">IT Ticket Manager</h1>
        <p class="sidebar__subtitle">AI-Powered Ticket System</p>
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
        <div class="sidebar__status">
          <p class="sidebar__status-label">Model Status</p>
          <p class="sidebar__status-value">● Active</p>
        </div>
      </div>
    </aside>

    <button
      class="toggle-btn"
      @click="toggle"
    >
      <X v-if="isOpen" class="toggle-btn__icon" />
      <Menu v-else class="toggle-btn__icon" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { Menu, X } from 'lucide-vue-next'
import { navItems } from '../router'

const route = useRoute()
const isOpen = ref(true)

const isActive = (path: string): boolean => {
  return route.path === path
}

const toggle = () => {
  isOpen.value = !isOpen.value
}
</script>

<style lang="scss" scoped>
.sidebar-wrapper {
  position: relative;
  display: flex;
  width: 16rem;
  flex-shrink: 0;
  transition: width 0.3s ease-in-out;

  &:has(.sidebar--collapsed) {
    width: 0;
  }
}

.sidebar {
  display: flex;
  flex-direction: column;
  width: 16rem;
  min-width: 16rem;
  background-color: var(--sidebar);
  border-right: 1px solid var(--sidebar-border);
  transform: translateX(0);
  transition: transform 0.3s ease-in-out;

  &--collapsed {
    transform: translateX(-100%);
  }

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

  &__status {
    padding: 0.75rem 1rem;
    background-color: var(--sidebar-accent);
    border-radius: var(--radius);
    white-space: nowrap;
  }

  &__status-label {
    font-size: 0.75rem;
    color: var(--muted-foreground);
    margin: 0;
  }

  &__status-value {
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
    color: var(--chart-2);
    margin: 0.25rem 0 0;
  }
}

.toggle-btn {
  position: absolute;
  top: 0.75rem;
  right: -2.5rem;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  background-color: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background-color 0.15s;

  &:hover {
    background-color: var(--muted);
  }

  &__icon {
    width: 1.25rem;
    height: 1.25rem;
    color: var(--foreground);
  }
}
</style>
