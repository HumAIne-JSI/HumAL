<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onUnmounted, Teleport, Transition, useId } from 'vue'
import { ChevronDown, ChevronUp, Check, Search, X } from 'lucide-vue-next'

// Types
export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectGroup {
  label: string
  options: SelectOption[]
}

export type SelectOptions = (SelectOption | SelectGroup)[]

// Props
const props = withDefaults(defineProps<{
  modelValue?: string
  options: SelectOptions
  placeholder?: string
  disabled?: boolean
  size?: 'sm' | 'default'
}>(), {
  modelValue: '',
  placeholder: 'Select an option...',
  disabled: false,
  size: 'default'
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

// State
const open = ref(false)
const triggerRef = ref<HTMLElement | null>(null)
const contentRef = ref<HTMLElement | null>(null)
const viewportRef = ref<HTMLElement | null>(null)
const showScrollUp = ref(false)
const showScrollDown = ref(false)
const contentPosition = ref({ top: 0, left: 0, width: 0 })

// Computed
const selectedOption = computed(() => {
  for (const item of props.options) {
    if (isGroup(item)) {
      const found = item.options.find(opt => opt.value === props.modelValue)
      if (found) return found
    } else if (item.value === props.modelValue) {
      return item
    }
  }
  return null
})

const displayValue = computed(() => selectedOption.value?.label ?? '')

// Filter: a visible search box at the top of the dropdown filters the list
// live (contains, case-insensitive). Typing on the closed trigger opens the
// dropdown and seeds the query.
const selectId = useId()
const filterQuery = ref('')
const filterInputRef = ref<HTMLInputElement | null>(null)
const activeIndex = ref<number | null>(null)

const flatOptions = computed<SelectOption[]>(() => {
  const flat: SelectOption[] = []
  for (const item of props.options) {
    if (isGroup(item)) {
      flat.push(...item.options)
    } else {
      flat.push(item)
    }
  }
  return flat
})

const filteredFlat = computed<SelectOption[]>(() => {
  const query = filterQuery.value.trim().toLowerCase()
  if (!query) return flatOptions.value
  return flatOptions.value.filter(
    (opt) => !opt.disabled && opt.label.toLowerCase().includes(query),
  )
})

const filteredIndexMap = computed(() => {
  const map = new Map<SelectOption, number>()
  filteredFlat.value.forEach((opt, i) => map.set(opt, i))
  return map
})

const activeOptionId = computed(() =>
  activeIndex.value != null ? `${selectId}-option-${activeIndex.value}` : undefined,
)

function isPrintableKey(event: KeyboardEvent): boolean {
  return (
    event.key.length === 1 &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.altKey &&
    event.key !== ' ' &&
    !event.isComposing
  )
}

function focusFilterInput() {
  nextTick(() => {
    const input = filterInputRef.value
    if (!input) return
    input.focus()
    input.setSelectionRange(input.value.length, input.value.length)
  })
}

function scrollActiveIntoView() {
  nextTick(() => {
    if (activeIndex.value == null) return
    const el = contentRef.value?.querySelector<HTMLElement>(
      `[data-index="${activeIndex.value}"]`,
    )
    el?.scrollIntoView({ block: 'nearest' })
  })
}

// Helpers
function isGroup(item: SelectOption | SelectGroup): item is SelectGroup {
  return 'options' in item
}

// Methods
const updateValue = (value: string) => {
  emit('update:modelValue', value)
  closeSelect()
}

const closeSelect = () => {
  open.value = false
  triggerRef.value?.focus()
}

const toggleOpen = () => {
  if (!props.disabled) {
    open.value = !open.value
  }
}

const updatePosition = () => {
  if (triggerRef.value) {
    const rect = triggerRef.value.getBoundingClientRect()
    contentPosition.value = {
      top: rect.bottom + 4,
      left: rect.left,
      width: rect.width
    }
  }
}

const checkScrollButtons = () => {
  if (viewportRef.value) {
    const { scrollTop, scrollHeight, clientHeight } = viewportRef.value
    showScrollUp.value = scrollTop > 0
    showScrollDown.value = scrollTop + clientHeight < scrollHeight
  }
}

const scrollUp = () => {
  viewportRef.value?.scrollBy({ top: -50, behavior: 'smooth' })
}

const scrollDown = () => {
  viewportRef.value?.scrollBy({ top: 50, behavior: 'smooth' })
}

const handleTriggerKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    if (open.value && event.key === 'Enter' && activeIndex.value != null) {
      const option = filteredFlat.value[activeIndex.value]
      if (option && !option.disabled) {
        updateValue(option.value)
        return
      }
    }
    toggleOpen()
  } else if (event.key === 'ArrowDown' && !open.value) {
    event.preventDefault()
    open.value = true
  } else if (isPrintableKey(event)) {
    if (!open.value) {
      // Type to open + seed: open the dropdown and start the filter query.
      event.preventDefault()
      open.value = true
      filterQuery.value = event.key
      focusFilterInput()
    } else {
      event.preventDefault()
      event.stopPropagation()
    }
  }
}

