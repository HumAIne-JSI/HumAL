import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia, type Pinia } from 'pinia'
import ResolutionIntake from '../components/ResolutionIntake.vue'
import { useLabeledTicketsStore } from '../stores/useLabeledTicketsStore'

const QUEUED_TICKET = {
  ref: 'TKT-1042',
  title: 'Cannot access shared finance drive',
  description: 'Access denied since the migration.',
  label: 'Service Desk',
  instanceId: null,
  mock: true,
  timestamp: '2026-01-01T09:00:00.000Z'
}

let pinia: Pinia

function mountIntake(props: Record<string, unknown> = {}) {
  return mount(ResolutionIntake, {
    props: {
      title: '',
      description: '',
      instanceId: 0,
      topK: 5,
      category: '',
      subcategory: '',
      ...props
    },
    global: { plugins: [pinia], stubs: { ResolutionAdvancedOptions: true } }
  })
}

const queueTicket = () => useLabeledTicketsStore().record(QUEUED_TICKET)

const selectedTab = (wrapper: ReturnType<typeof mountIntake>) =>
  wrapper.get('[role="tab"][aria-selected="true"]').text()

const detailsPanel = (wrapper: ReturnType<typeof mountIntake>) =>
  wrapper.findAll('[role="tabpanel"]')[1]!

describe('ResolutionIntake', () => {
  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('opens on the queue when labeled tickets are waiting, otherwise on ticket details', () => {
    expect(selectedTab(mountIntake())).toContain('Ticket details')

    queueTicket()
    expect(selectedTab(mountIntake())).toContain('From queue')
  })

  it('generates on Ctrl+Enter only once the ticket has content', async () => {
    const wrapper = mountIntake()
    const pressShortcut = () =>
      detailsPanel(wrapper).trigger('keydown', { key: 'Enter', ctrlKey: true })

    await pressShortcut()
    expect(wrapper.emitted('generate')).toBeUndefined()

    await wrapper.setProps({ title: 'VPN keeps dropping' })
    await pressShortcut()
    expect(wrapper.emitted('generate')).toHaveLength(1)
  })

  it('emits the picked queue ticket and switches to the details tab for review', async () => {
    queueTicket()
    const wrapper = mountIntake()

    const ticketButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes(QUEUED_TICKET.title))
    await ticketButton!.trigger('click')

    expect(wrapper.emitted('pick-ticket')?.[0]).toEqual([QUEUED_TICKET])
    expect(selectedTab(wrapper)).toContain('Ticket details')
    expect(wrapper.emitted('generate')).toBeUndefined()
  })
})
