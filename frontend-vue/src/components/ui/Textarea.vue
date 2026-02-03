<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue?: string
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  required?: boolean
  name?: string
  id?: string
  rows?: number
  cols?: number
  minlength?: number
  maxlength?: number
  wrap?: 'hard' | 'soft' | 'off'
  autocomplete?: string
  autofocus?: boolean
  ariaInvalid?: boolean | 'true' | 'false'
}>(), {
  modelValue: '',
  disabled: false,
  readonly: false,
  required: false,
  autofocus: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'focus': [event: FocusEvent]
  'blur': [event: FocusEvent]
  'input': [event: Event]
}>()

const handleInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
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
  <textarea
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :readonly="readonly"
    :required="required"
    :name="name"
    :id="id"
    :rows="rows"
    :cols="cols"
    :minlength="minlength"
    :maxlength="maxlength"
    :wrap="wrap"
    :autocomplete="autocomplete"
    :autofocus="autofocus"
    :aria-invalid="ariaInvalid"
    class="textarea"
    :class="{
      'textarea--disabled': disabled,
      'textarea--invalid': ariaInvalid === true || ariaInvalid === 'true'
    }"
    @input="handleInput"
    @focus="handleFocus"
    @blur="handleBlur"
  />
</template>

<style>
.textarea {
  display: flex;
  width: 100%;
  min-height: 4rem;
  resize: none;
  field-sizing: content;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background-color: var(--input-background);
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--foreground);
  outline: none;
  transition: color 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.textarea::placeholder {
  color: var(--muted-foreground);
}

/* Focus state */
.textarea:focus-visible {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring), 0.5);
}

/* Invalid state */
.textarea--invalid,
.textarea[aria-invalid="true"] {
  border-color: var(--destructive);
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.2);
}

.textarea--invalid:focus-visible,
.textarea[aria-invalid="true"]:focus-visible {
  border-color: var(--destructive);
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.3);
}

/* Disabled state */
.textarea--disabled,
.textarea:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* Dark mode adjustments */
.dark .textarea {
  background-color: rgba(var(--input), 0.3);
}

.dark .textarea--invalid,
.dark .textarea[aria-invalid="true"] {
  box-shadow: 0 0 0 3px rgba(var(--destructive), 0.4);
}
</style>