// Capture-phase handler: while the dropdown is open, swallow printable keys
// typed anywhere inside the content (except in the filter input itself) so
// they can't trigger page-level shortcuts like j/k navigation.
const handleContentKeydown = (event: KeyboardEvent) => {
  if (isPrintableKey(event) && document.activeElement !== filterInputRef.value) {
    event.preventDefault()
    event.stopPropagation()
  }
}

const handleItemKeydown = (event: KeyboardEvent, value: string, disabled?: boolean) => {
  if ((event.key === 'Enter' || event.key === ' ') && !disabled) {
    event.preventDefault()
    updateValue(value)
  }
}

const handleFilterKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    event.preventDefault()
    const index = activeIndex.value ?? 0
    const option = filteredFlat.value[index]
    if (option && !option.disabled) {
      updateValue(option.value)
      return
    }
    closeSelect()
  } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    const len = filteredFlat.value.length
    if (!len) return
    const current = activeIndex.value ?? (event.key === 'ArrowDown' ? -1 : 0)
    activeIndex.value =
      event.key === 'ArrowDown' ? (current + 1) % len : (current - 1 + len) % len
    scrollActiveIntoView()
  } else if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    if (filterQuery.value) {
      filterQuery.value = ''
    } else {
      closeSelect()
    }
  }
}

// Click outside handler
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node
  if (
    open.value &&
    triggerRef.value &&
    contentRef.value &&
    !triggerRef.value.contains(target) &&
    !contentRef.value.contains(target)
  ) {
    closeSelect()
  }
}

// Keyboard handler
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && open.value) {
    closeSelect()
  }
}

// Watchers
watch(open, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    updatePosition()
    checkScrollButtons()
    focusFilterInput()
  } else {
    filterQuery.value = ''
    activeIndex.value = null
  }
})

watch(filterQuery, () => {
  if (!open.value) return
  const list = filteredFlat.value
  if (!list.length) {
    activeIndex.value = null
    return
  }
  activeIndex.value = 0
  scrollActiveIntoView()
})

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', updatePosition)
  window.addEventListener('scroll', updatePosition, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', updatePosition)
  window.removeEventListener('scroll', updatePosition, true)
})

const contentStyle = computed(() => ({
  top: `${contentPosition.value.top}px`,
  left: `${contentPosition.value.left}px`,
  minWidth: `${contentPosition.value.width}px`
}))
</script>

