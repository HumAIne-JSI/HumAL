import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, mount } from '@vue/test-utils'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import ResolutionDraft from '../components/ResolutionDraft.vue'
import ResolutionIntake from '../components/ResolutionIntake.vue'
import ResolutionSent from '../components/ResolutionSent.vue'
import TicketResolution from '../pages/TicketResolution.vue'
import { resolutionApiService } from '../services/resolutionApi'
import { useMockModeStore } from '../stores/useMockModeStore'

enableAutoUnmount(afterEach)

beforeEach(() => {
  vi.stubGlobal('localStorage', {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn()
  })
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

function mountPage() {
  const pinia = createPinia()
  const mock = useMockModeStore(pinia)
  mock.setMockMode(true)
  const wrapper = mount(TicketResolution, {
    global: {
      plugins: [pinia, VueQueryPlugin],
      stubs: {
        ResolutionIntake: true,
        ResolutionTicketSummary: true,
        ResolutionDraft: true,
        ResolutionSimilarReplies: true,
        ResolutionSent: true
      }
    }
  })
  return { wrapper, mock }
}

type Page = ReturnType<typeof mountPage>['wrapper']

const intake = (page: Page) => page.findComponent(ResolutionIntake)
const draft = (page: Page) => page.findComponent(ResolutionDraft)
const stepButtons = (page: Page) => page.findAll('ol[aria-label="Progress"] button')
const stepButton = (page: Page, step: number) =>
  page.find(`button[aria-label^="Go to step ${step}:"]`)

// Resolves once the draft is in the review step and the stepper is unlocked again.
async function draftTicket(page: Page) {
  intake(page).vm.$emit('update:title', 'Printer offline')
  intake(page).vm.$emit('generate')
  await vi.waitFor(() => {
    expect(draft(page).exists() && draft(page).props('result')).toBeTruthy()
    expect(stepButton(page, 1).exists()).toBe(true)
  })
}

describe('TicketResolution stepper', () => {
  it('only offers a way back once there is a draft to return to', async () => {
    const { wrapper } = mountPage()
    expect(stepButtons(wrapper)).toHaveLength(0)

    await draftTicket(wrapper)

    expect(stepButtons(wrapper).map(button => button.attributes('aria-label'))).toEqual([
      'Go to step 1: Ticket'
    ])
  })

  it('goes back to step 1 with the ticket and draft intact, then forward to the draft', async () => {
    const { wrapper } = mountPage()
    await draftTicket(wrapper)

    await stepButton(wrapper, 1).trigger('click')

    expect(draft(wrapper).exists()).toBe(false)
    expect(intake(wrapper).props('title')).toBe('Printer offline')
    expect(intake(wrapper).props('hasDraft')).toBe(true)

    await stepButton(wrapper, 2).trigger('click')

    expect(intake(wrapper).exists()).toBe(false)
    expect(draft(wrapper).props('result')).toBeTruthy()
  })

  it('locks while the reply is being sent, then step 1 starts a fresh ticket', async () => {
    const { wrapper, mock } = mountPage()
    await draftTicket(wrapper)

    let finishSaving: (value: { ok: boolean }) => void = () => {}
    vi.spyOn(resolutionApiService, 'saveTicket').mockReturnValue(
      new Promise(resolve => (finishSaving = resolve))
    )
    mock.setMockMode(false)
    draft(wrapper).vm.$emit('send')

    await vi.waitFor(() => expect(stepButtons(wrapper)).toHaveLength(0))

    finishSaving({ ok: true })
    await vi.waitFor(() => expect(wrapper.findComponent(ResolutionSent).exists()).toBe(true))
    await vi.waitFor(() => expect(stepButton(wrapper, 1).exists()).toBe(true))

    await stepButton(wrapper, 1).trigger('click')

    expect(intake(wrapper).props('title')).toBe('')
    expect(intake(wrapper).props('hasDraft')).toBe(false)
    expect(stepButtons(wrapper)).toHaveLength(0)
  })
})
