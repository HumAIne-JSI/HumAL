<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Brain, BookOpen, Zap, ArrowRight, Users } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const features = [
  {
    title: 'Model Training',
    description: 'Create and configure active learning models with various algorithms and querying strategies.',
    icon: Brain,
    path: '/training',
    color: 'from-blue-500 to-purple-600',
  },
  {
    title: 'Dispatch Labeling',
    description: 'Review and confirm team assignments for support tickets to train dispatch models.',
    icon: Users,
    path: '/dispatch-labeling',
    color: 'from-blue-500 to-cyan-600',
  },
  {
    title: 'Ticket Resolution',
    description: 'Generate and refine AI-powered resolutions for support tickets.',
    icon: BookOpen,
    path: '/ticket-resolution',
    color: 'from-purple-500 to-pink-600',
  },
  {
    title: 'Inference',
    description: 'Get automatic predictions for ticket classification using your trained models.',
    icon: Zap,
    path: '/inference',
    color: 'from-green-500 to-blue-600',
  },
]
</script>

<template>
  <div class="min-h-screen">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- Hero Section -->
      <div class="text-center mb-16 ml-fade-in">
        <h1 class="text-5xl font-bold mb-6">
          <span class="ml-hero-text">Smart Ticketing System</span>
        </h1>
        <p class="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
          Harness the power of active machine learning to automatically classify and route support tickets. 
          Build intelligent models that learn from your feedback and improve over time.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <Button as-child class="ml-button-primary text-lg px-8 py-3">
            <RouterLink to="/training">
              <Brain class="w-5 h-5 mr-2" />
              Start Training
              <ArrowRight class="w-5 h-5 ml-2" />
            </RouterLink>
          </Button>
          <Button as-child variant="outline" class="text-lg px-8 py-3">
            <RouterLink to="/inference">
              Try Inference
              <Zap class="w-5 h-5 ml-2" />
            </RouterLink>
          </Button>
        </div>
      </div>

      <!-- Features Grid -->
      <div class="grid md:grid-cols-3 gap-8 mb-12">
        <Card 
          v-for="(feature, index) in features"
          :key="feature.title"
          class="ml-card hover:scale-105 transition-all duration-300 ml-fade-in"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <CardHeader class="text-center">
            <div :class="['w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r flex items-center justify-center', feature.color]">
              <component :is="feature.icon" class="w-8 h-8 text-white" />
            </div>
            <CardTitle class="text-xl font-semibold">{{ feature.title }}</CardTitle>
            <CardDescription class="text-base">
              {{ feature.description }}
            </CardDescription>
          </CardHeader>
          <CardContent class="text-center">
            <Button as-child class="ml-button-primary w-full">
              <RouterLink :to="feature.path">
                Get Started
                <ArrowRight class="w-4 h-4 ml-2" />
              </RouterLink>
            </Button>
          </CardContent>
        </Card>
      </div>

      <!-- Stats Section -->
      <div class="bg-card/50 backdrop-blur-sm rounded-lg p-8 mb-12 ml-fade-in">
        <h2 class="text-3xl font-bold text-center mb-8">Why Active Learning?</h2>
        <div class="grid md:grid-cols-3 gap-8 text-center">
          <div>
            <div class="text-4xl font-bold ml-hero-text mb-2">85%</div>
            <p class="text-muted-foreground">Reduction in labeling effort</p>
          </div>
          <div>
            <div class="text-4xl font-bold ml-hero-text mb-2">3x</div>
            <p class="text-muted-foreground">Faster model convergence</p>
          </div>
          <div>
            <div class="text-4xl font-bold ml-hero-text mb-2">95%</div>
            <p class="text-muted-foreground">Classification accuracy</p>
          </div>
        </div>
      </div>

      <!-- How it Works -->
      <div class="text-center ml-fade-in">
        <h2 class="text-3xl font-bold mb-8">How It Works</h2>
        <div class="grid md:grid-cols-3 gap-8">
          <div class="space-y-4">
            <div class="w-12 h-12 mx-auto bg-primary rounded-full flex items-center justify-center text-white font-bold text-xl">
              1
            </div>
            <h3 class="text-xl font-semibold">Train Your Model</h3>
            <p class="text-muted-foreground">
              Configure active learning parameters and create your first model instance
            </p>
          </div>
          <div class="space-y-4">
            <div class="w-12 h-12 mx-auto bg-primary rounded-full flex items-center justify-center text-white font-bold text-xl">
              2
            </div>
            <h3 class="text-xl font-semibold">Label Smart Samples</h3>
            <p class="text-muted-foreground">
              The system intelligently selects the most informative tickets for you to label
            </p>
          </div>
          <div class="space-y-4">
            <div class="w-12 h-12 mx-auto bg-primary rounded-full flex items-center justify-center text-white font-bold text-xl">
              3
            </div>
            <h3 class="text-xl font-semibold">Get Predictions</h3>
            <p class="text-muted-foreground">
              Use your trained model to automatically classify new support tickets
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
