<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Brain, BookOpen, Zap, Github, Mail, ExternalLink } from 'lucide-vue-next'
import HumaineLogo from './HumaineLogo.vue'

const currentYear = new Date().getFullYear()

const navLinks = [
  { path: '/', label: 'Home', icon: Brain },
  { path: '/training', label: 'Model Training', icon: BookOpen },
  { path: '/dispatch-labeling', label: 'Dispatch Labeling', icon: BookOpen },
  { path: '/ticket-resolution', label: 'Ticket Resolution', icon: BookOpen },
  { path: '/inference', label: 'Inference', icon: Zap },
]
</script>

<template>
  <footer class="bg-card/50 backdrop-blur-sm border-t border-border mt-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid md:grid-cols-4 gap-8">
        <!-- Brand Section -->
        <div class="md:col-span-2">
          <div class="flex items-center space-x-3 mb-4">
            <HumaineLogo :width="150" :height="45" class="text-primary" />
          </div>
          <p class="text-muted-foreground max-w-md mb-4">
            Advanced machine learning platform for intelligent ticket classification and routing using active learning algorithms.
          </p>
          <div class="flex space-x-4">
            <a
              href="mailto:contact@humaine.ai"
              class="text-muted-foreground hover:text-primary transition-colors"
              aria-label="Email"
            >
              <Mail class="w-5 h-5" />
            </a>
            <a
              href="https://github.com/humaine"
              target="_blank"
              rel="noopener noreferrer"
              class="text-muted-foreground hover:text-primary transition-colors"
              aria-label="GitHub"
            >
              <Github class="w-5 h-5" />
            </a>
            <a
              href="https://humaine.ai"
              target="_blank"
              rel="noopener noreferrer"
              class="text-muted-foreground hover:text-primary transition-colors"
              aria-label="Website"
            >
              <ExternalLink class="w-5 h-5" />
            </a>
          </div>
        </div>

        <!-- Navigation Links -->
        <div>
          <h4 class="font-semibold mb-4">Platform</h4>
          <ul class="space-y-2">
            <li v-for="link in navLinks" :key="link.path">
              <RouterLink
                :to="link.path"
                class="text-muted-foreground hover:text-primary transition-colors flex items-center space-x-2 text-sm"
              >
                <component :is="link.icon" class="w-4 h-4" />
                <span>{{ link.label }}</span>
              </RouterLink>
            </li>
          </ul>
        </div>

        <!-- Resources -->
        <div>
          <h4 class="font-semibold mb-4">Resources</h4>
          <ul class="space-y-2">
            <li>
              <a
                href="#"
                class="text-muted-foreground hover:text-primary transition-colors text-sm"
              >
                Documentation
              </a>
            </li>
            <li>
              <a
                href="#"
                class="text-muted-foreground hover:text-primary transition-colors text-sm"
              >
                API Reference
              </a>
            </li>
            <li>
              <a
                href="#"
                class="text-muted-foreground hover:text-primary transition-colors text-sm"
              >
                Support
              </a>
            </li>
            <li>
              <a
                href="#"
                class="text-muted-foreground hover:text-primary transition-colors text-sm"
              >
                Privacy Policy
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Bottom Section -->
      <div class="border-t border-border pt-8 mt-8">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <p class="text-sm text-muted-foreground">
            © {{ currentYear }} HumAIne. All rights reserved.
          </p>
          <p class="text-sm text-muted-foreground mt-2 md:mt-0">
            Built with ❤️ using Active Learning
          </p>
        </div>
      </div>
    </div>
  </footer>
</template>
