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
      { path: '/standalone', component: page, meta: { standalone: true, label: 'Standalone' } },
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
        HumaineLogo: true,
        Toaster: true,
        // Queries the API, which needs VueQueryPlugin and the network.
        TutorialHost: true,
      },
    },
  })
  const hasSidebar = () => wrapper.findComponent({ name: 'Navigation' }).exists()
  return { router, wrapper, hasSidebar }
}

describe('App', () => {
  it('mounts the application shell with its required providers', async () => {
    const { wrapper } = await mountApp('/')

    expect(wrapper.find('.app-layout').exists()).toBe(true)
  })

  it('hides the sidebar on routes flagged hideSidebar', async () => {
    const { router, wrapper, hasSidebar } = await mountApp('/')
    expect(hasSidebar()).toBe(true)

    await router.push('/login')
    await nextTick()

    expect(hasSidebar()).toBe(false)
    expect(wrapper.find('.app-standalone-bar').exists()).toBe(false)
  })

  it('shows the standalone header instead of the sidebar on standalone routes', async () => {
    const { wrapper, hasSidebar } = await mountApp('/standalone')

    expect(hasSidebar()).toBe(false)
    expect(wrapper.find('.app-standalone-bar').exists()).toBe(true)
  })

  it('keeps the sidebar hidden until the first navigation resolves', async () => {
    const { router, hasSidebar } = await mountApp()
    expect(hasSidebar()).toBe(false)

    await router.push('/')
    await nextTick()

    expect(hasSidebar()).toBe(true)
  })
})