<template>
  <div class="select">
    <!-- Trigger -->
    <button
      ref="triggerRef"
      type="button"
      role="combobox"
      :aria-expanded="open"
      aria-haspopup="listbox"
      :aria-activedescendant="activeOptionId"
      :disabled="disabled"
      :data-size="size"
      :data-state="open ? 'open' : 'closed'"
      class="select-trigger"
      :class="{ 'select-trigger--disabled': disabled, 'select-trigger--sm': size === 'sm' }"
      @click="toggleOpen"
      @keydown="handleTriggerKeydown"
    >
      <span class="select-trigger__value">
        <template v-if="displayValue">{{ displayValue }}</template>
        <span v-else class="select-trigger__placeholder">{{ placeholder }}</span>
      </span>
      <span class="select-trigger__icon">
        <ChevronDown :size="16" />
      </span>
    </button>

    <!-- Content -->
    <Teleport to="body">
      <Transition name="select-content">
        <div
          v-if="open"
          ref="contentRef"
          class="select-content"
          :style="contentStyle"
          :data-state="open ? 'open' : 'closed'"
          @keydown.capture="handleContentKeydown"
        >
          <!-- Filter -->
          <div class="select-search">
            <Search :size="14" class="select-search__icon" />
            <input
              ref="filterInputRef"
              v-model="filterQuery"
              type="search"
              class="select-search__input"
              placeholder="Search..."
              role="searchbox"
              aria-label="Search options"
              @keydown="handleFilterKeydown"
            />
            <button
              v-if="filterQuery"
              type="button"
              class="select-search__clear"
              aria-label="Clear search"
              @click="filterQuery = ''"
            >
              <X :size="12" />
            </button>
          </div>

          <!-- Scroll Up Button -->
          <button
            v-if="showScrollUp"
            type="button"
            class="select-scroll-button"
            @click="scrollUp"
          >
            <ChevronUp :size="16" />
          </button>

          <!-- Viewport -->
          <div ref="viewportRef" class="select-viewport" role="listbox" @scroll="checkScrollButtons">
            <template v-if="!filterQuery.trim()">
              <template v-for="(item, index) in options" :key="index">
              <!-- Group -->
              <template v-if="isGroup(item)">
                <div class="select-group" :class="{ 'select-group--with-separator': index > 0 }">
                  <div class="select-label">{{ item.label }}</div>
                  <div
                    v-for="option in item.options"
                    :key="option.value"
                    role="option"
                    :id="`${selectId}-option-${filteredIndexMap.get(option)}`"
                    :data-index="filteredIndexMap.get(option)"
                    :aria-selected="option.value === modelValue"
                    :aria-disabled="option.disabled"
                    :data-state="option.value === modelValue ? 'checked' : 'unchecked'"
                    class="select-item"
                    :class="{
                      'select-item--selected': option.value === modelValue,
                      'select-item--disabled': option.disabled,
                      'select-item--active': filteredIndexMap.get(option) === activeIndex
                    }"
                    tabindex="0"
                    @click="!option.disabled && updateValue(option.value)"
                    @keydown="handleItemKeydown($event, option.value, option.disabled)"
                  >
                    <span class="select-item__indicator">
                      <Check v-if="option.value === modelValue" :size="16" />
                    </span>
                    <span class="select-item__text">{{ option.label }}</span>
                  </div>
                </div>
              </template>

              <!-- Single Option -->
              <div
                v-else
                role="option"
                :id="`${selectId}-option-${filteredIndexMap.get(item)}`"
                :data-index="filteredIndexMap.get(item)"
                :aria-selected="item.value === modelValue"
                :aria-disabled="item.disabled"
                :data-state="item.value === modelValue ? 'checked' : 'unchecked'"
                class="select-item"
                :class="{
                  'select-item--selected': item.value === modelValue,
                  'select-item--disabled': item.disabled,
                  'select-item--active': filteredIndexMap.get(item) === activeIndex
                }"
                tabindex="0"
                @click="!item.disabled && updateValue(item.value)"
                @keydown="handleItemKeydown($event, item.value, item.disabled)"
              >
                <span class="select-item__indicator">
                  <Check v-if="item.value === modelValue" :size="16" />
                </span>
                <span class="select-item__text">{{ item.label }}</span>
              </div>
              </template>
            </template>

            <!-- Flat filtered list while searching -->
            <template v-else>
              <div v-if="filteredFlat.length === 0" class="select-empty">No matches</div>
              <div
                v-for="option in filteredFlat"
                :key="option.value"
                role="option"
                :id="`${selectId}-option-${filteredIndexMap.get(option)}`"
                :data-index="filteredIndexMap.get(option)"
                :aria-selected="option.value === modelValue"
                :aria-disabled="option.disabled"
                :data-state="option.value === modelValue ? 'checked' : 'unchecked'"
                class="select-item"
                :class="{
                  'select-item--selected': option.value === modelValue,
                  'select-item--disabled': option.disabled,
                  'select-item--active': filteredIndexMap.get(option) === activeIndex
                }"
                tabindex="0"
                @click="!option.disabled && updateValue(option.value)"
                @keydown="handleItemKeydown($event, option.value, option.disabled)"
              >
                <span class="select-item__indicator">
                  <Check v-if="option.value === modelValue" :size="16" />
                </span>
                <span class="select-item__text">{{ option.label }}</span>
              </div>
            </template>
          </div>

          <!-- Scroll Down Button -->
          <button
            v-if="showScrollDown"
            type="button"
            class="select-scroll-button"
            @click="scrollDown"
          >
            <ChevronDown :size="16" />
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style>
/* Select Root */
.select {
  position: relative;
  display: inline-block;
  width: 100%;
}

