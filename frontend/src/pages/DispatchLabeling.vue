<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Users, Check, X, ArrowRight, Search, Target, CheckCircle, XCircle } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { apiService } from '@/services/api'
import { toast } from 'vue-sonner'

interface Ticket {
  id: string
  title: string
  description: string
  service: string
  subcategory: string
}

interface Prediction {
  team: { name: string; id: string }
  model: any
  reasoning: string
}

interface Confirmation {
  type: string
  message: string
  team: string
  originalTeam?: string
  action: string
}

interface NearestTicketData {
  ref: string
  label: string
  similarity: number
  title?: string
  description?: string
  service?: string
  subcategory?: string
}

const currentTicket = ref<Ticket | null>(null)
const selectedModel = ref('')
const prediction = ref<Prediction | null>(null)
const explanation = ref<[string, number][] | null>(null)
const nearestTicket = ref<NearestTicketData | null>(null)
const isLoading = ref(false)
const confirmation = ref<Confirmation | null>(null)

// Track the current prediction ID to prevent stale LIME explanations
let currentPredictionId = 0

// Available models from API
const availableModels = ref<any[]>([])

// Available teams from API
const availableTeams = ref<string[]>([])
const selectedTeam = ref('')

// Track if model needs manual assignment (when inference fails with "not trained yet")
const needsManualAssignment = ref(false)

// Track selected team for reassignment
const selectedReassignTeam = ref('')

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
  }

  // Fetch teams
  try {
    const trainDataPath = 'data/al_demo_train_data.csv'
    const teamsResponse = await apiService.getTeams(0, trainDataPath)
    if (teamsResponse.success && teamsResponse.data) {
      availableTeams.value = teamsResponse.data.teams
    }
  } catch (error) {
    console.error('Failed to load teams:', error)
  }
})

const handleGetNextTicket = async () => {
  if (!selectedModel.value) {
    toast.error('No Model Selected', {
      description: 'Please select an active learning model first',
    })
    return
  }
  
  isLoading.value = true
  try {
    // Call /activelearning/<id>/next endpoint with batch size 1
    const nextResponse = await apiService.getNextInstances(parseInt(selectedModel.value), 1)
    
    if (!nextResponse.success || !nextResponse.data) {
      throw new Error(nextResponse.error?.detail || 'Failed to get next ticket')
    }
    
    const queryIdx = nextResponse.data.query_idx
    if (!queryIdx || queryIdx.length === 0) {
      toast.error('No More Tickets', {
        description: 'No more tickets available for labeling',
      })
      return
    }
    
    // Call /data/tickets endpoint with the returned index
    const ticketsResponse = await apiService.getTickets(parseInt(selectedModel.value), [queryIdx[0].toString()])
    
    if (!ticketsResponse.success || !ticketsResponse.data || ticketsResponse.data.tickets.length === 0) {
      throw new Error('Failed to retrieve ticket data')
    }
    
    const ticketData = ticketsResponse.data.tickets[0]
    
    // Transform ticket data to match expected format
    const ticket: Ticket = {
      id: ticketData.Ref,
      title: ticketData.Title_anon || 'No title available',
      description: ticketData.Description_anon || 'No description available',
      service: ticketData['Service->Name'] || 'Unknown Service',
      subcategory: ticketData['Service subcategory->Name'] || 'Unknown Subcategory'
    }
    
    currentTicket.value = ticket
    prediction.value = null
    confirmation.value = null
    selectedReassignTeam.value = ''
    explanation.value = null
    nearestTicket.value = null
    
    // Auto-generate team recommendation for the new ticket
    handleGetRecommendation(ticket)
    
    toast.success('New Ticket Retrieved', {
      description: `Model provided ticket ${ticket.id} for labeling`,
    })
  } catch (error) {
    toast.error('Error', {
      description: error instanceof Error ? error.message : 'Failed to get ticket from model',
    })
  } finally {
    isLoading.value = false
  }
}

