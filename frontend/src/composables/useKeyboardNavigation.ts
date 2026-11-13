import { ref, onMounted, onUnmounted, watch, type Ref, computed } from 'vue'

export type KeyboardShortcut = {
  key: string
  description: string
  action: () => void
  // Optional modifiers
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  // Optional guard; when it returns false the key is left to the browser
  when?: (event: KeyboardEvent) => boolean
  // Category for grouping in help modal
  category?: 'navigation' | 'actions' | 'bulk' | 'general'
}

export interface UseKeyboardNavigationOptions {
  /** Whether keyboard shortcuts are enabled */
  enabled?: Ref<boolean> | boolean
  /** Callback when navigation occurs */
  onNavigate?: (direction: 'next' | 'prev') => void
  /** Callback for action keys */
  onAction?: (action: string) => void
}

// Number keys 1..N stage the matching ranked model suggestion.
export const SUGGESTION_SHORTCUT_COUNT = 2

// Inputs that don't take typed text, so shortcuts stay live while they're focused.
const NON_TEXT_INPUT_TYPES = new Set(['radio', 'checkbox', 'button', 'submit', 'reset'])

// True when no control claims a bare key like Enter: nothing is focused, or
// focus rests on the current item of a list (e.g. the open ticket row).
function canCommitFromKeyboard(event: KeyboardEvent) {
  if (event.repeat) return false
  const activeElement = document.activeElement
  if (!activeElement || activeElement === document.body) return true
  return activeElement.getAttribute('aria-current') === 'true'
}

// Digits and symbols need Shift on many keyboard layouts (e.g. "/" and "?" on
// German QWERTZ), so only letters are matched against the Shift modifier.
function matchesShift(shortcut: KeyboardShortcut, event: KeyboardEvent) {
  const isLetter = /^[a-z]$/i.test(shortcut.key)
  return !isLetter && shortcut.key.length === 1 ? true : !!shortcut.shift === event.shiftKey
}

// Global enabled state that can be toggled from settings
const globalEnabled = ref(true)

export function setKeyboardShortcutsEnabled(enabled: boolean) {
  globalEnabled.value = enabled
}

export function getKeyboardShortcutsEnabled() {
  return globalEnabled.value
}

/**
 * Composable for keyboard navigation and shortcuts
 */
