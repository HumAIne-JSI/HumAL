import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import Navigation from '../components/Navigation.vue'

enableAutoUnmount(afterEach)

beforeEach(() => {
  vi.stubGlobal('localStorage', {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn()
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Navigation triage levels', () => {
  it('keeps both groups and their links accessible when collapsed', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }]
    })
    await router.push('/')
    await router.isReady()
    const wrapper = mount(Navigation, {
      global: {
        plugins: [createPinia(), router],
        stubs: { InstanceSelector: true, MockToggle: true }
      }
    })

    const groups = wrapper.findAll('[role="group"]')
    expect(groups.map(group => group.attributes('aria-label'))).toEqual([
      'Level 1: Triage and routing',
      'Level 2: Resolution support'
    ])
    expect(groups[0]!.text()).toContain('HumAIne Core · TRL 5')
    expect(groups[1]!.text()).toContain('Exploratory preview')

    await wrapper.get('button[aria-label="Collapse sidebar"]').trigger('click')

    expect(groups[0]!.get('a[href="/queue"]').attributes('aria-label')).toBe('Smart Assign')
    expect(groups[1]!.get('a[href="/ticket-resolution"]').attributes('aria-label')).toBe(
      'Specialist Resolution Workspace (opens in a new tab)'
    )
    expect(groups[1]!.get('a[href="/analytics"]').attributes('aria-label')).toBe('Performance')
  })
})
