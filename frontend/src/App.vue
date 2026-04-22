<template>
  <div class="app-layout">
    <Navigation />
    <main class="app-layout__main">
      <router-view />
    </main>
    <Toaster position="bottom-right" :duration="3000" />
  </div>
</template>

<script setup lang="ts">
import Navigation from '@/components/Navigation.vue'
import { Toaster } from 'vue-sonner'
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
}
</style>
