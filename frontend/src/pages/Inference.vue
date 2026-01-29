<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Zap, Send, Brain } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { apiService } from '@/services/api'
import { toast } from 'vue-sonner'

interface NearestTicketData {
  ref: string
  label: string
  similarity: number
  title?: string
  description?: string
  service?: string
  subcategory?: string
}

const isLoading = ref(false)
const prediction = ref<any>(null)
const explanationTopWords = ref<[string, number][] | null>(null)
const nearestTicket = ref<NearestTicketData | null>(null)
const selectedModel = ref<string | undefined>(undefined)
const formData = ref({
  service: '',
  subcategory: '',
  title: '',
  description: ''
})

// Track the current prediction ID to prevent stale LIME explanations
let currentPredictionId = 0

// Available models from API
const availableModels = ref<any[]>([])

// Available categories and subcategories from API
const availableCategories = ref<string[]>([])
const availableSubcategories = ref<string[]>([])

// Fetch available models from API
onMounted(async () => {
  try {
    const instancesResponse = await apiService.getInstances()
    
    if (instancesResponse.success && instancesResponse.data) {
      const instances = instancesResponse.data.instances
      
      // Fetch info for each instance to get accuracy
      const modelPromises = Object.keys(instances).map(async (instanceId) => {
        const instance = instances[instanceId]
        
        // Fetch instance info to get f1_scores
        const infoResponse = await apiService.getInstanceInfo(parseInt(instanceId))
        
        let accuracy = null
        if (infoResponse.success && infoResponse.data?.f1_scores) {
          const f1Scores = infoResponse.data.f1_scores
          if (f1Scores.length > 0) {
            accuracy = Math.round(f1Scores[f1Scores.length - 1] * 100 * 10) / 10
          }
        }
        
        // Capitalize model name
        const capitalizedModelName = instance.model_name
          ?.split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ') || 'Unknown'
        
        return {
          id: instanceId,
          name: `${capitalizedModelName} v${instanceId}`,
          accuracy,
          status: 'active'
        }
      })
      
      const models = (await Promise.all(modelPromises)).filter(m => m !== null)
      models.sort((a, b) => parseInt(b.id) - parseInt(a.id)) // Sort newest first
      
      availableModels.value = models
      
      // Set default to first model
      if (models.length > 0 && !selectedModel.value) {
        selectedModel.value = models[0].id
      }
    }
  } catch (error) {
    console.error('Failed to load models:', error)
    toast.error('Error', {
      description: 'Failed to load available models',
    })
  }

  // Fetch categories
  try {
    const trainDataPath = 'data/al_demo_train_data.csv'
    const categoriesResponse = await apiService.getCategories(0, trainDataPath)
    if (categoriesResponse.success && categoriesResponse.data) {
      availableCategories.value = categoriesResponse.data.categories
    }
  } catch (error) {
    console.error('Failed to load categories:', error)
  }

  // Fetch subcategories
  try {
    const trainDataPath = 'data/al_demo_train_data.csv'
    const subcategoriesResponse = await apiService.getSubcategories(0, trainDataPath)
    if (subcategoriesResponse.success && subcategoriesResponse.data) {
      availableSubcategories.value = subcategoriesResponse.data.subcategories
    }
  } catch (error) {
    console.error('Failed to load subcategories:', error)
  }
})

// Auto-select first model when models are loaded
watch(availableModels, (models) => {
  if (models.length > 0 && !selectedModel.value) {
    selectedModel.value = models[0].id
    console.log('Auto-selected model:', models[0].id)
  }
})

