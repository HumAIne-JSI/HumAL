<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Brain, Settings, Sparkles } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { apiService } from '@/services/api'
import { toast } from 'vue-sonner'

const TASK_TYPE = 'dispatch'

const isAdvancedOpen = ref(false)
const isLoading = ref(false)
const instanceId = ref<number | null>(null)

// State for available models and strategies from API
const availableModels = ref<string[]>([])
const availableStrategies = ref<string[]>([])
const teams = ref<string[]>([])
const isLoadingConfig = ref(true)

const config = ref({
  model: '',
  strategy: ''
})

// Fetch available models, strategies, and teams on component mount
onMounted(async () => {
  isLoadingConfig.value = true
  try {
    const trainDataPath = 'data/al_demo_train_data.csv'
    const [modelsResponse, strategiesResponse, teamsResponse] = await Promise.all([
      apiService.getModels(),
      apiService.getQueryStrategies(),
      apiService.getTeams(0, trainDataPath)
    ])

    if (modelsResponse.success && modelsResponse.data) {
      availableModels.value = modelsResponse.data.models
      // Set first model as default
      if (modelsResponse.data.models.length > 0) {
        config.value.model = modelsResponse.data.models[0]
      }
    }

    if (strategiesResponse.success && strategiesResponse.data) {
      availableStrategies.value = strategiesResponse.data.strategies
      // Set first strategy as default
      if (strategiesResponse.data.strategies.length > 0) {
        config.value.strategy = strategiesResponse.data.strategies[0]
      }
    }

    if (teamsResponse.success && teamsResponse.data) {
      teams.value = teamsResponse.data.teams
    }
  } catch (error) {
    toast.error('Error', {
      description: 'Failed to load configuration options',
    })
  } finally {
    isLoadingConfig.value = false
  }
})

const handleCreateInstance = async () => {
  isLoading.value = true
  
  try {
    // Call the actual API endpoint
    const response = await apiService.createInstance({
      model_name: config.value.model,
      qs_strategy: config.value.strategy,
      class_list: teams.value, // Use teams from /data/teams endpoint
      train_data_path: 'data/al_demo_train_data.csv',
      test_data_path: 'data/al_demo_test_data.csv'
    })

    if (response.success && response.data) {
      instanceId.value = response.data.instance_id
      
      toast.success('Success!', {
        description: `Active learning instance created with ID: ${response.data.instance_id}`,
      })
    } else {
      throw new Error(response.error?.detail || 'Failed to create instance')
    }
  } catch (error) {
    toast.error('Error', {
      description: error instanceof Error ? error.message : 'Failed to create active learning instance',
    })
  } finally {
    isLoading.value = false
  }
}

// Helper function to format display names
const formatDisplayName = (name: string) => {
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<template>
  <div class="min-h-screen py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-8 ml-fade-in">
        <h1 class="text-4xl font-bold mb-4">
          <span class="ml-hero-text">Active Learning Model Training</span>
        </h1>
        <p class="text-xl text-muted-foreground">
          Create and configure your machine learning models for smart ticket classification
        </p>
      </div>

      <!-- Main Card -->
      <Card class="ml-card mb-8 ml-fade-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Brain class="w-6 h-6 text-primary" />
            <span>Create Active Learning Instance</span>
          </CardTitle>
          <CardDescription>
            Configure your model parameters to get started with active learning
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <!-- Advanced Settings -->
          <Collapsible v-model:open="isAdvancedOpen">
            <CollapsibleTrigger as-child>
              <Button variant="ghost" class="w-full justify-start">
                <Settings class="w-4 h-4 mr-2" />
                Advanced Settings
                <span class="ml-auto">{{ isAdvancedOpen ? '−' : '+' }}</span>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent class="space-y-4 mt-4 p-4 bg-muted/30 rounded-lg">
              <div class="grid md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="model">Model Algorithm</Label>
                  <Select 
                    v-model="config.model"
                    :disabled="isLoadingConfig"
                  >
                    <SelectTrigger>
                      <SelectValue :placeholder="isLoadingConfig ? 'Loading...' : 'Select model'" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="model in availableModels" :key="model" :value="model">
                        {{ formatDisplayName(model) }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div class="space-y-2">
                  <Label for="strategy">Querying Strategy</Label>
                  <Select 
                    v-model="config.strategy"
                    :disabled="isLoadingConfig"
                  >
                    <SelectTrigger>
                      <SelectValue :placeholder="isLoadingConfig ? 'Loading...' : 'Select strategy'" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="strategy in availableStrategies" :key="strategy" :value="strategy">
                        {{ formatDisplayName(strategy) }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div class="space-y-2">
                <h4 class="font-medium">Strategy Explanation</h4>
                <div class="text-sm text-muted-foreground space-y-1">
                  <p v-if="config.strategy === 'random sampling'">Randomly selects samples for labeling. Good baseline but not optimal for learning efficiency.</p>
                  <p v-if="config.strategy === 'uncertainty sampling entropy'">Selects samples with highest prediction entropy. Focuses on the most uncertain predictions.</p>
                  <p v-if="config.strategy === 'uncertainty sampling margin sampling'">Selects samples with smallest margin between top two predictions. Good for binary classification.</p>
                  <p v-if="config.strategy === 'uncertainty sampling least confidence'">Selects samples with lowest confidence in the top prediction. Conservative approach.</p>
                  <p v-if="config.strategy === 'CLUE'">Clustering-based Uncertainty sampling with Entropy for diverse instance selection.</p>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>

          <!-- Create Button -->
          <div class="pt-4">
            <Button 
              @click="handleCreateInstance"
              :disabled="isLoading || isLoadingConfig"
              class="ml-button-primary w-full md:w-auto"
            >
              <template v-if="isLoading">
                <div class="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                Creating Instance...
              </template>
              <template v-else>
                <Sparkles class="w-4 h-4 mr-2" />
                Create Active Learning Instance
              </template>
            </Button>
          </div>

          <!-- Success Message -->
          <div v-if="instanceId" class="mt-6 p-4 bg-ml-success/10 border border-ml-success/20 rounded-lg ml-scale-in">
            <div class="flex items-start space-x-3">
              <div class="w-8 h-8 bg-ml-success rounded-full flex items-center justify-center flex-shrink-0">
                <Brain class="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 class="font-semibold text-ml-success">Instance Created Successfully!</h4>
                <p class="text-sm text-muted-foreground mt-1">
                  Your active learning instance has been created with ID: <code class="px-2 py-1 bg-muted rounded text-xs">{{ instanceId }}</code>
                </p>
                <p class="text-sm text-muted-foreground mt-2">
                  You can now proceed to the labeling page to start training your model with sample tickets.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Configuration Summary -->
      <Card class="ml-card ml-fade-in">
        <CardHeader>
          <CardTitle>Current Configuration</CardTitle>
          <CardDescription>Review your model settings</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid md:grid-cols-3 gap-4">
            <div class="text-center p-4 bg-muted/30 rounded-lg">
              <div class="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Task</div>
              <div class="mt-1 text-lg font-bold capitalize">{{ TASK_TYPE }}</div>
            </div>
            <div class="text-center p-4 bg-muted/30 rounded-lg">
              <div class="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Model</div>
              <div class="mt-1 text-lg font-bold capitalize">{{ formatDisplayName(config.model) }}</div>
            </div>
            <div class="text-center p-4 bg-muted/30 rounded-lg">
              <div class="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Strategy</div>
              <div class="mt-1 text-sm font-bold capitalize">{{ formatDisplayName(config.strategy) }}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