export function useKeyboardNavigation(options: UseKeyboardNavigationOptions = {}) {
  const shortcuts = ref<KeyboardShortcut[]>([])
  const isHelpOpen = ref(false)

  // Compute whether enabled based on option or global state
  const isEnabled = computed(() => {
    if (options.enabled !== undefined) {
      return typeof options.enabled === 'boolean' ? options.enabled : options.enabled.value
    }
    return globalEnabled.value
  })

  // Track if we're in an input element (disable shortcuts)
  const isInInput = () => {
    const activeElement = document.activeElement
    if (!activeElement) return false
    const tagName = activeElement.tagName.toLowerCase()
    if (tagName === 'input') {
      return !NON_TEXT_INPUT_TYPES.has((activeElement as HTMLInputElement).type)
    }
    return (
      tagName === 'textarea' ||
      tagName === 'select' ||
      activeElement.getAttribute('contenteditable') === 'true'
    )
  }

  const handleKeyDown = (event: KeyboardEvent) => {
    // Skip if disabled, in input, or a focused control already handled the key
    if (!isEnabled.value || isInInput() || event.defaultPrevented) return

    // Find matching shortcut
    for (const shortcut of shortcuts.value) {
      const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase()
      const ctrlMatch = !!shortcut.ctrl === (event.ctrlKey || event.metaKey)
      const shiftMatch = matchesShift(shortcut, event)
      const altMatch = !!shortcut.alt === event.altKey

      if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
        if (shortcut.when && !shortcut.when(event)) return
        event.preventDefault()
        shortcut.action()
        return
      }
    }
  }

  // Register shortcut
  function registerShortcut(shortcut: KeyboardShortcut) {
    // Avoid duplicates
    const existing = shortcuts.value.findIndex(
      (s) =>
        s.key === shortcut.key &&
        s.ctrl === shortcut.ctrl &&
        s.shift === shortcut.shift &&
        s.alt === shortcut.alt
    )
    if (existing >= 0) {
      shortcuts.value[existing] = shortcut
    } else {
      shortcuts.value.push(shortcut)
    }
  }

  // Unregister shortcut
  function unregisterShortcut(key: string, modifiers?: { ctrl?: boolean; shift?: boolean; alt?: boolean }) {
    shortcuts.value = shortcuts.value.filter(
      (s) =>
        !(
          s.key === key &&
          s.ctrl === modifiers?.ctrl &&
          s.shift === modifiers?.shift &&
          s.alt === modifiers?.alt
        )
    )
  }

  // Register common navigation shortcuts
  function registerNavigationShortcuts(handlers: {
    onNext?: () => void
    onPrev?: () => void
    onOpen?: () => void
    onClose?: () => void
    onToggleBulk?: () => void
    onSelectAll?: () => void
    onHelp?: () => void
    onSelectChoice?: (rank: number) => void
    onFocusTeamSearch?: () => void
    onCommit?: () => void
  }) {
    if (handlers.onNext) {
      registerShortcut({
        key: 'j',
        description: 'Next ticket',
        category: 'navigation',
        action: handlers.onNext,
      })
      registerShortcut({
        key: 'ArrowDown',
        description: 'Next ticket',
        category: 'navigation',
        action: handlers.onNext,
      })
    }

    if (handlers.onPrev) {
      registerShortcut({
        key: 'k',
        description: 'Previous ticket',
        category: 'navigation',
        action: handlers.onPrev,
      })
      registerShortcut({
        key: 'ArrowUp',
        description: 'Previous ticket',
        category: 'navigation',
        action: handlers.onPrev,
      })
    }

    if (handlers.onOpen) {
      registerShortcut({
        key: 'Enter',
        description: 'Open ticket details',
        category: 'navigation',
        action: handlers.onOpen,
      })
      registerShortcut({
        key: 'o',
        description: 'Open ticket details',
        category: 'navigation',
        action: handlers.onOpen,
      })
    }

    if (handlers.onClose) {
      registerShortcut({
        key: 'Escape',
        description: 'Close / Clear selection',
        category: 'navigation',
        action: handlers.onClose,
      })
    }

    if (handlers.onToggleBulk) {
      registerShortcut({
        key: 'x',
        description: 'Toggle bulk select',
        category: 'bulk',
        action: handlers.onToggleBulk,
      })
    }

    if (handlers.onSelectAll) {
      registerShortcut({
        key: 'a',
        shift: true,
        description: 'Select all visible',
        category: 'bulk',
        action: handlers.onSelectAll,
      })
    }

    if (handlers.onHelp) {
      registerShortcut({
        key: '?',
        description: 'Show keyboard shortcuts',
        category: 'general',
        action: handlers.onHelp,
      })
    }

    // Team decision: stage a choice first, then commit it explicitly.
    const { onSelectChoice, onFocusTeamSearch, onCommit } = handlers
    if (onSelectChoice) {
      for (let rank = 1; rank <= SUGGESTION_SHORTCUT_COUNT; rank++) {
        registerShortcut({
          key: String(rank),
          description: `Select suggestion ${rank}`,
          category: 'actions',
          action: () => onSelectChoice(rank),
        })
      }
    }

    if (onFocusTeamSearch) {
      registerShortcut({
        key: '/',
        description: 'Search all teams',
        category: 'actions',
        action: onFocusTeamSearch,
      })
    }

    if (onCommit) {
      registerShortcut({
        key: 'Enter',
        description: 'Assign the selected team',
        category: 'actions',
        action: onCommit,
        when: canCommitFromKeyboard,
      })
    }
  }

  function openHelp() {
    isHelpOpen.value = true
  }

  function closeHelp() {
    isHelpOpen.value = false
  }

  // Lifecycle
  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    shortcuts,
    isHelpOpen,
    isEnabled,
    registerShortcut,
    unregisterShortcut,
    registerNavigationShortcuts,
    openHelp,
    closeHelp,
    setEnabled: setKeyboardShortcutsEnabled,
  }
}

/**
 * Format shortcut key for display
 */
export function formatShortcutKey(shortcut: KeyboardShortcut): string {
  const parts: string[] = []
  if (shortcut.ctrl) parts.push('Ctrl')
  if (shortcut.shift) parts.push('Shift')
  if (shortcut.alt) parts.push('Alt')
  
  // Format special keys
  let key = shortcut.key
  switch (key) {
    case 'ArrowUp':
      key = '↑'
      break
    case 'ArrowDown':
      key = '↓'
      break
    case 'ArrowLeft':
      key = '←'
      break
    case 'ArrowRight':
      key = '→'
      break
    case 'Enter':
      key = '↵'
      break
    case 'Escape':
      key = 'Esc'
      break
    case ' ':
      key = 'Space'
      break
  }

  parts.push(key.toUpperCase())
  return parts.join(' + ')
}