const handleSubmit = async () => {
  if (!selectedModel.value) {
    toast.error('Error', {
      description: 'Please select a model before classifying the ticket',
    })
    return
  }
  
  // Increment prediction ID to invalidate any pending LIME requests
  currentPredictionId += 1
  const thisPredictionId = currentPredictionId
  
  isLoading.value = true
  explanationTopWords.value = null
  nearestTicket.value = null
  
  try {
    // Build inference payload
    const inferenceData = {
      service_subcategory_name: formData.value.subcategory,
      service_name: formData.value.service,
      title_anon: formData.value.title,
      description_anon: formData.value.description,
      team_name: undefined,
      last_team_id_name: undefined,
      public_log_anon: undefined
    }

    // Call real inference endpoint
    const inferRes = await apiService.infer(parseInt(selectedModel.value), inferenceData)
    if (!inferRes.success || !inferRes.data) {
      if (inferRes.error?.detail?.includes('not trained yet')) {
        toast.error('Model not trained', {
          description: 'Please train the model first.',
        })
        return
      }
      throw new Error(inferRes.error?.detail || 'Failed to get prediction from model')
    }

    const selectedModelInfo = availableModels.value.find(m => m.id === selectedModel.value)
    // Backend returns array of predictions; extract first element
    const predictedGroup = Array.isArray(inferRes.data) ? inferRes.data[0] : inferRes.data.prediction

    // Set immediate prediction (no confidence shown)
    prediction.value = {
      group: String(predictedGroup),
      explanation: `Prediction generated by ${selectedModelInfo?.name}.`,
      model: selectedModelInfo
    }

    toast.success('Prediction Complete', {
      description: `Ticket classified as: ${String(predictedGroup)}`,
    })

    // Fire-and-forget LIME explanation
    ;(async () => {
      try {
        const explainRes = await apiService.explainLime(parseInt(selectedModel.value!), {
          ticket_data: inferenceData,
          model_id: 0
        })
        
        // Only update if this is still the current prediction
        if (thisPredictionId === currentPredictionId && explainRes.success && explainRes.data && explainRes.data.length > 0) {
          const item = explainRes.data[0]
          if (item && Array.isArray(item.top_words)) {
            explanationTopWords.value = item.top_words
          }
        }
      } catch (err) {
        console.error('Explain LIME failed', err)
      }
    })()
    
    // Fire-and-forget nearest ticket lookup
    ;(async () => {
      try {
        const nearestResponse = await apiService.findNearestTicket(parseInt(selectedModel.value!), {
          ticket_data: inferenceData,
          model_id: 0,
        })
        
        // Only update if this is still the current prediction
        if (thisPredictionId === currentPredictionId && nearestResponse.success && nearestResponse.data) {
          const item = nearestResponse.data
          const ref = Array.isArray(item.nearest_ticket_ref) ? item.nearest_ticket_ref[0] : item.nearest_ticket_ref
          const label = Array.isArray(item.nearest_ticket_label) ? item.nearest_ticket_label[0] : item.nearest_ticket_label
          const similarity = Array.isArray(item.similarity_score) ? item.similarity_score[0] : item.similarity_score
          
          if (ref && label !== undefined && similarity !== undefined) {
            // Fetch the full ticket details for the nearest ticket
            try {
              const nearestTicketResponse = await apiService.getTickets(parseInt(selectedModel.value!), [ref.toString()])
              
              if (nearestTicketResponse.success && nearestTicketResponse.data && nearestTicketResponse.data.tickets.length > 0) {
                const nearestTicketData = nearestTicketResponse.data.tickets[0]
                
                nearestTicket.value = {
                  ref: ref,
                  label: label,
                  similarity: similarity,
                  title: nearestTicketData.Title_anon || 'No title available',
                  description: nearestTicketData.Description_anon || 'No description available',
                  service: nearestTicketData['Service->Name'] || 'Unknown Service',
                  subcategory: nearestTicketData['Service subcategory->Name'] || 'Unknown Subcategory'
                }
              } else {
                nearestTicket.value = { ref, label, similarity }
              }
            } catch (ticketErr) {
              console.error('Failed to fetch nearest ticket details', ticketErr)
              nearestTicket.value = { ref, label, similarity }
            }
          }
        }
      } catch (err) {
        console.error('Find nearest ticket failed', err)
      }
    })()
  } catch (error) {
    toast.error('Error', {
      description: 'Failed to get prediction from model',
    })
  } finally {
    isLoading.value = false
  }
}

const useExample = (title: string, description: string) => {
  const firstCategory = availableCategories.value[0] || ''
  const firstSubcategory = availableSubcategories.value[0] || ''
  formData.value = {
    ...formData.value,
    title,
    description,
    service: firstCategory,
    subcategory: firstSubcategory
  }
}
</script>

