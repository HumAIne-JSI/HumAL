<script setup lang="ts">
import { computed, watch, toRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Select from '@/components/ui/Select.vue'
import { useInstances } from '@/composables/api/useActiveLearning'

export interface InstanceSelectorProps {
  modelValue?: number | string
  filterTrained?: boolean
  syncRoute?: boolean
  placeholder?: string
  disabled?: boolean
  size?: 'sm' | 'default'
}

const props = withDefaults(defineProps<InstanceSelectorProps>(), {
  modelValue: '',
  filterTrained: false,
  syncRoute: false,
  placeholder: 'Select instance...',
  disabled: false,
  size: 'default',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const route = useRoute()
const router = useRouter()

// Fetch instances
const { data: instancesData, isLoading } = useInstances()

// Filter and format options
const instanceOptions = computed(() => {
  const instances = instancesData.value?.instances ?? {}
  return Object.entries(instances)
    .map(([id, info]) => {
      const accuracy = info.test_accuracy ?? info.training_accuracy
      const accuracyStr = accuracy !== undefined ? ` - ${(accuracy * 100).toFixed(1)}%` : ''
      return {
        value: id,
        label: `#${id} - ${info.model_name ?? info.model ?? 'Unknown'} (${info.qs ?? 'N/A'})${accuracyStr}`,
        trained: accuracy !== undefined,
      }
    })
    .filter((opt) => {
      // If filterTrained is false, show all instances
      // If filterTrained is true, still show all but could be used for sorting/priority
      return true
    })
})

// Current value as string
const currentValue = computed(() => String(props.modelValue || ''))

// Handle value update
const handleUpdate = (value: string) => {
  emit('update:modelValue', value)

  // Sync to route if enabled
  if (props.syncRoute && value) {
    router.replace({
      query: {
        ...route.query,
        instance: value,
      },
    })
  }
}

// Initialize from route if syncRoute is enabled
watch(
  () => route.query.instance,
  (instanceParam) => {
    if (props.syncRoute && instanceParam && instanceParam !== currentValue.value) {
      emit('update:modelValue', String(instanceParam))
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="instance-selector">
    <Select
      :model-value="currentValue"
      :options="instanceOptions"
      :placeholder="isLoading ? 'Loading instances...' : placeholder"
      :disabled="disabled || isLoading"
      :size="size"
      @update:model-value="handleUpdate"
    />
  </div>
</template>

<style scoped lang="scss">
.instance-selector {
  min-width: 200px;
}
</style>
