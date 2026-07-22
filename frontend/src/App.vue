<template>
  <div class="app-layout" :class="{ 'app-layout--standalone': isStandalone }">
    <Navigation v-if="!isStandalone" />
    <header v-else class="app-standalone-bar">
      <HumaineLogo :height="30" :width="100" class="app-standalone-bar__logo" />
      <span class="app-standalone-bar__title">{{ standaloneTitle }}</span>
    </header>
    <main class="app-layout__main">
      <router-view />
    </main>
    <Toaster position="bottom-right" :duration="3000" rich-colors close-button />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navigation from '@/components/Navigation.vue'
import HumaineLogo from '@/components/HumaineLogo.vue'
import { Toaster } from 'vue-sonner'
import 'vue-sonner/style.css'
import { useMockModeStore } from '@/stores/useMockModeStore'

// Initialize mock mode store early to sync all mock flags
useMockModeStore()

// Routes flagged `standalone` render detached from the app shell (no sidebar) —
// used for features that open in their own browser tab, like Ticket Evolution.
const route = useRoute()
const isStandalone = computed(() => Boolean(route.meta?.standalone))
const standaloneTitle = computed(() => (route.meta?.label as string) || 'Workspace')
</script>

<style lang="scss">
.app-layout {
  display: flex;
  height: 100vh;
  background-color: #f9fafb;

  &--standalone {
    flex-direction: column;
  }

  &__main {
    flex: 1;
    overflow: auto;
    padding: 1rem;
  }
}

.app-standalone-bar {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  flex-shrink: 0;
  padding: 0.625rem 1.5rem;
  background-color: var(--sidebar, #ffffff);
  border-bottom: 1px solid var(--sidebar-border, #e5e7eb);

  &__logo {
    color: var(--sidebar-foreground, #1f2937);
    flex-shrink: 0;
  }

  &__title {
    padding-left: 0.875rem;
    border-left: 1px solid var(--sidebar-border, #e5e7eb);
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--foreground, #111827);
  }
}
</style>
