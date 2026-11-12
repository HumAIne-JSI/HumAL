<template>
  <div class="sidebar-wrapper" :class="{ 'sidebar-wrapper--collapsed': isCollapsed }">
    <aside class="sidebar">
      <div class="sidebar__header">
        <div v-if="!isCollapsed" class="sidebar__header-text">
          <h1 class="sidebar__title">IT Ticket Manager</h1>
          <p class="sidebar__subtitle">AI-Powered Ticket System</p>
        </div>
        <button
          class="sidebar__toggle"
          type="button"
          :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="!isCollapsed"
          @click="toggleCollapsed"
        >
          <PanelLeftClose v-if="!isCollapsed" class="sidebar__toggle-icon" />
          <PanelLeftOpen v-else class="sidebar__toggle-icon" />
        </button>
      </div>

      <div v-if="!isCollapsed" class="sidebar__instance">
        <label class="sidebar__instance-label">Active Project</label>
        <InstanceSelector
          :model-value="String(instanceStore.selectedInstanceId || '')"
          placeholder="Select project..."
          size="sm"
          @update:model-value="handleInstanceChange"
        />
      </div>

      <nav class="sidebar__nav" aria-label="Main navigation">
        <div class="sidebar__nav-tier" role="group" aria-label="Level 1: Triage and routing">
          <div v-if="!isCollapsed" class="sidebar__tier-label">
            <span class="sidebar__tier-number" aria-hidden="true">01</span>
            <div class="sidebar__tier-text">
              <h2 class="sidebar__tier-level">Level 1: Triage &amp; routing</h2>
              <p class="sidebar__tier-description">HumAIne Core · TRL 5</p>
            </div>
          </div>
          <template v-for="item in tier1Items" :key="item.path">
            <a
              v-if="item.newTab"
              :href="resolveHref(item.path)"
              target="_blank"
              rel="noopener"
              class="sidebar__link"
              :title="isCollapsed ? `${item.label} (opens in a new tab)` : undefined"
              :aria-label="`${item.label} (opens in a new tab)`"
            >
              <component :is="item.icon" class="sidebar__icon" />
              <span v-if="!isCollapsed" class="sidebar__label">{{ item.label }}</span>
              <ExternalLink v-if="!isCollapsed" class="sidebar__link-external" />
            </a>
            <RouterLink
              v-else
              :to="item.path"
              class="sidebar__link"
              :class="{ 'sidebar__link--active': isActive(item.path) }"
              :title="isCollapsed ? item.label : undefined"
              :aria-label="isCollapsed ? item.label : undefined"
            >
              <component :is="item.icon" class="sidebar__icon" />
              <span v-if="!isCollapsed" class="sidebar__label">{{ item.label }}</span>
            </RouterLink>
          </template>
        </div>

        <div class="sidebar__nav-tier" role="group" aria-label="Level 2: Resolution support">
          <div v-if="!isCollapsed" class="sidebar__tier-label">
            <span class="sidebar__tier-number" aria-hidden="true">02</span>
            <div class="sidebar__tier-text">
              <h2 class="sidebar__tier-level">Level 2: Resolution support</h2>
              <p class="sidebar__tier-description">Exploratory preview</p>
            </div>
          </div>
          <template v-for="item in tier2Items" :key="item.path">
            <a
              v-if="item.newTab"
              :href="resolveHref(item.path)"
              target="_blank"
              rel="noopener"
              class="sidebar__link"
              :title="isCollapsed ? `${item.label} (opens in a new tab)` : undefined"
              :aria-label="`${item.label} (opens in a new tab)`"
            >
              <component :is="item.icon" class="sidebar__icon" />
              <span v-if="!isCollapsed" class="sidebar__label">{{ item.label }}</span>
              <ExternalLink v-if="!isCollapsed" class="sidebar__link-external" />
            </a>
            <RouterLink
              v-else
              :to="item.path"
              class="sidebar__link"
              :class="{ 'sidebar__link--active': isActive(item.path) }"
              :title="isCollapsed ? item.label : undefined"
              :aria-label="isCollapsed ? item.label : undefined"
            >
              <component :is="item.icon" class="sidebar__icon" />
              <span v-if="!isCollapsed" class="sidebar__label">{{ item.label }}</span>
            </RouterLink>
          </template>
        </div>
      </nav>

      <div v-if="!isCollapsed" class="sidebar__footer">
        <button type="button" class="sidebar__tour" @click="tutorialStore.runChain()">
          <Play class="sidebar__tour-icon" />
          <span>Tour guide</span>
        </button>
        <MockToggle />
        <div class="sidebar__account">
          <span class="sidebar__account-user" :title="accountLabel">{{ accountLabel }}</span>
          <button type="button" class="sidebar__logout" @click="handleLogout">
            <LogOut class="sidebar__logout-icon" />
            <span>Sign out</span>
          </button>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PanelLeftClose, PanelLeftOpen, LogOut, ExternalLink, Play } from 'lucide-vue-next'
import { navItems } from '../router'
import InstanceSelector from './InstanceSelector.vue'
import MockToggle from './MockToggle.vue'
import { useInstanceStore } from '@/stores/useInstanceStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { useTutorialStore } from '@/stores/useTutorialStore'

const STORAGE_KEY = 'humal-sidebar-collapsed'
const EXPAND_EVENT = 'humal:tutorial-expand-sidebar'

const route = useRoute()
const router = useRouter()
const instanceStore = useInstanceStore()
const authStore = useAuthStore()
const tutorialStore = useTutorialStore()