/* Select Trigger */
.select-trigger {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background-color: var(--input-background);
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
  white-space: nowrap;
  outline: none;
  cursor: pointer;
  transition: color 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  height: 2.25rem;
}

.select-trigger--sm {
  height: 2rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
}

.select-trigger:focus-visible {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring), 0.5);
}

.select-trigger:hover:not(:disabled) {
  background-color: var(--accent);
}

.select-trigger--disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.select-trigger__value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
  text-align: left;
}

.select-trigger__placeholder {
  color: var(--muted-foreground);
}

.select-trigger__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.5;
  flex-shrink: 0;
  color: var(--muted-foreground);
}

.select-trigger__icon svg {
  width: 1rem;
  height: 1rem;
}

/* Select Content */
.select-content {
  position: fixed;
  z-index: 1000000001;
  min-width: 8rem;
  max-width: 32rem;
  overflow: hidden;
  background-color: var(--popover);
  color: var(--popover-foreground);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.select-viewport {
  padding: 0.25rem;
  max-height: 15rem;
  overflow-x: hidden;
  overflow-y: auto;
  scroll-margin: 0.25rem;
}

.select-scroll-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  cursor: default;
  background: none;
  border: none;
  width: 100%;
  color: var(--foreground);
}

.select-scroll-button:hover {
  background-color: var(--accent);
}

.select-scroll-button svg {
  width: 1rem;
  height: 1rem;
}

/* Select Search */
.select-search {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.5rem;
  border-bottom: 1px solid var(--border);
}

.select-search__icon {
  flex-shrink: 0;
  color: var(--muted-foreground);
}

.select-search__input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  padding: 0.125rem 0;
  font-size: 0.8125rem;
  color: var(--popover-foreground);
}

.select-search__input::-webkit-search-cancel-button {
  -webkit-appearance: none;
}

.select-search__clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.125rem;
  border: none;
  border-radius: calc(var(--radius) - 2px);
  background: none;
  color: var(--muted-foreground);
  cursor: pointer;
}

.select-search__clear:hover {
  color: var(--foreground);
  background-color: var(--accent);
}

/* Select Empty */
.select-empty {
  padding: 0.75rem 0.5rem;
  text-align: center;
  font-size: 0.8125rem;
  color: var(--muted-foreground);
}

/* Select Item */
.select-item {
  position: relative;
  display: flex;
  width: 100%;
  cursor: default;
  align-items: center;
  gap: 0.5rem;
  border-radius: calc(var(--radius) - 2px);
  padding: 0.375rem 0.5rem;
  padding-right: 2rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
  outline: none;
  user-select: none;
  scroll-margin: 0.25rem;
  transition: background-color 0.1s ease;
}

.select-item:focus,
.select-item:hover:not(.select-item--disabled) {
  background-color: var(--accent);
  color: var(--accent-foreground);
}

.select-item--active {
  background-color: var(--accent);
  color: var(--accent-foreground);
}

.select-item--disabled {
  pointer-events: none;
  opacity: 0.5;
}

.select-item__indicator {
  position: absolute;
  right: 0.5rem;
  display: flex;
  width: 0.875rem;
  height: 0.875rem;
  align-items: center;
  justify-content: center;
}

.select-item__indicator svg {
  width: 1rem;
  height: 1rem;
}

.select-item__text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Select Group */
.select-group {
  padding: 0.25rem 0;
}

.select-group--with-separator {
  border-top: 1px solid var(--border);
  margin-top: 0.25rem;
  padding-top: 0.5rem;
}

/* Select Label */
.select-label {
  padding: 0.375rem 0.5rem;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: var(--font-weight-medium);
  color: var(--muted-foreground);
}

/* Transition animations */
.select-content-enter-active {
  animation: select-in 0.15s ease-out;
}

.select-content-leave-active {
  animation: select-out 0.1s ease-in;
}

@keyframes select-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-2px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes select-out {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.95) translateY(-2px);
  }
}
</style>
