<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { MessageSquare, Send, Check, Edit3, ChevronDown, ChevronUp } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { apiService } from '@/services/api'
import { toast } from 'vue-sonner'
import type { SimilarReply } from '@/types/api'

interface ResolutionPrediction {
  classification: string
  team: string
  teamConfidence: number
  response: string
  similar_tickets: SimilarReply[]
}

const isLoading = ref(false)
const prediction = ref<ResolutionPrediction | null>(null)
const isEditingResponse = ref(false)
const editedResponse = ref('')
const expandedTickets = ref<Set<number>>(new Set())
const formData = ref({
  service: '',
  subcategory: '',
  title: '',
  description: ''
})

// Available categories and subcategories from API
const availableCategories = ref<string[]>([])
const availableSubcategories = ref<string[]>([])

// Fetch categories and subcategories on mount
onMounted(async () => {
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

const handleSubmit = async () => {
  isLoading.value = true
  prediction.value = null
  isEditingResponse.value = false
  
  try {
    // Call the resolution API
    const response = await apiService.processResolution({
      ticket_title: formData.value.title,
      ticket_description: formData.value.description,
      service_category: formData.value.service,
      service_subcategory: formData.value.subcategory,
    })

    if (!response.success || !response.data) {
      throw new Error(response.error?.detail || 'Failed to generate resolution')
    }

    const data = response.data

    // Map API response to local state
    const resolutionPrediction: ResolutionPrediction = {
      classification: data.classification,
      team: data.predicted_team,
      teamConfidence: data.team_confidence,
      response: data.response,
      similar_tickets: data.similar_replies,
    }

    prediction.value = resolutionPrediction
    editedResponse.value = resolutionPrediction.response

    toast.success('Resolution Generated', {
      description: `Ticket resolved and assigned to ${resolutionPrediction.team}`,
    })
  } catch (error) {
    toast.error('Error', {
      description: error instanceof Error ? error.message : 'Failed to generate resolution',
    })
  } finally {
    isLoading.value = false
  }
}

const handleConfirmResolution = async () => {
  if (!prediction.value) return

  try {
    isLoading.value = true

    // Call feedback endpoint with the edited (or original) response
    const response = await apiService.sendResolutionFeedback({
      ticket_title: formData.value.title,
      ticket_description: formData.value.description,
      edited_response: editedResponse.value,
      predicted_team: prediction.value.team,
      predicted_classification: prediction.value.classification,
      service_name: formData.value.service,
      service_subcategory: formData.value.subcategory,
    })

    if (!response.success || !response.data) {
      throw new Error(response.error?.detail || 'Failed to save feedback')
    }

    toast.success('Resolution Confirmed', {
      description: response.data.message || 'The resolution has been saved successfully.',
    })
    
    // Reset form and state
    formData.value = {
      service: '',
      subcategory: '',
      title: '',
      description: ''
    }
    prediction.value = null
    isEditingResponse.value = false
    editedResponse.value = ''
    expandedTickets.value = new Set()
  } catch (error) {
    toast.error('Error', {
      description: error instanceof Error ? error.message : 'Failed to save resolution',
    })
  } finally {
    isLoading.value = false
  }
}

const toggleTicketExpansion = (index: number) => {
  const newExpanded = new Set(expandedTickets.value)
  if (newExpanded.has(index)) {
    newExpanded.delete(index)
  } else {
    newExpanded.add(index)
  }
  expandedTickets.value = newExpanded
}

const useExample = (title: string, description: string) => {
  const firstCategory = availableCategories.value[0] || ''
  const firstSubcategory = availableSubcategories.value[0] || ''
  formData.value = {
    service: firstCategory,
    subcategory: firstSubcategory,
    title,
    description
  }
}
</script>

<template>
  <div class="min-h-screen py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-8 ml-fade-in">
        <h1 class="text-4xl font-bold mb-4">
          <span class="ml-hero-text">Ticket Resolution Interface</span>
        </h1>
        <p class="text-xl text-muted-foreground">
          Generate automated responses for IT support tickets using AI-powered resolution
        </p>
      </div>

      <!-- Input Form -->
      <Card class="ml-card mb-8 ml-fade-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <MessageSquare class="w-6 h-6 text-primary" />
            <span>Ticket Information</span>
          </CardTitle>
          <CardDescription>
            Enter ticket details to generate an automated resolution
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="handleSubmit" class="space-y-6">
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
                Generating Resolution...
              </template>
              <template v-else>
                <Send class="w-4 h-4 mr-2" />
                Generate Resolution
              </template>
            </Button>
          </form>
        </CardContent>
      </Card>

      <!-- Resolution Results -->
      <Card v-if="prediction" class="ml-card mb-8 ml-scale-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Check class="w-6 h-6 text-ml-success" />
            <span>Generated Resolution</span>
          </CardTitle>
          <CardDescription>
            AI-generated response based on similar historical tickets
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <!-- Team Assignment -->
          <div class="p-4 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-muted-foreground mb-1">Assigned Team</p>
                <h3 class="text-xl font-bold">{{ prediction.team }}</h3>
                <div class="mt-2">
                  <Badge 
                    variant="outline" 
                    :class="
                      prediction.teamConfidence >= 0.9 
                        ? 'bg-green-50 border-green-200 text-green-700' 
                        : prediction.teamConfidence >= 0.7 
                        ? 'bg-yellow-50 border-yellow-200 text-yellow-700' 
                        : 'bg-red-50 border-red-200 text-red-700'
                    "
                  >
                    {{ (prediction.teamConfidence * 100).toFixed(1) }}% confidence
                  </Badge>
                </div>
              </div>
              <Badge variant="secondary" class="text-sm">
                {{ prediction.classification }}
              </Badge>
            </div>
          </div>

          <!-- Generated Response -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <Label for="resolution-response">Suggested Response</Label>
              <Button
                v-if="!isEditingResponse"
                variant="outline"
                size="sm"
                @click="isEditingResponse = true"
              >
                <Edit3 class="w-4 h-4 mr-2" />
                Edit Response
              </Button>
            </div>
            <Textarea
              id="resolution-response"
              v-model="editedResponse"
              class="min-h-[250px]"
              :readonly="!isEditingResponse"
            />
            <p v-if="isEditingResponse" class="text-sm text-muted-foreground">
              Editing enabled. Modify the response as needed before confirming.
            </p>
          </div>

          <!-- Similar Tickets -->
          <div v-if="prediction.similar_tickets && prediction.similar_tickets.length > 0" class="space-y-3">
            <h4 class="font-semibold">Similar Historical Tickets</h4>
            <p class="text-sm text-muted-foreground mb-3">
              These tickets were used to generate the suggested response
            </p>
            
            <div class="space-y-3">
              <div 
                v-for="(ticket, index) in prediction.similar_tickets"
                :key="index"
                class="border rounded-lg overflow-hidden transition-all"
              >
                <!-- Ticket Header - Always Visible -->
                <div 
                  class="p-4 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                  @click="toggleTicketExpansion(index)"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3 flex-1">
                      <Badge variant="outline">{{ ticket.Ref || `Ticket ${index + 1}` }}</Badge>
                      <Badge 
                        variant="secondary"
                        :class="(ticket.enhanced_score || ticket.similarity || 0) > 0.85 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'"
                      >
                        {{ ((ticket.enhanced_score || ticket.similarity || 0) * 100).toFixed(1) }}% similar
                      </Badge>
                    </div>
                    <ChevronUp v-if="expandedTickets.has(index)" class="w-5 h-5 text-muted-foreground" />
                    <ChevronDown v-else class="w-5 h-5 text-muted-foreground" />
                  </div>
                </div>

                <!-- Ticket Details - Expandable -->
                <div v-if="expandedTickets.has(index)" class="p-4 border-t bg-background space-y-3 ml-scale-in">
                  <div class="flex items-center space-x-2 mb-3">
                    <Badge variant="secondary">{{ ticket['Service->Name'] || 'Unknown Service' }}</Badge>
                    <Badge variant="outline">{{ ticket['Service subcategory->Name'] || 'Unknown Subcategory' }}</Badge>
                  </div>
                  
                  <div>
                    <span class="text-xs font-medium text-muted-foreground">Title:</span>
                    <p class="text-sm mt-1">{{ ticket.Title_anon || 'No title available' }}</p>
                  </div>
                  
                  <div>
                    <span class="text-xs font-medium text-muted-foreground">Description:</span>
                    <Textarea
                      :model-value="ticket.Description_anon || 'No description available'"
                      readonly
                      class="mt-1 min-h-[80px] resize-none text-sm"
                    />
                  </div>
                  
                  <div>
                    <span class="text-xs font-medium text-muted-foreground">First Reply:</span>
                    <Textarea
                      :model-value="ticket.first_reply || 'No reply available'"
                      readonly
                      class="mt-1 min-h-[120px] resize-none text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Confirm Button -->
          <div class="pt-4">
            <Button 
              @click="handleConfirmResolution"
              class="ml-button-primary w-full"
            >
              <Check class="w-4 h-4 mr-2" />
              Confirm Resolution
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Example Tickets -->
      <Card class="ml-card ml-fade-in">
        <CardHeader>
          <CardTitle>Example Tickets</CardTitle>
          <CardDescription>Try these sample tickets to see the resolution system in action</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid md:grid-cols-2 gap-4">
            <div class="p-4 bg-muted/30 rounded-lg">
              <h4 class="font-semibold mb-2">Jira License Request</h4>
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
              <h4 class="font-semibold mb-2">VPN Access Issue</h4>
              <p class="text-sm text-muted-foreground mb-3">
                "I cannot connect to the corporate VPN from my home network. Getting connection timeout errors."
              </p>
              <Button 
                variant="outline" 
                size="sm"
                @click="useExample('VPN Connection Timeout', 'I cannot connect to the corporate VPN from my home network. Getting connection timeout errors.')"
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
