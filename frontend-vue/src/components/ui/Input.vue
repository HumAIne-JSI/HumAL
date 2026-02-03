<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  modelValue?: string | number
  type?: string
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  required?: boolean
  name?: string
  id?: string
  autocomplete?: string
  autofocus?: boolean
  min?: string | number
  max?: string | number
  step?: string | number
  minlength?: number
  maxlength?: number
  pattern?: string
  ariaInvalid?: boolean | 'true' | 'false'
}>(), {
  modelValue: '',
  type: 'text',
  disabled: false,
  readonly: false,
  required: false,
  autofocus: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  'focus': [event: FocusEvent]
  'blur': [event: FocusEvent]
  'input': [event: Event]
}>()

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
  emit('input', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}
</script>

<template>
  <input
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :readonly="readonly"
    :required="required"
    :name="name"
    :id="id"
    :autocomplete="autocomplete"
    :autofocus="autofocus"
    :min="min"
    :max="max"
    :step="step"
    :minlength="minlength"
    :maxlength="maxlength"
    :pattern="pattern"
    :aria-invalid="ariaInvalid"
    class="input"
    :class="{
      'input--disabled': disabled,
      'input--invalid': ariaInvalid === true || ariaInvalid === 'true'
    }"
    @input="handleInput"
    @focus="handleFocus"
    @blur="handleBlur"
  />
</template>

<style>
.input {
  display: flex;
  height: 2.25rem;
  width: 100%;
  min-width: 0;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background-color: var(--input-background);
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
  color: var(--foreground);
  outline: none;
  transition: color 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.input::placeholder {
  color: var(--muted-foreground);
}

.input::selection {
  background-color: var(--primary);
  color: var(--primary-foreground);
}

/* File input styles */
.input::file-selector-button {
  display: inline-flex;
  height: 1.75rem;
  border: 0;
  background-color: transparent;
  font-size: 0.875rem;
  font-weight: var(--font-weight-medium);
  color: var(--foreground);
  cursor: pointer;
}

/* Focus state */
.input:focus-visible {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring), 0.5);
}

/* Invalid state */
.input--invalid,
.input[aria-invalid="true"] {
  border-color: var(--destructive);
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.2);
}

.input--invalid:focus-visible,
.input[aria-invalid="true"]:focus-visible {
  border-color: var(--destructive);
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.3);
}

/* Disabled state */
.input--disabled,
.input:disabled {
  pointer-events: none;
  cursor: not-allowed;
  opacity: 0.5;
}

/* Dark mode adjustments */
.dark .input {
  background-color: rgba(var(--input), 0.3);
}

.dark .input--invalid,
.dark .input[aria-invalid="true"] {
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.4);
}
</style>
