import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { enableAutoUnmount, mount } from '@vue/test-utils'
import { useKeyboardNavigation } from '../composables/useKeyboardNavigation'

enableAutoUnmount(afterEach)

function mountShortcuts() {
  const handlers = { onCommit: vi.fn(), onSelectChoice: vi.fn(), onFocusTeamSearch: vi.fn() }
  const Host = defineComponent({
    setup() {
      useKeyboardNavigation({ enabled: true }).registerNavigationShortcuts(handlers)
      return () =>
        h('div', [
          h('button', { id: 'action' }, 'Action'),
          h('input', { id: 'text', type: 'text' }),
          h('input', { id: 'radio', type: 'radio' }),
          h('div', { id: 'current', tabindex: 0, 'aria-current': 'true' }),
        ])
    },
  })
  const wrapper = mount(Host, { attachTo: document.body })
  return { wrapper, handlers }
}

function press(key: string, init: KeyboardEventInit = {}) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, ...init })
  ;(document.activeElement ?? document.body).dispatchEvent(event)
  return event
}

function focus(id: string) {
  document.getElementById(id)?.focus()
}

describe('useKeyboardNavigation team decision shortcuts', () => {
  it('commits on Enter only when focus is neutral or on the current item', () => {
    const { handlers } = mountShortcuts()

    focus('action')
    expect(press('Enter').defaultPrevented).toBe(false)
    expect(handlers.onCommit).not.toHaveBeenCalled()

    focus('current')
    press('Enter')
    ;(document.activeElement as HTMLElement).blur()
    press('Enter')
    expect(handlers.onCommit).toHaveBeenCalledTimes(2)
  })

  it('skips keys a focused control already handled', () => {
    const { handlers } = mountShortcuts()
    const event = new KeyboardEvent('keydown', { key: '1', bubbles: true, cancelable: true })
    event.preventDefault()

    document.body.dispatchEvent(event)
    expect(handlers.onSelectChoice).not.toHaveBeenCalled()
  })

  it('does not assign another ticket while Enter remains held', () => {
    const { handlers } = mountShortcuts()

    press('Enter', { repeat: true })
    focus('current')
    press('Enter', { repeat: true })
    expect(handlers.onCommit).not.toHaveBeenCalled()

    press('Enter')
    expect(handlers.onCommit).toHaveBeenCalledTimes(1)
  })

  it('stays live on radios but not in text fields', () => {
    const { handlers } = mountShortcuts()

    focus('text')
    press('2')
    focus('radio')
    press('2')
    expect(handlers.onSelectChoice).toHaveBeenCalledTimes(1)
    expect(handlers.onSelectChoice).toHaveBeenCalledWith(2)
  })

  it('matches symbol keys typed with Shift on other layouts', () => {
    const { handlers } = mountShortcuts()

    press('/', { shiftKey: true })
    expect(handlers.onFocusTeamSearch).toHaveBeenCalledTimes(1)
  })
})
