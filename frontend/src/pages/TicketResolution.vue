<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Progress from '@/components/ui/Progress.vue'
import Accordion from '@/components/ui/Accordion.vue'
import ExportButton from '@/components/ExportButton.vue'
import { useInstances } from '@/composables/api/useActiveLearning'
import { useCategories, useSubcategories } from '@/composables/api/useData'
import { useProcessResolution, useResolutionFeedback } from '@/composables/api/useResolution'
import type { ResolutionProcessRequest, ResolutionProcessResponse, SimilarReply } from '@/types/api'
import {
  MessageSquare,
  Send,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  RefreshCw,
  FileText,
  Sparkles,
  Users,
  Target,
} from 'lucide-vue-next'

// Form state
const ticketTitle = ref('')
const ticketDescription = ref('')
const selectedCategory = ref('')
const selectedSubcategory = ref('')

// Result state
const result = ref<ResolutionProcessResponse | null>(null)
const editedResponse = ref('')
const feedbackSent = ref(false)
const copiedToClipboard = ref(false)

// Get instances to use for fetching categories
const { data: instancesData } = useInstances()

// Use first available instance for categories, fallback to 0
const dataInstanceId = computed(() => {
  const instances = instancesData.value?.instances
  if (instances) {
    const keys = Object.keys(instances)
    if (keys.length > 0) {
      return Number(keys[0])
    }
  }
  return 0
})

// Data composables - use first available instance for categories
const { data: categoriesData } = useCategories(dataInstanceId, undefined, {
  enabled: computed(() => dataInstanceId.value > 0),
})
const { data: subcategoriesData } = useSubcategories(dataInstanceId, undefined, {
  enabled: computed(() => dataInstanceId.value > 0),
})

// Extract arrays from response objects
const categories = computed(() => categoriesData.value?.categories ?? [])
const subcategories = computed(() => subcategoriesData.value?.subcategories ?? [])

// Filter subcategories based on selected category (client-side filtering)
const filteredSubcategories = computed(() => {
  if (!selectedCategory.value) return []
  // Return all subcategories - API may not provide category-specific filtering
  return subcategories.value
})

// Reset subcategory when category changes
watch(selectedCategory, () => {
  selectedSubcategory.value = ''
})

// Mutations
const processMutation = useProcessResolution({
  onSuccess: (data) => {
    result.value = data
    editedResponse.value = data.response
    feedbackSent.value = false
    toast.success('Resolution generated')
  },
})

const feedbackMutation = useResolutionFeedback({
  onSuccess: (data) => {
    feedbackSent.value = true
    toast.success('Feedback saved', {
      description: data.message,
    })
  },
})

// Computed
const hasInput = computed(() => !!(ticketTitle.value || ticketDescription.value))
const isProcessing = computed(() => processMutation.isPending.value)
const isSendingFeedback = computed(() => feedbackMutation.isPending.value)

const exportData = computed(() => {
  if (!result.value) return []
  return [
    {
      title: ticketTitle.value,
      description: ticketDescription.value,
      category: selectedCategory.value,
      subcategory: selectedSubcategory.value,
      classification: result.value.classification,
      predicted_team: result.value.predicted_team,
      team_confidence: result.value.team_confidence,
      response: editedResponse.value,
      similar_count: result.value.similar_replies.length,
    },
  ]
})

// Methods
const processTicket = async () => {
  if (!hasInput.value) {
    toast.error('Empty ticket', { description: 'Please enter title or description' })
    return
  }

  const request: ResolutionProcessRequest = {
    ticket_title: ticketTitle.value,
    ticket_description: ticketDescription.value,
  }

  if (selectedCategory.value) {
    request.service_category = selectedCategory.value
  }
  if (selectedSubcategory.value) {
    request.service_subcategory = selectedSubcategory.value
  }

  processMutation.mutate(request)
}

const sendFeedback = async () => {
  if (!result.value) return

  feedbackMutation.mutate({
    ticket_title: ticketTitle.value,
    ticket_description: ticketDescription.value,
    edited_response: editedResponse.value,
    predicted_team: result.value.predicted_team,
    predicted_classification: result.value.classification,
    service_name: selectedCategory.value || undefined,
    service_subcategory: selectedSubcategory.value || undefined,
  })
}