const handleGetRecommendation = async (ticketData: Ticket) => {
  if (!ticketData || !selectedModel.value) return
  
  // Increment prediction ID to invalidate any pending LIME requests
  currentPredictionId += 1
  const thisPredictionId = currentPredictionId
  
  isLoading.value = true
  prediction.value = null
  confirmation.value = null
  explanation.value = null
  nearestTicket.value = null
  
  try {
    // Prepare inference data from ticket
    const inferenceData = {
      service_subcategory_name: ticketData.subcategory,
      service_name: ticketData.service,
      title_anon: ticketData.title,
      description_anon: ticketData.description,
      team_name: undefined,
      last_team_id_name: undefined,
      public_log_anon: undefined
    }
    
    // Call /activelearning/<id>/infer endpoint
    const inferenceResponse = await apiService.infer(parseInt(selectedModel.value), inferenceData)
    
    if (!inferenceResponse.success || !inferenceResponse.data) {
      // Check if the error is because the model isn't trained yet
      if (inferenceResponse.error?.detail?.includes('not trained yet')) {
        // Set flag to show manual assignment interface
        needsManualAssignment.value = true
        return
      }
      throw new Error(inferenceResponse.error?.detail || 'Failed to get team recommendation')
    }
    
    const currentModel = availableModels.value.find(m => m.id === selectedModel.value)
    // Backend returns array of predictions; extract first element
    const predictedTeam = Array.isArray(inferenceResponse.data) ? inferenceResponse.data[0] : inferenceResponse.data.prediction
    
    // Ensure availableTeams is not empty
    if (!availableTeams.value || availableTeams.value.length === 0) {
      throw new Error('No teams available for matching prediction')
    }
    
    // Find the team that matches the prediction
    let recommendedTeam = availableTeams.value.find(t => 
      t && typeof t === 'string' && 
      predictedTeam && typeof predictedTeam === 'string' &&
      t.toLowerCase().includes(predictedTeam.toLowerCase())
    )
    
    // If no exact match, use the first team as fallback
    if (!recommendedTeam) {
      recommendedTeam = availableTeams.value[0]
    }
    
    // Ensure recommendedTeam is valid
    if (!recommendedTeam) {
      throw new Error('Could not determine recommended team')
    }
    
    prediction.value = {
      team: { name: recommendedTeam, id: recommendedTeam },
      model: currentModel,
      reasoning: `Model ${currentModel?.name} analyzed ticket content and predicted "${predictedTeam}". Based on ${currentModel?.accuracy}% accuracy from training data.`
    }
    
    // Fire-and-forget LIME explanation
    ;(async () => {
      try {
        const explainResponse = await apiService.explainLime(parseInt(selectedModel.value), {
          ticket_data: inferenceData,
          model_id: 0,
        })
        
        // Only update if this is still the current prediction
        if (thisPredictionId === currentPredictionId && explainResponse.success && explainResponse.data && explainResponse.data.length > 0) {
          const item = explainResponse.data[0]
          if (item && Array.isArray(item.top_words)) {
            explanation.value = item.top_words
          }
        }
      } catch (err) {
        console.error('Explain LIME failed', err)
      }
    })()
    
    // Fire-and-forget nearest ticket lookup
    ;(async () => {
      try {
        const nearestResponse = await apiService.findNearestTicket(parseInt(selectedModel.value), {
          query_idx: [ticketData.id],
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
              const nearestTicketResponse = await apiService.getTickets(parseInt(selectedModel.value), [ref.toString()])
              
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
    
    // Reset manual assignment flag since we got a successful prediction
    needsManualAssignment.value = false
    
  } catch (error: any) {
    // Only show error toast if it's not a "model not trained" error
    if (!error.message?.includes('not trained yet')) {
      toast.error('Error', {
        description: error instanceof Error ? error.message : 'Failed to get team recommendation',
      })
    }
  } finally {
    isLoading.value = false
  }
}

const updateModelAccuracy = async (modelId: string) => {
  try {
    const infoResponse = await apiService.getInstanceInfo(parseInt(modelId))
    
    if (infoResponse.success && infoResponse.data?.f1_scores) {
      const f1Scores = infoResponse.data.f1_scores
      if (f1Scores.length > 0) {
        const accuracy = Math.round(f1Scores[f1Scores.length - 1] * 100 * 10) / 10
        
        // Update the accuracy in availableModels
        availableModels.value = availableModels.value.map(model => 
          model.id === modelId 
            ? { ...model, accuracy }
            : model
        )
        
        return accuracy
      }
    }
  } catch (error) {
    console.error('Failed to fetch updated accuracy:', error)
  }
  return null
}

const handleManualTeamAssignment = async () => {
  if (!selectedTeam.value || !currentTicket.value || !selectedModel.value) {
    toast.error('Missing Information', {
      description: 'Please select a team before confirming',
    })
    return
  }

  isLoading.value = true
  try {
    // Call /activelearning/<id>/label endpoint
    const labelResponse = await apiService.labelInstance(parseInt(selectedModel.value), {
      query_idx: [currentTicket.value.id],
      labels: [selectedTeam.value]
    })

    if (!labelResponse.success) {
      throw new Error(labelResponse.error?.detail || 'Failed to label ticket')
    }

    // Show success confirmation
    const confirmationData: Confirmation = {
      type: 'manual',
      message: 'Team assigned successfully',
      team: selectedTeam.value,
      action: `The ticket has been assigned to ${selectedTeam.value}. This will help train the model for future predictions.`
    }

    confirmation.value = confirmationData
    
    toast.success('Success!', {
      description: `Ticket assigned to ${selectedTeam.value}`,
    })

    // Reset selection and manual assignment flag
    selectedTeam.value = ''
    needsManualAssignment.value = false
    
    // Fetch updated accuracy after labeling
    await updateModelAccuracy(selectedModel.value)
    
  } catch (error) {
    toast.error('Error', {
      description: error instanceof Error ? error.message : 'Failed to assign team',
    })
  } finally {
    isLoading.value = false
  }
}

const handleLabelAction = async (action: string, teamId?: string) => {
  if (!currentTicket.value || !selectedModel.value || !prediction.value) return
  
  isLoading.value = true
  let confirmationData: Confirmation
  let labelToSend = prediction.value.team.name // Default to predicted team
  
  try {
    if (action === 'correct') {
      confirmationData = {
        type: 'correct',
        message: 'Assignment confirmed as correct',
        team: prediction.value.team.name,
        action: "The model's recommendation has been validated and the ticket will be dispatched to the correct team."
      }
    } else if (action === 'reassign') {
      const newTeam = availableTeams.value.find(t => t === teamId)
      labelToSend = newTeam || prediction.value.team.name
      confirmationData = {
        type: 'reassign',
        message: 'Ticket reassigned successfully',
        team: newTeam || 'Unknown Team',
        originalTeam: prediction.value.team.name,
        action: `The ticket has been reassigned from ${prediction.value.team.name} to ${newTeam}. This feedback will help improve the model's future predictions.`
      }
    } else {
      throw new Error('Invalid action')
    }
    
    // Call /activelearning/<id>/label endpoint
    const labelResponse = await apiService.labelInstance(parseInt(selectedModel.value), {
      query_idx: [currentTicket.value.id],
      labels: [labelToSend]
    })

    if (!labelResponse.success) {
      throw new Error(labelResponse.error?.detail || 'Failed to label ticket')
    }
    
    confirmation.value = confirmationData
    
    toast.success(confirmationData.message, {
      description: confirmationData.action,
    })
    
    // Fetch updated accuracy after labeling
    await updateModelAccuracy(selectedModel.value)
    
  } catch (error) {
    toast.error('Error', {
      description: error instanceof Error ? error.message : 'Failed to process label action',
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen py-8">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-8 ml-fade-in">
        <h1 class="text-4xl font-bold mb-4">
          <span class="ml-hero-text">Dispatch Labeling Interface</span>
        </h1>
        <p class="text-xl text-muted-foreground">
          Review tickets and confirm team assignments for dispatch training
        </p>
      </div>

      <!-- Model Selection & Ticket Selection -->
      <Card class="ml-card mb-8 ml-fade-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Users class="w-6 h-6 text-primary" />
            <span>Model & Ticket Selection</span>
          </CardTitle>
          <CardDescription>
            Choose your active learning model and ticket for team assignment review
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <!-- Model Selection -->
          <div class="space-y-2">
            <Label for="model-select">Active Learning Model</Label>
            <Select v-model="selectedModel" :disabled="availableModels.length === 0">
              <SelectTrigger>
                <SelectValue :placeholder="availableModels.length === 0 ? 'No models available' : '-- Select a Model --'" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="model in availableModels" :key="model.id" :value="model.id">
                  <div class="flex items-center justify-between w-full min-w-0">
                    <div class="flex items-center space-x-2">
                      <span>{{ model.name }}</span>
                      <Badge 
                        :variant="model.status === 'active' ? 'default' : 'secondary'"
                        class="text-xs"
                      >
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

          <!-- Ticket Selection -->
          <div class="space-y-2">
            <Label for="ticket-retrieve">Current Ticket for Team Assignment</Label>
            <div v-if="!currentTicket" class="p-4 border-2 border-dashed border-muted-foreground/25 rounded-lg text-center">
              <p class="text-muted-foreground">No ticket assigned yet</p>
              <p class="text-sm text-muted-foreground">Click "Get Next Ticket" to retrieve a ticket from the model</p>
            </div>
            <div v-else class="mt-6 space-y-4 ml-scale-in">
              <!-- Ticket Details -->
              <div class="p-4 bg-muted/30 rounded-lg">
                <div class="flex items-start justify-between mb-3">
                  <h3 class="font-semibold">Model-Provided Ticket</h3>
                  <div class="flex space-x-2">
                    <Badge variant="secondary">{{ currentTicket.service }}</Badge>
                    <Badge variant="outline">{{ currentTicket.subcategory }}</Badge>
                  </div>
                </div>
                <div class="space-y-2">
                  <div>
                    <strong>Title:</strong> {{ currentTicket.title }}
                  </div>
                  <div>
                    <strong>Description:</strong>
                    <Textarea
                      :model-value="currentTicket.description"
                      readonly
                      class="mt-1 min-h-[120px] resize-none"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="pt-4 flex space-x-3">
            <Button 
              @click="handleGetNextTicket"
              :disabled="!selectedModel || isLoading"
              class="ml-button-primary"
            >
              <template v-if="isLoading">
                <div class="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                Getting ticket from {{ availableModels.find(m => m.id === selectedModel)?.name }}...
              </template>
              <template v-else>
                <Search class="w-4 h-4 mr-2" />
                Get Next Ticket
              </template>
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Confirmation Message -->
      <Card 
        v-if="confirmation" 
        :class="[
          'ml-card mb-8 ml-scale-in',
          confirmation.type === 'correct' ? 'border-ml-success' : 
          confirmation.type === 'reassign' ? 'border-ml-warning' : 
          confirmation.type === 'manual' ? 'border-ml-primary' : 'border-ml-error'
        ]"
      >
        <CardContent class="pt-6">
          <div class="text-center">
            <div :class="[
              'w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center',
              confirmation.type === 'correct' ? 'bg-ml-success/10' : 
              confirmation.type === 'reassign' ? 'bg-ml-warning/10' : 
              confirmation.type === 'manual' ? 'bg-ml-primary/10' : 'bg-ml-error/10'
            ]">
              <CheckCircle :class="[
                'w-8 h-8',
                confirmation.type === 'correct' ? 'text-ml-success' : 
                confirmation.type === 'reassign' ? 'text-ml-warning' : 
                confirmation.type === 'manual' ? 'text-ml-primary' : 'text-ml-error'
              ]" />
            </div>
            <h3 class="text-xl font-semibold mb-2">{{ confirmation.message }}</h3>
            <p v-if="confirmation.type === 'reassign'" class="text-lg mb-2">
              <span class="line-through text-muted-foreground">{{ confirmation.originalTeam }}</span> 
              <ArrowRight class="w-4 h-4 inline mx-2" />
              <span class="font-semibold text-ml-warning">{{ confirmation.team }}</span>
            </p>
            <p v-if="confirmation.type === 'correct' || confirmation.type === 'manual'" class="text-lg mb-2 font-semibold text-ml-success">{{ confirmation.team }}</p>
            <p class="text-muted-foreground">{{ confirmation.action }}</p>
          </div>
        </CardContent>
      </Card>

      <!-- Manual Labeling Interface - shown when model not trained yet -->
      <Card v-if="currentTicket && !prediction && !confirmation && needsManualAssignment" class="ml-card mb-8 ml-scale-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Target class="w-6 h-6 text-ml-warning" />
            <span>Manual Team Assignment</span>
          </CardTitle>
          <CardDescription>
            Model not trained yet. Please assign the team manually to start training.
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <div class="text-center p-6 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
            <h3 class="text-xl font-semibold mb-2">Assign Team</h3>
            <p class="text-muted-foreground mb-4">
              Select the appropriate team for this ticket to start training the model.
            </p>
            <div class="space-y-4">
              <Select v-model="selectedTeam">
                <SelectTrigger class="w-64 mx-auto">
                  <SelectValue placeholder="Select team..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="team in availableTeams" :key="team" :value="team">
                    {{ team }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <Button 
                @click="handleManualTeamAssignment"
                :disabled="!selectedTeam || isLoading"
                class="ml-button-primary"
              >
                <template v-if="isLoading">
                  <div class="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                  Assigning...
                </template>
                <template v-else>
                  <Check class="w-4 h-4 mr-2" />
                  Confirm Assignment
                </template>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Team Recommendation -->
      <Card v-if="prediction && !confirmation" class="ml-card mb-8 ml-scale-in">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <ArrowRight class="w-6 h-6 text-ml-success" />
            <span>Recommended Team Assignment</span>
          </CardTitle>
          <CardDescription>
            Model prediction for team dispatch
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <!-- Team Recommendation -->
          <div class="text-center p-6 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
            <div v-if="isLoading" class="space-y-3">
              <div class="ml-pulse w-8 h-8 mx-auto bg-primary rounded-full" />
              <p class="text-muted-foreground">Analyzing ticket content...</p>
            </div>
            <template v-else>
              <h3 class="text-2xl font-bold mb-2">{{ prediction.team.name }}</h3>
              <p class="text-muted-foreground mb-3">Recommended team assignment</p>
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
            <div v-if="explanation || nearestTicket" class="space-y-4">
              <div v-if="explanation" class="p-4 bg-muted/30 rounded-lg">
                <h4 class="font-semibold mb-2">LIME Explanation</h4>
                <p class="text-sm text-muted-foreground mb-2">{{ prediction.reasoning }}</p>
                <div class="flex flex-wrap gap-2">
                  <span 
                    v-for="([word, weight], idx) in explanation.slice(0, 10)"
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

            <!-- Action Buttons -->
            <div class="flex flex-wrap gap-3 justify-center pt-4">
              <div class="flex gap-2 items-center">
                <Select v-model="selectedReassignTeam">
                  <SelectTrigger class="w-48">
                    <SelectValue placeholder="Reassign to..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem 
                      v-for="team in availableTeams.filter(t => t !== prediction?.team.name)" 
                      :key="team" 
                      :value="team"
                    >
                      {{ team }}
                    </SelectItem>
                  </SelectContent>
                </Select>
                
                <Button 
                  v-if="selectedReassignTeam"
                  @click="selectedReassignTeam = ''"
                  variant="ghost"
                  size="icon"
                  title="Clear selection"
                >
                  <XCircle class="w-4 h-4" />
                </Button>
              </div>
              
              <Button 
                @click="selectedReassignTeam ? handleLabelAction('reassign', selectedReassignTeam) : handleLabelAction('correct')"
                :class="selectedReassignTeam ? 'bg-ml-warning hover:bg-ml-warning/90 text-white' : 'ml-button-primary'"
              >
                <template v-if="selectedReassignTeam">
                  <ArrowRight class="w-4 h-4 mr-2" />
                  Reassign to {{ selectedReassignTeam }}
                </template>
                <template v-else>
                  <Check class="w-4 h-4 mr-2" />
                  Correct Assignment
                </template>
              </Button>
            </div>
          </template>
        </CardContent>
      </Card>

      <!-- Teams Overview -->
      <Card class="ml-card ml-fade-in">
        <CardHeader>
          <CardTitle>Available Teams</CardTitle>
          <CardDescription>Overview of teams that can be assigned tickets</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid md:grid-cols-2 gap-4">
            <div v-for="team in availableTeams" :key="team" class="p-4 bg-muted/30 rounded-lg">
              <h4 class="font-semibold mb-1">{{ team }}</h4>
              <p class="text-sm text-muted-foreground">Available team for ticket assignment</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
