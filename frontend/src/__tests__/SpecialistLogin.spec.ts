import { afterEach, describe, expect, it } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import SpecialistLogin from '../pages/SpecialistLogin.vue'
import { useSpecialistAuthStore } from '../stores/useSpecialistAuthStore'

enableAutoUnmount(afterEach)

afterEach(() => {
  sessionStorage.clear()
})

const page = { render: () => null }

async function mountLogin(redirect?: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/ticket-resolution', component: page },
      { path: '/ticket-resolution/performance', component: page },
      { path: '/ticket-resolution/login', component: SpecialistLogin },
      { path: '/analytics', component: page }
    ]
  })
  await router.push({ path: '/ticket-resolution/login', query: redirect ? { redirect } : {} })
  const pinia = createPinia()
  const wrapper = mount(SpecialistLogin, { global: { plugins: [pinia, router] } })
  return { router, wrapper, session: useSpecialistAuthStore(pinia) }
}

async function fillIn(wrapper: Awaited<ReturnType<typeof mountLogin>>['wrapper']) {
  await wrapper.get('input[name="username"]').setValue('ada')
  await wrapper.get('input[name="password"]').setValue('anything')
}

describe('SpecialistLogin', () => {
  it('stays locked until both a username and a password are entered', async () => {
    const { wrapper } = await mountLogin()
    const submit = wrapper.get('button[type="submit"]')
    expect(submit.attributes('disabled')).toBeDefined()

    await wrapper.get('input[name="username"]').setValue('ada')
    expect(submit.attributes('disabled')).toBeDefined()

    await wrapper.get('input[name="password"]').setValue('anything')
    expect(submit.attributes('disabled')).toBeUndefined()
  })

  it('opens a session and returns to the workspace page that was requested', async () => {
    const { router, wrapper, session } = await mountLogin('/ticket-resolution/performance')
    await fillIn(wrapper)

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(session.username).toBe('ada')
    expect(router.currentRoute.value.path).toBe('/ticket-resolution/performance')
  })

  it('ignores a redirect that leaves the workspace', async () => {
    const { router, wrapper } = await mountLogin('/analytics')
    await fillIn(wrapper)

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/ticket-resolution')
  })
})