const copyResponse = async () => {
  try {
    await navigator.clipboard.writeText(editedResponse.value)
    copiedToClipboard.value = true
    setTimeout(() => (copiedToClipboard.value = false), 2000)
    toast.success('Copied to clipboard')
  } catch {
    toast.error('Failed to copy')
  }
}

const useReply = (reply: SimilarReply) => {
  if (reply.first_reply) {
    editedResponse.value = reply.first_reply
    toast.info('Reply applied', { description: 'You can edit it before saving' })
  }
}

const clearForm = () => {
  ticketTitle.value = ''
  ticketDescription.value = ''
  selectedCategory.value = ''
  selectedSubcategory.value = ''
  result.value = null
  editedResponse.value = ''
  feedbackSent.value = false
}
</script>

<template>
  <div class="resolution">
    <header class="resolution__header">
      <div class="resolution__header-content">
        <h1 class="resolution__title">Ticket Resolution</h1>
        <p class="resolution__subtitle">Get AI-powered resolution suggestions with similar past replies</p>
      </div>
    </header>

    <div class="resolution__content">
      <!-- Input Form -->
      <Card class="resolution__form">
        <template #title>
          <FileText :size="18" />
          Ticket Details
        </template>
        <template #description>Enter the ticket information to get resolution suggestions</template>

        <div class="form-grid">
          <div class="form-field form-field--full">
            <label class="form-label">Title</label>
            <Input
              v-model="ticketTitle"
              placeholder="Enter ticket title..."
              :disabled="isProcessing"
            />
          </div>

          <div class="form-field form-field--full">
            <label class="form-label">Description</label>
            <Textarea
              v-model="ticketDescription"
              placeholder="Enter ticket description..."
              :rows="4"
              :disabled="isProcessing"
            />
          </div>

          <div class="form-field">
            <label class="form-label">Category (optional)</label>
            <select
              v-model="selectedCategory"
              class="form-select"
              :disabled="isProcessing"
            >
              <option value="">Select category...</option>
              <option
                v-for="(cat, index) in categories"
                :key="index"
                :value="cat"
              >
                {{ cat }}
              </option>
            </select>
          </div>

          <div class="form-field">
            <label class="form-label">Subcategory (optional)</label>
            <select
              v-model="selectedSubcategory"
              class="form-select"
              :disabled="isProcessing || !selectedCategory"
            >
              <option value="">Select subcategory...</option>
              <option
                v-for="(sub, index) in filteredSubcategories"
                :key="index"
                :value="sub"
              >
                {{ sub }}
              </option>
            </select>
          </div>
        </div>

        <template #footer>
          <div class="form-actions">
            <Button variant="ghost" size="sm" @click="clearForm" :disabled="isProcessing">
              Clear
            </Button>
            <Button @click="processTicket" :loading="isProcessing" :disabled="!hasInput">
              <Sparkles :size="16" />
              Get Resolution
            </Button>
          </div>
        </template>
      </Card>

      <!-- Results Section -->
      <template v-if="result || isProcessing">
        <!-- Classification & Team -->
        <Card class="resolution__classification">
          <template #title>
            <Target :size="18" />
            Classification
          </template>

          <div v-if="isProcessing" class="loading-state">
            <Progress :value="undefined" />
            <span>Analyzing ticket...</span>
          </div>

          <template v-else-if="result">
            <div class="classification-grid">
              <div class="classification-item">
                <span class="classification-label">Classification</span>
                <Badge variant="default" size="lg">{{ result.classification }}</Badge>
              </div>
              <div class="classification-item">
                <span class="classification-label">Predicted Team</span>
                <Badge variant="secondary" size="lg">
                  <Users :size="14" />
                  {{ result.predicted_team }}
                </Badge>
              </div>
              <div class="classification-item">
                <span class="classification-label">Confidence</span>
                <div class="confidence-display">
                  <Progress :value="result.team_confidence * 100" :max="100" />
                  <span>{{ (result.team_confidence * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Generated Response -->
        <Card class="resolution__response">
          <template #title>
            <MessageSquare :size="18" />
            Suggested Response
          </template>
          <template #action>
            <div class="response-actions">
              <ExportButton :data="exportData" filename="resolution_result" :disabled="!result" />
            </div>
          </template>

          <div v-if="isProcessing" class="loading-state">
            <Progress :value="undefined" />
            <span>Generating response...</span>
          </div>

          <template v-else-if="result">
            <Textarea
              v-model="editedResponse"
              :rows="6"
              placeholder="Edit the response here..."
              class="response-textarea"
            />

            <div class="response-toolbar">
              <Button variant="outline" size="sm" @click="copyResponse">
                <Check v-if="copiedToClipboard" :size="14" />
                <Copy v-else :size="14" />
                {{ copiedToClipboard ? 'Copied!' : 'Copy' }}
              </Button>
              <Button variant="outline" size="sm" @click="editedResponse = result.response">
                <RefreshCw :size="14" />
                Reset
              </Button>
              <div class="response-toolbar__spacer" />
              <Button
                variant="default"
                size="sm"
                @click="sendFeedback"
                :loading="isSendingFeedback"
                :disabled="feedbackSent"
              >
                <ThumbsUp :size="14" />
                {{ feedbackSent ? 'Saved!' : 'Save to KB' }}
              </Button>
            </div>
          </template>
        </Card>

        <!-- Similar Replies -->
        <Card v-if="result && result.similar_replies.length > 0" class="resolution__similar">
          <template #title>
            <FileText :size="18" />
            Similar Past Replies ({{ result.similar_replies.length }})
          </template>
          <template #description>Click on a reply to use it as your response</template>

          <div class="similar-replies">
            <div
              v-for="(reply, index) in result.similar_replies"
              :key="index"
              class="similar-reply"
              @click="useReply(reply)"
            >
              <div class="similar-reply__header">
                <Badge variant="outline">
                  {{ reply['Service->Name'] || 'Unknown Service' }}
                </Badge>
                <Badge v-if="reply.enhanced_score" variant="secondary">
                  {{ (reply.enhanced_score * 100).toFixed(0) }}% match
                </Badge>
                <Badge v-else-if="reply.similarity" variant="secondary">
                  {{ (reply.similarity * 100).toFixed(0) }}% similar
                </Badge>
              </div>

              <h4 class="similar-reply__title">
                {{ reply.Title_anon || 'No title' }}
              </h4>

              <p v-if="reply.Description_anon" class="similar-reply__description">
                {{ reply.Description_anon }}
              </p>

              <div v-if="reply.first_reply" class="similar-reply__response">
                <span class="similar-reply__response-label">Past Reply:</span>
                <p>{{ reply.first_reply }}</p>
              </div>

              <Button variant="ghost" size="sm" class="similar-reply__use-btn">
                <Copy :size="14" />
                Use this reply
              </Button>
            </div>
          </div>
        </Card>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
.resolution {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;

  &__header {
    margin-bottom: 2rem;
  }

  &__header-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__title {
    font-size: 1.875rem;
    font-weight: 700;
    margin: 0;
  }

  &__subtitle {
    color: var(--muted-foreground);
    margin: 0;
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  &__form,
  &__classification,
  &__response,
  &__similar {
    :deep(.card__title) {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
  }
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;

  &--full {
    grid-column: 1 / -1;
  }
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
}

.form-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--background);
  font-size: 0.875rem;
  color: inherit;

  &:focus {
    outline: none;
    border-color: var(--ring);
    box-shadow: 0 0 0 2px var(--ring);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.classification-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.classification-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.classification-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted-foreground);
}

.confidence-display {
  display: flex;
  align-items: center;
  gap: 0.75rem;

  span {
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
  }
}

.response-actions {
  display: flex;
  gap: 0.5rem;
}

.response-textarea {
  margin-top: 1rem;
}

.response-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;

  &__spacer {
    flex: 1;
  }
}

.similar-replies {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.similar-reply {
  padding: 1rem;
  background: var(--muted);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.15s ease, transform 0.1s ease;

  &:hover {
    background: var(--accent);

    .similar-reply__use-btn {
      opacity: 1;
    }
  }

  &:active {
    transform: scale(0.99);
  }

  &__header {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
  }

  &__title {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 500;
  }

  &__description {
    margin: 0.5rem 0 0;
    font-size: 0.875rem;
    color: var(--muted-foreground);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__response {
    margin-top: 0.75rem;
    padding: 0.75rem;
    background: var(--background);
    border-radius: calc(var(--radius) - 2px);
    font-size: 0.875rem;

    p {
      margin: 0.25rem 0 0;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }

  &__response-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &__use-btn {
    margin-top: 0.75rem;
    opacity: 0;
    transition: opacity 0.15s ease;
  }
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .classification-grid {
    grid-template-columns: 1fr;
  }
}
</style>