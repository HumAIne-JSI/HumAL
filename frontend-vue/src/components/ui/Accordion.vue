<script lang="ts">
import { defineComponent, h, computed, provide, inject, ref, type InjectionKey, type Ref } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

// Types
export type AccordionType = 'single' | 'multiple'

export interface AccordionProps {
  type?: AccordionType
  modelValue?: string | string[]
  collapsible?: boolean
  disabled?: boolean
}

export interface AccordionItemProps {
  value: string
  disabled?: boolean
}

// Injection keys
const AccordionContextKey: InjectionKey<{
  type: Ref<AccordionType>
  modelValue: Ref<string | string[]>
  collapsible: Ref<boolean>
  disabled: Ref<boolean>
  toggleItem: (value: string) => void
  isItemOpen: (value: string) => boolean
}> = Symbol('AccordionContext')

const AccordionItemContextKey: InjectionKey<{
  value: Ref<string>
  disabled: Ref<boolean>
  isOpen: Ref<boolean>
  toggle: () => void
}> = Symbol('AccordionItemContext')

// Accordion Root Component
const Accordion = defineComponent({
  name: 'Accordion',
  props: {
    type: {
      type: String as () => AccordionType,
      default: 'single'
    },
    modelValue: {
      type: [String, Array] as unknown as () => string | string[],
      default: ''
    },
    collapsible: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { slots, emit }) {
    // Internal state for uncontrolled mode
    const internalValue = ref<string | string[]>(props.type === 'multiple' ? [] : '')

    // Computed value that uses modelValue if provided, otherwise internal state
    const currentValue = computed(() => {
      if (props.modelValue !== undefined && props.modelValue !== '') {
        return props.modelValue
      }
      return internalValue.value
    })

    // Methods
    const toggleItem = (value: string) => {
      if (props.disabled) return

      if (props.type === 'multiple') {
        const current = Array.isArray(currentValue.value) ? currentValue.value : []
        const newValue = current.includes(value)
          ? current.filter(v => v !== value)
          : [...current, value]
        internalValue.value = newValue
        emit('update:modelValue', newValue)
      } else {
        const newValue = currentValue.value === value
          ? (props.collapsible ? '' : value)
          : value
        internalValue.value = newValue
        emit('update:modelValue', newValue)
      }
    }

    const isItemOpen = (value: string): boolean => {
      if (props.type === 'multiple') {
        return Array.isArray(currentValue.value) && currentValue.value.includes(value)
      }
      return currentValue.value === value
    }

    // Provide context
    provide(AccordionContextKey, {
      type: computed(() => props.type),
      modelValue: currentValue,
      collapsible: computed(() => props.collapsible),
      disabled: computed(() => props.disabled),
      toggleItem,
      isItemOpen
    })

    return () => h('div', {
      class: 'accordion',
      'data-slot': 'accordion'
    }, slots.default?.())
  }
})

// AccordionItem Component
const AccordionItem = defineComponent({
  name: 'AccordionItem',
  props: {
    value: {
      type: String,
      required: true
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { slots }) {
    const accordionContext = inject(AccordionContextKey)
    
    if (!accordionContext) {
      console.warn('AccordionItem must be used within an Accordion')
      return () => null
    }

    const isOpen = computed(() => accordionContext.isItemOpen(props.value))
    const isDisabled = computed(() => props.disabled || accordionContext.disabled.value)

    const toggle = () => {
      if (!isDisabled.value) {
        accordionContext.toggleItem(props.value)
      }
    }

    provide(AccordionItemContextKey, {
      value: computed(() => props.value),
      disabled: isDisabled,
      isOpen,
      toggle
    })

    return () => h('div', {
      class: ['accordion-item', { 'accordion-item--disabled': isDisabled.value }],
      'data-slot': 'accordion-item',
      'data-state': isOpen.value ? 'open' : 'closed'
    }, slots.default?.())
  }
})

// AccordionTrigger Component
const AccordionTrigger = defineComponent({
  name: 'AccordionTrigger',
  setup(_, { slots }) {
    const itemContext = inject(AccordionItemContextKey)

    if (!itemContext) {
      console.warn('AccordionTrigger must be used within an AccordionItem')
      return () => null
    }

    const handleClick = () => {
      itemContext.toggle()
    }

    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        itemContext.toggle()
      }
    }

    return () => h('div', { class: 'accordion-header' }, [
      h('button', {
        type: 'button',
        class: ['accordion-trigger', { 'accordion-trigger--disabled': itemContext.disabled.value }],
        'data-slot': 'accordion-trigger',
        'data-state': itemContext.isOpen.value ? 'open' : 'closed',
        'aria-expanded': itemContext.isOpen.value,
        disabled: itemContext.disabled.value,
        onClick: handleClick,
        onKeydown: handleKeydown
      }, [
        h('span', { class: 'accordion-trigger__content' }, slots.default?.()),
        h(ChevronDown, {
          class: 'accordion-trigger__icon',
          size: 16
        })
      ])
    ])
  }
})

// AccordionContent Component
const AccordionContent = defineComponent({
  name: 'AccordionContent',
  setup(_, { slots }) {
    const itemContext = inject(AccordionItemContextKey)

    if (!itemContext) {
      console.warn('AccordionContent must be used within an AccordionItem')
      return () => null
    }

    return () => h('div', {
      class: 'accordion-content',
      'data-slot': 'accordion-content',
      'data-state': itemContext.isOpen.value ? 'open' : 'closed',
      'aria-hidden': !itemContext.isOpen.value,
      hidden: !itemContext.isOpen.value ? true : undefined
    }, [
      h('div', { class: 'accordion-content__inner' }, slots.default?.())
    ])
  }
})

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }
export default Accordion
</script>

<style>
/* Accordion Root */
.accordion {
  width: 100%;
}

/* Accordion Item */
.accordion-item {
  border-bottom: 1px solid var(--border);
}

.accordion-item:last-child {
  border-bottom: none;
}

.accordion-item--disabled {
  pointer-events: none;
  opacity: 0.5;
}

/* Accordion Header */
.accordion-header {
  display: flex;
}

/* Accordion Trigger */
.accordion-trigger {
  display: flex;
  flex: 1;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 0;
  text-align: left;
  font-size: 0.875rem;
  font-weight: var(--font-weight-medium);
  background: none;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  outline: none;
  transition: all 0.15s ease;
  width: 100%;
}

.accordion-trigger:hover {
  text-decoration: underline;
}

.accordion-trigger:focus-visible {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring), 0.5);
}

.accordion-trigger--disabled {
  pointer-events: none;
  opacity: 0.5;
  cursor: not-allowed;
}

.accordion-trigger__content {
  flex: 1;
  text-align: left;
}

.accordion-trigger__icon {
  color: var(--muted-foreground);
  flex-shrink: 0;
  transform: translateY(2px);
  transition: transform 0.2s ease;
  pointer-events: none;
}

.accordion-trigger[data-state="open"] .accordion-trigger__icon {
  transform: translateY(2px) rotate(180deg);
}

/* Accordion Content */
.accordion-content {
  overflow: hidden;
  font-size: 0.875rem;
  transition: max-height 0.2s ease-out, opacity 0.2s ease-out;
}

.accordion-content[data-state="closed"] {
  max-height: 0;
  opacity: 0;
}

.accordion-content[data-state="open"] {
  max-height: none;
  opacity: 1;
}

.accordion-content[hidden] {
  display: none;
}

.accordion-content__inner {
  padding-top: 0;
  padding-bottom: 1rem;
}
</style>
