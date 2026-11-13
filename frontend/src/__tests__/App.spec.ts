import { describe, it, expect } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import App from '../App.vue'

const page = { render: () => null }

// Mounts the shell on `path`, or before any navigation when no path is given.
async function mountApp(path?: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: page },
      { path: '/login', component: page, meta: { hideSidebar: true } },
      { path: '/specialist', component: page, meta: { app: 'specialist' } },
    ],
  })
  if (path) {
    await router.push(path)
    await router.isReady()
  }

  const wrapper = mount(App, {
    global: {
      plugins: [createPinia(), router],
      stubs: {
        Navigation: true,
        Toaster: true,
        // Queries the API, which needs VueQueryPlugin and the network.
        TutorialHost: true,
      },
    },
  })
  const sidebar = () => wrapper.findComponent({ name: 'Navigation' })
  const hasSidebar = () => sidebar().exists()
  return { router, wrapper, sidebar, hasSidebar }
}

describe('App', () => {
  it('mounts the application shell with its required providers', async () => {
    const { wrapper } = await mountApp('/')

    expect(wrapper.find('.app-layout').exists()).toBe(true)
  })

  it('hides the sidebar on routes flagged hideSidebar', async () => {
    const { router, hasSidebar } = await mountApp('/')
    expect(hasSidebar()).toBe(true)

    await router.push('/login')
    await nextTick()

    expect(hasSidebar()).toBe(false)
  })

  it('scopes the sidebar to the Tier 2 entries on specialist routes', async () => {
    const { router, sidebar } = await mountApp('/')
    expect(sidebar().props('scope')).toBe('main')

    await router.push('/specialist')
    await nextTick()

    expect(sidebar().props('scope')).toBe('specialist')
  })

  it('keeps the sidebar hidden until the first navigation resolves', async () => {
    const { router, hasSidebar } = await mountApp()
    expect(hasSidebar()).toBe(false)

    await router.push('/')
    await nextTick()

    expect(hasSidebar()).toBe(true)
  })
})
