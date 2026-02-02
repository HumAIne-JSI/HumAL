<template>
  <div class="app-layout">
    <Navigation />
    <main class="app-layout__main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Navigation from '@/components/Navigation.vue'
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
