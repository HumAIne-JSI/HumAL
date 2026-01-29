<script setup lang="ts">
import { useRoute } from 'vue-router'
import { onMounted } from 'vue'

const route = useRoute()

onMounted(() => {
  console.error('404 Error: User attempted to access non-existent route:', route.path)
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-100">
    <div class="text-center">
      <h1 class="mb-4 text-4xl font-bold">404</h1>
      <p class="mb-4 text-xl text-gray-600">Oops! Page not found</p>
      <RouterLink to="/" class="text-blue-500 underline hover:text-blue-700">
        Return to Home
      </RouterLink>
    </div>
  </div>
</template>
