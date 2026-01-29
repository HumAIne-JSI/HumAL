<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Brain, BookOpen, Zap, Menu } from 'lucide-vue-next'

const route = useRoute()
const isOpen = ref(false)

const navItems = [
  { path: '/', label: 'Home', icon: Brain },
  { path: '/training', label: 'Model Training', icon: BookOpen },
  { path: '/dispatch-labeling', label: 'Dispatch Labeling', icon: BookOpen },
  { path: '/ticket-resolution', label: 'Ticket Resolution', icon: BookOpen },
  { path: '/inference', label: 'Inference', icon: Zap },
]

const isActive = (path: string) => route.path === path
</script>

<template>
  <nav class="ml-nav-gradient shadow-lg sticky top-0 z-50 backdrop-blur-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Brand -->
        <RouterLink to="/" class="flex items-center space-x-3">
          <span class="text-white font-bold text-xl">Smart Ticketing System</span>
        </RouterLink>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center space-x-1">
          <RouterLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            :class="[
              'px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center space-x-2',
              isActive(item.path)
                ? 'bg-white/20 text-white shadow-md'
                : 'text-white/80 hover:text-white hover:bg-white/10'
            ]"
          >
            <component :is="item.icon" class="w-4 h-4" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>

        <!-- Mobile menu button -->
        <div class="md:hidden">
          <button
            @click="isOpen = !isOpen"
            class="text-white hover:text-white/80 p-2 rounded-md"
          >
            <Menu class="w-6 h-6" />
          </button>
        </div>
      </div>

      <!-- Mobile Navigation -->
      <div v-if="isOpen" class="md:hidden pb-4">
        <div class="flex flex-col space-y-1">
          <RouterLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            @click="isOpen = false"
            :class="[
              'px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center space-x-2',
              isActive(item.path)
                ? 'bg-white/20 text-white shadow-md'
                : 'text-white/80 hover:text-white hover:bg-white/10'
            ]"
          >
            <component :is="item.icon" class="w-4 h-4" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
      </div>
    </div>
  </nav>
</template>
