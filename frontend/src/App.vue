<template>
  <div class="app-layout">
    <Navigation v-if="showSidebar" :scope="navScope" />
    <main class="app-layout__main">
      <router-view />
    </main>
    <Toaster position="bottom-right" :duration="3000" rich-colors close-button />
    <TutorialHost />
  </div>
</template>

<script setup lang="ts">
import Navigation from '@/components/Navigation.vue'
import TutorialHost from '@/components/TutorialHost.vue'
import { useMockModeStore } from '@/stores/useMockModeStore'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Toaster } from 'vue-sonner'
import 'vue-sonner/style.css'

// Initialize mock mode store early to sync all mock flags
useMockModeStore()

// Routes flagged `app: 'specialist'` belong to the Tier 2 workspace, which has its own
// sidebar (Tier 2 entries only) and its own sign-in, like a separate app.
const route = useRoute()
const navScope = computed(() => (route.meta?.app === 'specialist' ? 'specialist' : 'main'))

// Routes flagged `hideSidebar` (e.g. login) keep the regular shell minus the sidebar. `matched`
// is empty until the first navigation resolves; waiting for it stops the sidebar from flashing
// on routes that hide it.
const showSidebar = computed(() => route.matched.length > 0 && !route.meta?.hideSidebar)
</script>

<style lang="scss">
.app-layout {
  display: flex;
  height: 100vh;
  background-color: #f9fafb;

  &__main {
    flex: 1;
    overflow: auto;
    padding: 1rem;
  }

  &__timer { position: fixed; right: 1rem; bottom: 1rem; z-index: 20; }
}
</style>
