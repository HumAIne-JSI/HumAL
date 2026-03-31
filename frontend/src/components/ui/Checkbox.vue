<script setup lang="ts">
import { computed } from 'vue'
import { Check, Minus } from 'lucide-vue-next'

// Props
const props = withDefaults(defineProps<{
  modelValue?: boolean | 'indeterminate'
  disabled?: boolean
  id?: string
  name?: string
  value?: string
  required?: boolean
}>(), {
  modelValue: false,
  disabled: false,
  required: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean | 'indeterminate']
}>()

// Computed
const isChecked = computed(() => props.modelValue === true)
const isIndeterminate = computed(() => props.modelValue === 'indeterminate')

const dataState = computed(() => {
  if (isIndeterminate.value) return 'indeterminate'
  return isChecked.value ? 'checked' : 'unchecked'
})

// Methods
const toggle = () => {
  if (props.disabled) return
  
  if (isIndeterminate.value) {
    emit('update:modelValue', true)
  } else {
    emit('update:modelValue', !props.modelValue)
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault()
    toggle()
  }
}
</script>

<template>
  <button
    type="button"
    role="checkbox"
    :aria-checked="isIndeterminate ? 'mixed' : isChecked"
    :aria-disabled="disabled"
    :disabled="disabled"
    :id="id"
    :name="name"
    :value="value"
    :data-state="dataState"
    data-slot="checkbox"
    class="checkbox"
    :class="{
      'checkbox--checked': isChecked,
      'checkbox--indeterminate': isIndeterminate,
      'checkbox--disabled': disabled
    }"
    @click="toggle"
    @keydown="handleKeydown"
  >
    <span
      v-if="isChecked || isIndeterminate"
      data-slot="checkbox-indicator"
      class="checkbox__indicator"
    >
      <Minus v-if="isIndeterminate" :size="14" />
      <Check v-else :size="14" />
    </span>
  </button>
</template>

<style>
.checkbox {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  border-radius: 4px;
  border: 1px solid var(--border);
  background-color: var(--input-background);
  cursor: pointer;
  outline: none;
  transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.checkbox:focus-visible {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring), 0.5);
}

.checkbox:hover:not(:disabled) {
  border-color: var(--ring);
}

.checkbox--checked,
.checkbox--indeterminate {
  background-color: var(--primary);
  border-color: var(--primary);
  color: var(--primary-foreground);
}

.checkbox--checked:hover:not(:disabled),
.checkbox--indeterminate:hover:not(:disabled) {
  background-color: var(--primary);
  border-color: var(--primary);
}

.checkbox--disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.checkbox__indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  color: currentColor;
}

.checkbox__indicator svg {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
