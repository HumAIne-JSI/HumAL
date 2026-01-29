<script setup lang="ts">
import { Toaster } from '@/components/ui/sonner'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <Navigation />
    <main class="flex-1">
      <RouterView />
    </main>
    <Toaster />
  </div>
</template>
