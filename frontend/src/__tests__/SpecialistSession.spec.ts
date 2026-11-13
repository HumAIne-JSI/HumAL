import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import router from '../router'
import { useSpecialistAuthStore } from '../stores/useSpecialistAuthStore'

// The guard does not depend on the page content; skip the heavy page modules.
vi.mock('../pages/TicketResolution.vue', () => ({ default: { render: () => null } }))
vi.mock('../pages/Analytics.vue', () => ({ default: { render: () => null } }))

beforeEach(() => {
  setActivePinia(createPinia())
})

afterEach(() => {
  sessionStorage.clear()
})

describe('Tier 2 workspace session', () => {
  it('sends visitors without a session to the workspace sign-in and remembers the target', async () => {
    await router.push('/ticket-resolution/performance')

    const { name, query } = router.currentRoute.value
    expect(name).toBe('specialist-login')
    expect(query.redirect).toBe('/ticket-resolution/performance')
  })

  it('lets a signed-in specialist through without the main app sign-in', async () => {
    useSpecialistAuthStore().login('ada')

    await router.push('/ticket-resolution/performance')

    expect(router.currentRoute.value.name).toBe('specialist-performance')
  })

  it('skips the sign-in page once signed in', async () => {
    useSpecialistAuthStore().login('ada')

    await router.push('/ticket-resolution/login')

    expect(router.currentRoute.value.name).toBe('ticket-resolution')
  })

  it('keeps the session across reloads until sign out', () => {
    useSpecialistAuthStore().login('ada')

    setActivePinia(createPinia())
    const reloaded = useSpecialistAuthStore()
    expect(reloaded.isAuthenticated).toBe(true)
    expect(reloaded.username).toBe('ada')

    reloaded.logout()
    setActivePinia(createPinia())
    expect(useSpecialistAuthStore().isAuthenticated).toBe(false)
  })
})