const accountLabel = computed(() => authStore.user?.username || 'System user')

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}

const isCollapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')

watch(isCollapsed, (value) => {
  localStorage.setItem(STORAGE_KEY, String(value))
})

const toggleCollapsed = () => {
  isCollapsed.value = !isCollapsed.value
}

// The tutorial relies on the sidebar (project selector, nav). When the sidebar
// is collapsed, expand it so the guided steps are visible.
onMounted(() => {
  window.addEventListener(EXPAND_EVENT, handleTutorialExpand)
})

onBeforeUnmount(() => {
  window.removeEventListener(EXPAND_EVENT, handleTutorialExpand)
})

const handleTutorialExpand = () => {
  isCollapsed.value = false
}

const handleInstanceChange = (value: string) => {
  instanceStore.setInstance(value)
}

const isActive = (path: string): boolean => {
  return route.path === path
}

// Absolute href (respecting the router base) for entries that open in a new tab.
const resolveHref = (path: string): string => router.resolve(path).href

// Split nav items into two tiers
// Tier 1: Home, New Project, Ticket Queue, Manual Queue (core triage and routing)
// Tier 2: Ticket Evolution, Performance (exploratory/resolution support)
const tier1Items = computed(() =>
  navItems.filter(item =>
    ['/', '/training', '/queue', '/manual'].includes(item.path)
  )
)

const tier2Items = computed(() =>
  navItems.filter(item =>
    ['/ticket-resolution', '/analytics'].includes(item.path)
  )
)
</script>

<style lang="scss" scoped>
.sidebar-wrapper {
  position: relative;
  display: flex;
  width: 22rem;
  flex-shrink: 0;
  transition: width 0.2s ease;

  &--collapsed {
    width: 4rem;
  }
}

.sidebar {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
  background-color: var(--sidebar);
  border-right: 1px solid var(--sidebar-border);
  overflow-y: auto;
  overflow-x: hidden;

  &__header {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 1.5rem;
    border-bottom: 1px solid var(--sidebar-border);

    .sidebar-wrapper--collapsed & {
      padding: 1rem 0.5rem;
      justify-content: center;
    }
  }

  &__header-text {
    flex: 1;
    min-width: 0;
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

  &__toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    padding: 0;
    border: none;
    border-radius: var(--radius);
    background-color: transparent;
    color: var(--sidebar-foreground);
    cursor: pointer;
    flex-shrink: 0;
    transition: background-color 0.15s;

    &:hover {
      background-color: var(--sidebar-accent);
    }
  }

  &__toggle-icon {
    width: 1.125rem;
    height: 1.125rem;
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
    min-height: 0;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0;

    .sidebar-wrapper--collapsed & {
      padding: 1rem 0.5rem;
    }
  }

  &__nav-tier {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;

    &:not(:last-child) {
      margin-bottom: 0.75rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--sidebar-border);
    }
  }

  &__tier-label {
    display: flex;
    align-items: flex-start;
    gap: 0.625rem;
    padding: 0.5rem 0.5rem 0.75rem;
  }

  &__tier-number {
    display: grid;
    place-items: center;
    flex-shrink: 0;
    width: 1.75rem;
    height: 1.75rem;
    border: 1px solid var(--sidebar-border);
    border-radius: 0.5rem;
    background: var(--sidebar-accent);
    color: var(--sidebar-foreground);
    font-size: 0.7rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  &__tier-text {
    min-width: 0;
    overflow: hidden;
  }

  &__tier-level {
    margin: 0;
    font-size: 0.8125rem;
    font-weight: 600;
    line-height: 1.35;
    color: var(--sidebar-foreground);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__tier-description {
    margin: 0.2rem 0 0;
    font-size: 0.7rem;
    line-height: 1.4;
    color: var(--muted-foreground);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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
    min-width: 0;
    overflow: hidden;

    &:hover {
      background-color: var(--sidebar-accent);
    }

    &:focus-visible {
      outline: 2px solid var(--sidebar-ring);
      outline-offset: -2px;
    }

    &--active {
      background-color: var(--sidebar-accent);
      color: var(--sidebar-primary);
    }

    .sidebar-wrapper--collapsed & {
      justify-content: center;
      padding: 0.75rem;
      overflow: visible;
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
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  &__link-external {
    width: 0.875rem;
    height: 0.875rem;
    margin-left: auto;
    color: var(--muted-foreground);
    flex-shrink: 0;
  }

  &__footer {
    padding: 1rem;
    border-top: 1px solid var(--sidebar-border);
  }

  &__tour {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.75rem;
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
    color: var(--sidebar-primary, inherit);
    background: transparent;
    border: 1px dashed var(--sidebar-border);
    border-radius: var(--radius);
    cursor: pointer;

    &:hover {
      background-color: var(--sidebar-accent);
    }
  }

  &__tour-icon {
    width: 0.875rem;
    height: 0.875rem;
  }

  &__account {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }

  &__account-user {
    font-size: 0.75rem;
    color: var(--muted-foreground);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__logout {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    color: var(--sidebar-foreground, inherit);
    background: transparent;
    border: 1px solid var(--sidebar-border);
    border-radius: var(--radius);
    cursor: pointer;

    &:hover {
      background-color: var(--sidebar-accent, rgb(0 0 0 / 0.04));
    }
  }

  &__logout-icon {
    width: 0.875rem;
    height: 0.875rem;
  }
}
</style>
