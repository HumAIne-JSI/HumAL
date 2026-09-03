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

      <nav class="sidebar__nav">
        <template v-for="item in navItems" :key="item.path">
          <a
            v-if="item.newTab"
            :href="resolveHref(item.path)"
            target="_blank"
            rel="noopener"
            class="sidebar__link"
            :title="isCollapsed ? `${item.label} (opens in a new tab)` : undefined"
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
          >
            <component :is="item.icon" class="sidebar__icon" />
            <span v-if="!isCollapsed" class="sidebar__label">{{ item.label }}</span>
          </RouterLink>
        </template>
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
</script>

<style lang="scss" scoped>
.sidebar-wrapper {
  position: relative;
  display: flex;
  width: 16rem;
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
  overflow: hidden;

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
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;

    .sidebar-wrapper--collapsed & {
      padding: 1rem 0.5rem;
    }
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

    .sidebar-wrapper--collapsed & {
      justify-content: center;
      padding: 0.75rem;
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
