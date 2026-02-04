<script setup lang="ts">
import { computed } from 'vue'
import Input from '@/components/ui/Input.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Select from '@/components/ui/Select.vue'
import { useCategories, useSubcategories } from '@/composables/api/useData'
import type { InferenceData } from '@/types/api'

export interface TicketFormProps {
  modelValue: InferenceData
  showCategories?: boolean
  showAllFields?: boolean
  disabled?: boolean
  compact?: boolean
}

const props = withDefaults(defineProps<TicketFormProps>(), {
  showCategories: false,
  showAllFields: false,
  disabled: false,
  compact: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: InferenceData]
}>()

// Fetch categories and subcategories if showing category selects
const { data: categoriesData } = useCategories(0, undefined, {
  enabled: computed(() => props.showCategories),
})
const { data: subcategoriesData } = useSubcategories(0, undefined, {
  enabled: computed(() => props.showCategories),
})

const categoryOptions = computed(() =>
  (categoriesData.value?.categories ?? []).map((cat) => ({
    value: cat,
    label: cat,
  }))
)

const subcategoryOptions = computed(() =>
  (subcategoriesData.value?.subcategories ?? []).map((sub) => ({
    value: sub,
    label: sub,
  }))
)

const updateField = <K extends keyof InferenceData>(field: K, value: InferenceData[K]) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value,
  })
}
</script>

<template>
  <div :class="['ticket-form', { 'ticket-form--compact': compact }]">
    <div class="ticket-form__field">
      <label class="ticket-form__label">Title</label>
      <Input
        :model-value="modelValue.title_anon ?? ''"
        placeholder="Enter ticket title..."
        :disabled="disabled"
        @update:model-value="updateField('title_anon', $event as string)"
      />
    </div>

    <div class="ticket-form__field">
      <label class="ticket-form__label">Description</label>
      <Textarea
        :model-value="modelValue.description_anon ?? ''"
        placeholder="Enter ticket description..."
        :rows="compact ? 3 : 5"
        :disabled="disabled"
        @update:model-value="updateField('description_anon', $event)"
      />
    </div>

    <template v-if="showCategories">
      <div class="ticket-form__row">
        <div class="ticket-form__field">
          <label class="ticket-form__label">Service Category</label>
          <Select
            :model-value="modelValue.service_name ?? ''"
            :options="categoryOptions"
            placeholder="Select category..."
            :disabled="disabled"
            @update:model-value="updateField('service_name', $event)"
          />
        </div>

        <div class="ticket-form__field">
          <label class="ticket-form__label">Service Subcategory</label>
          <Select
            :model-value="modelValue.service_subcategory_name ?? ''"
            :options="subcategoryOptions"
            placeholder="Select subcategory..."
            :disabled="disabled"
            @update:model-value="updateField('service_subcategory_name', $event)"
          />
        </div>
      </div>
    </template>

    <template v-if="showAllFields">
      <div class="ticket-form__row">
        <div class="ticket-form__field">
          <label class="ticket-form__label">Team Name</label>
          <Input
            :model-value="modelValue.team_name ?? ''"
            placeholder="Team name..."
            :disabled="disabled"
            @update:model-value="updateField('team_name', $event as string)"
          />
        </div>

        <div class="ticket-form__field">
          <label class="ticket-form__label">Last Team ID</label>
          <Input
            :model-value="modelValue.last_team_id_name ?? ''"
            placeholder="Last team ID..."
            :disabled="disabled"
            @update:model-value="updateField('last_team_id_name', $event as string)"
          />
        </div>
      </div>

      <div class="ticket-form__field">
        <label class="ticket-form__label">Public Log</label>
        <Textarea
          :model-value="modelValue.public_log_anon ?? ''"
          placeholder="Public log content..."
          :rows="compact ? 2 : 3"
          :disabled="disabled"
          @update:model-value="updateField('public_log_anon', $event)"
        />
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.ticket-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;

  &--compact {
    gap: 0.75rem;
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  &__label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--foreground);
  }

  &__row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;

    @media (max-width: 640px) {
      grid-template-columns: 1fr;
    }
  }
}
</style>
