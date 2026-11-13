import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import Navigation from '../components/Navigation.vue'
import primaryLogo from '../assets/images/logo.png'
import secondaryLogo from '../assets/images/humaine-logo.png'
import { useSpecialistAuthStore } from '../stores/useSpecialistAuthStore'

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
  sessionStorage.clear()
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

describe('Navigation Tier 2 workspace scope', () => {
  const page = { template: '<div />' }

  async function mountNavigation(props: { scope?: 'main' | 'specialist' } = {}) {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/ticket-resolution', component: page },
        { path: '/ticket-resolution/performance', component: page },
        { path: '/ticket-resolution/login', name: 'specialist-login', component: page }
      ]
    })
    await router.push('/ticket-resolution')
    await router.isReady()
    const pinia = createPinia()
    const session = useSpecialistAuthStore(pinia)
    session.login('ada')
    const wrapper = mount(Navigation, {
      props,
      global: { plugins: [pinia, router], stubs: { InstanceSelector: true, MockToggle: true } }
    })
    return { router, session, wrapper }
  }

  it.each(['main', 'specialist'] as const)(
    'shows primary and secondary branding only while the %s sidebar is expanded',
    async scope => {
      const { wrapper } = await mountNavigation({ scope })

      expect(wrapper.get('.sidebar__header img').attributes('src')).toBe(primaryLogo)
      expect(wrapper.get('.sidebar__footer img').attributes('src')).toBe(secondaryLogo)

      await wrapper.get('button[aria-label="Collapse sidebar"]').trigger('click')
      expect(wrapper.find('img.humaine-logo').exists()).toBe(false)

      await wrapper.get('button[aria-label="Expand sidebar"]').trigger('click')
      expect(wrapper.get('.sidebar__header img').attributes('src')).toBe(primaryLogo)
      expect(wrapper.get('.sidebar__footer img').attributes('src')).toBe(secondaryLogo)
    }
  )

  it('lists only the Tier 2 pages and opens them in the same tab', async () => {
    const { wrapper } = await mountNavigation({ scope: 'specialist' })

    const groups = wrapper.findAll('[role="group"]')
    expect(groups.map(group => group.attributes('aria-label'))).toEqual([
      'Level 2: Resolution support'
    ])
    const links = groups[0]!.findAll('a')
    expect(links.map(link => link.attributes('href'))).toEqual([
      '/ticket-resolution',
      '/ticket-resolution/performance'
    ])
    expect(links.map(link => link.attributes('target'))).toEqual([undefined, undefined])
    expect(links[0]!.classes()).toContain('sidebar__link--active')
    expect(links[1]!.classes()).not.toContain('sidebar__link--active')
  })

  it('presents itself as its own app without the Tier 1 project controls', async () => {
    const { wrapper } = await mountNavigation({ scope: 'specialist' })

    expect(wrapper.get('h1').text()).toBe('Specialist Workspace')
    expect(wrapper.find('.sidebar__instance').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Tour guide')
  })

  it('keeps the project selector and tour in the main app sidebar', async () => {
    const { wrapper } = await mountNavigation()

    expect(wrapper.get('h1').text()).toBe('IT Ticket Manager')
    expect(wrapper.find('.sidebar__instance').exists()).toBe(true)
    expect(wrapper.text()).toContain('Tour guide')
  })

  it('signs out of the workspace session and returns to its sign-in', async () => {
    const { router, session, wrapper } = await mountNavigation({ scope: 'specialist' })
    expect(wrapper.get('.sidebar__account-user').text()).toBe('ada')

    const signOut = wrapper.findAll('button').find(button => button.text() === 'Sign out')!
    await signOut.trigger('click')
    await flushPromises()

    expect(session.isAuthenticated).toBe(false)
    expect(router.currentRoute.value.name).toBe('specialist-login')
  })
})