<template>
  <div class="min-h-screen py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-8 ml-fade-in">
        <h1 class="text-4xl font-bold mb-4">
          <span class="ml-hero-text">Ticket Inference Engine</span>
        </h1>
        <p class="text-xl text-muted-foreground">
          Get automatic predictions for ticket classification using your trained models
        </p>
      </div>

      <!-- Input Form -->
      <Card class="ml-card mb-8 ml-fade-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Zap class="w-6 h-6 text-primary" />
            <span>Ticket Classification</span>
          </CardTitle>
          <CardDescription>
            Enter ticket details to get an automatic classification prediction
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="handleSubmit" class="space-y-6">
            <!-- Model Selection -->
            <div class="space-y-2">
              <Label for="model">Select Inference Model</Label>
              <Select
                :key="availableModels.length > 0 ? `models-${availableModels[0].id}` : 'no-models'"
                v-model="selectedModel"
                :disabled="availableModels.length === 0"
              >
                <SelectTrigger>
                  <SelectValue
                    :placeholder="availableModels.length === 0 ? 'No models available' : '-- Select a Model --'"
                  />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="model in availableModels" :key="model.id" :value="model.id">
                    <div class="flex items-center justify-between w-full min-w-0">
                      <div class="flex items-center space-x-2">
                        <span>{{ model.name }}</span>
                        <Badge :variant="model.status === 'active' ? 'default' : 'secondary'" class="text-xs">
                          {{ model.status }}
                        </Badge>
                      </div>
                      <span v-if="model.accuracy !== null" class="text-sm text-muted-foreground ml-2">
                        {{ model.accuracy }}% acc
                      </span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>

              <p v-if="selectedModel" class="text-sm text-muted-foreground">
                Using: {{ availableModels.find(m => m.id === selectedModel)?.name }}
                <span v-if="availableModels.find(m => m.id === selectedModel)?.accuracy !== null" class="text-ml-success ml-2">
                  ({{ availableModels.find(m => m.id === selectedModel)?.accuracy }}% accuracy)
                </span>
              </p>
            </div>

            <!-- Service Selection -->
            <div class="grid md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="service">Service Category</Label>
                <Select 
                  v-model="formData.service"
                  @update:model-value="formData.subcategory = ''"
                  :disabled="availableCategories.length === 0"
                >
                  <SelectTrigger>
                    <SelectValue :placeholder="availableCategories.length === 0 ? 'No categories available' : 'Select a service'" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="category in availableCategories" :key="category" :value="category">
                      {{ category }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-2">
                <Label for="subcategory">Service Subcategory</Label>
                <Select 
                  v-model="formData.subcategory"
                  :disabled="!formData.service || availableSubcategories.length === 0"
                >
                  <SelectTrigger>
                    <SelectValue :placeholder="availableSubcategories.length === 0 ? 'No subcategories available' : 'Select a subcategory'" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="subcategory in availableSubcategories" :key="subcategory" :value="subcategory">
                      {{ subcategory }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <!-- Title and Description -->
            <div class="space-y-4">
              <div class="space-y-2">
                <Label for="title">Ticket Title</Label>
                <Input
                  id="title"
                  v-model="formData.title"
                  placeholder="Enter ticket title"
                  required
                />
              </div>

              <div class="space-y-2">
                <Label for="description">Ticket Description</Label>
                <Textarea
                  id="description"
                  v-model="formData.description"
                  placeholder="Enter detailed ticket description"
                  class="min-h-[120px]"
                  required
                />
              </div>
            </div>

            <!-- Submit Button -->
            <Button 
              type="submit"
              :disabled="isLoading"
              class="ml-button-primary w-full md:w-auto"
            >
              <template v-if="isLoading">
                <div class="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                Classifying Ticket...
              </template>
              <template v-else>
                <Send class="w-4 h-4 mr-2" />
                Classify Ticket
              </template>
            </Button>
          </form>
        </CardContent>
      </Card>

      <!-- Prediction Results -->
      <Card v-if="prediction" class="ml-card mb-8 ml-scale-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Brain class="w-6 h-6 text-ml-success" />
            <span>Classification Result</span>
          </CardTitle>
          <CardDescription>
            Model prediction for the submitted ticket
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <!-- Main Prediction -->
          <div class="text-center p-6 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
            <div v-if="isLoading" class="space-y-3">
              <div class="ml-pulse w-8 h-8 mx-auto bg-primary rounded-full" />
              <p class="text-muted-foreground">Analyzing ticket content...</p>
            </div>
            <template v-else>
              <h3 class="text-2xl font-bold mb-2">{{ prediction.group }}</h3>
              <p class="text-muted-foreground mb-3">Predicted classification</p>
            </template>
          </div>

          <template v-if="!isLoading">
            <!-- Model Info -->
            <div class="text-center text-sm text-muted-foreground mb-4">
              Prediction by: <span class="font-semibold">{{ prediction.model?.name }}</span>
              <Badge v-if="prediction.model?.accuracy !== null" variant="outline" class="ml-2">
                {{ prediction.model?.accuracy }}% accuracy
              </Badge>
            </div>

            <!-- Reasoning appears after explanation arrives -->
            <div v-if="explanationTopWords || nearestTicket" class="space-y-4">
              <div v-if="explanationTopWords" class="p-4 bg-muted/30 rounded-lg">
                <h4 class="font-semibold mb-2">LIME Explanation</h4>
                <p class="text-sm text-muted-foreground mb-2">{{ prediction.explanation }}</p>
                <div class="flex flex-wrap gap-2">
                  <span 
                    v-for="([word, weight], idx) in explanationTopWords.slice(0, 10)"
                    :key="`${word}-${idx}`" 
                    :class="[
                      'inline-flex items-center rounded border px-2 py-1 text-xs',
                      weight > 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                    ]"
                  >
                    <span class="mr-1">{{ word }}</span>
                    <Badge 
                      variant="secondary" 
                      :class="weight > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                    >
                      {{ weight.toFixed(3) }}
                    </Badge>
                  </span>
                </div>
              </div>
              
              <div v-if="nearestTicket" class="p-4 bg-muted/30 rounded-lg">
                <h4 class="font-semibold mb-2">Similar Ticket</h4>
                <p class="text-sm text-muted-foreground mb-3">
                  Found a previously labeled ticket that is {{ (nearestTicket.similarity * 100).toFixed(1) }}% similar to this one.
                </p>
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium">Ticket Reference:</span>
                    <Badge variant="outline">{{ nearestTicket.ref }}</Badge>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium">Assigned Team:</span>
                    <Badge variant="secondary">{{ nearestTicket.label }}</Badge>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium">Similarity Score:</span>
                    <Badge 
                      variant="outline"
                      :class="nearestTicket.similarity > 0.8 ? 'bg-green-50 border-green-200 text-green-700' : 'bg-blue-50 border-blue-200 text-blue-700'"
                    >
                      {{ (nearestTicket.similarity * 100).toFixed(1) }}%
                    </Badge>
                  </div>
                  <div v-if="nearestTicket.title" class="pt-2 border-t">
                    <div class="flex items-start space-x-2 mb-2">
                      <Badge variant="secondary">{{ nearestTicket.service }}</Badge>
                      <Badge variant="outline">{{ nearestTicket.subcategory }}</Badge>
                    </div>
                    <div class="space-y-2">
                      <div>
                        <span class="text-xs font-medium text-muted-foreground">Title:</span>
                        <p class="text-sm mt-1">{{ nearestTicket.title }}</p>
                      </div>
                      <div>
                        <span class="text-xs font-medium text-muted-foreground">Description:</span>
                        <Textarea
                          :model-value="nearestTicket.description"
                          readonly
                          class="mt-1 min-h-[80px] resize-none text-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </CardContent>
      </Card>

      <!-- Quick Examples -->
      <Card class="ml-card ml-fade-in">
        <CardHeader>
          <CardTitle>Example Tickets</CardTitle>
          <CardDescription>Try these sample tickets to see the model in action</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid md:grid-cols-2 gap-4">
            <div class="p-4 bg-muted/30 rounded-lg">
              <h4 class="font-semibold mb-2">IT Access Request</h4>
              <p class="text-sm text-muted-foreground mb-3">
                "I need a Jira license to access the project Agile Transformation and track my development tasks"
              </p>
              <Button 
                variant="outline" 
                size="sm"
                @click="useExample('Jira License Request', 'I need a Jira license to access the project Agile Transformation and track my development tasks')"
              >
                Use This Example
              </Button>
            </div>
            
            <div class="p-4 bg-muted/30 rounded-lg">
              <h4 class="font-semibold mb-2">Hardware Issue</h4>
              <p class="text-sm text-muted-foreground mb-3">
                "My laptop screen is flickering and sometimes goes black. It's affecting my productivity."
              </p>
              <Button 
                variant="outline" 
                size="sm"
                @click="useExample('Laptop Screen Issue', 'My laptop screen is flickering and sometimes goes black. It\'s affecting my productivity.')"
              >
                Use This Example
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
