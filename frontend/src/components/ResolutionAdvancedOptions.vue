<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { ChevronRight } from 'lucide-vue-next'
import Input from '@/components/ui/Input.vue'
import InstanceSelector from '@/components/InstanceSelector.vue'
import { useInstances } from '@/composables/api/useActiveLearning'
import { useCategories, useSubcategories } from '@/composables/api/useData'
import { DEFAULT_RESOLUTION_TOP_K } from '@/composables/api/useResolution'

defineProps<{
  disabled?: boolean
}>()

const instanceId = defineModel<number>('instanceId', { required: true })
const topK = defineModel<number>('topK', { required: true })
const category = defineModel<string>('category', { required: true })
const subcategory = defineModel<string>('subcategory', { required: true })

const open = ref(false)
const panelId = useId()
const modelLabelId = useId()
const topKId = useId()
const categoryId = useId()
const subcategoryId = useId()

const instanceModel = computed<string>({
  get: () => (instanceId.value > 0 ? String(instanceId.value) : ''),
  set: (value) => {
    instanceId.value = value ? Number(value) : 0
  }
})

// Category lists come from the selected model, or the first available one.
const { data: instancesData } = useInstances()
const firstInstanceId = computed(() => {
  const instances = instancesData.value?.instances
  const keys = instances ? Object.keys(instances) : []
  return keys.length ? Number(keys[0]) : 0
})
const catInstanceId = computed(() =>
  instanceId.value > 0 ? instanceId.value : firstInstanceId.value
)
const hasCatInstance = computed(() => catInstanceId.value > 0)
const { data: categoriesData } = useCategories(catInstanceId, undefined, {
  enabled: hasCatInstance
})
const { data: subcategoriesData } = useSubcategories(catInstanceId, undefined, undefined, {
  enabled: hasCatInstance
})
const categories = computed(() => categoriesData.value?.categories ?? [])
const subcategories = computed(() => subcategoriesData.value?.subcategories ?? [])

// Non-default choices stay visible while the panel is collapsed.
const summaryChips = computed(() => {
  const chips: string[] = []
  if (instanceId.value > 0) chips.push(`Model #${instanceId.value}`)
  if (topK.value !== DEFAULT_RESOLUTION_TOP_K) chips.push(`${topK.value} suggestions`)
  if (category.value) {
    chips.push(subcategory.value ? `${category.value} › ${subcategory.value}` : category.value)
  }
  return chips
})

function onCategoryChange(event: Event): void {
  category.value = (event.target as HTMLSelectElement).value
  subcategory.value = ''
}
</script>

<template>
  <div class="advanced" :class="{ 'advanced--open': open }">
    <button
      type="button"
      class="advanced__toggle"
      :aria-expanded="open"
      :aria-controls="panelId"
      @click="open = !open"
    >
      <ChevronRight class="advanced__chevron" :size="16" aria-hidden="true" />
      <span class="advanced__label">Advanced options</span>
      <span v-if="!open && summaryChips.length" class="advanced__chips">
        <span v-for="chip in summaryChips" :key="chip" class="advanced__chip">{{ chip }}</span>
      </span>
      <span v-else-if="!open" class="advanced__hint">Model, suggestions, service category</span>
    </button>

    <div :id="panelId" class="advanced__panel">
      <div class="advanced__inner">
        <div class="advanced__grid">
          <div class="field">
            <span :id="modelLabelId" class="field__label">AI model</span>
            <div role="group" :aria-labelledby="modelLabelId">
              <InstanceSelector
                v-model="instanceModel"
                placeholder="No team prediction"
                :disabled="disabled"
              />
            </div>
            <span class="field__hint">Predicts the team first to sharpen the suggestions.</span>
          </div>

          <div class="field">
            <label :for="topKId" class="field__label">Similar replies to retrieve</label>
            <Input
              :id="topKId"
              v-model.number="topK"
              type="number"
              min="1"
              max="20"
              :disabled="disabled"
            />
            <span class="field__hint">Between 1 and 20. Default {{ DEFAULT_RESOLUTION_TOP_K }}.</span>
          </div>

          <div class="field">
            <label :for="categoryId" class="field__label">Service category</label>
            <select
              :id="categoryId"
              :value="category"
              class="field__select"
              :disabled="disabled"
              @change="onCategoryChange"
            >
              <option value="">None</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>

          <div class="field">
            <label :for="subcategoryId" class="field__label">Service subcategory</label>
            <select
              :id="subcategoryId"
              v-model="subcategory"
              class="field__select"
              :disabled="disabled || !category"
            >
              <option value="">{{ category ? 'None' : 'Choose a category first' }}</option>
              <option v-for="sub in subcategories" :key="sub" :value="sub">{{ sub }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.advanced {
  border-top: 1px solid var(--border);
}

.advanced__toggle {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.875rem 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;

  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 2px;
    border-radius: calc(var(--radius) - 4px);
  }
}

.advanced__chevron {
  flex-shrink: 0;
  transition: transform 0.2s ease;

  .advanced--open & {
    transform: rotate(90deg);
  }
}

.advanced__label {
  font-size: 0.875rem;
  font-weight: 500;
}

.advanced__hint {
  font-size: 0.8125rem;
  color: var(--muted-foreground);
}

.advanced__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.advanced__chip {
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  background: var(--muted);
  font-size: 0.75rem;
}

// Height animation without measuring: collapse the row track, then hide content
// once closed so collapsed fields can't receive focus.
.advanced__panel {
  display: grid;
  grid-template-rows: 0fr;
  visibility: hidden;
  transition:
    grid-template-rows 0.2s ease,
    visibility 0s linear 0.2s;

  .advanced--open & {
    grid-template-rows: 1fr;
    visibility: visible;
    transition:
      grid-template-rows 0.2s ease,
      visibility 0s linear 0s;
  }
}

.advanced__inner {
  min-height: 0;
  overflow: hidden;
}

.advanced__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem 1.25rem;
  padding: 0.25rem 0.125rem 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;

  :deep(.instance-selector) {
    min-width: 0;
  }
}

.field__label {
  font-size: 0.8125rem;
  font-weight: 500;
}

.field__hint {
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

.field__select {
  width: 100%;
  height: 2.25rem;
  padding: 0 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--input-background);
  font-family: inherit;
  font-size: 0.875rem;
  color: inherit;

  &:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 1px;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

@media (max-width: 640px) {
  .advanced__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (prefers-reduced-motion: reduce) {
  .advanced__chevron,
  .advanced__panel,
  .advanced--open .advanced__panel {
    transition: none;
  }
}
</style>
