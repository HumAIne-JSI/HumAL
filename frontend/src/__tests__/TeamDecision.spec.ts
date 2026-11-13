import { afterEach, beforeAll, describe, expect, it } from 'vitest'
import { createPinia } from 'pinia'
import { enableAutoUnmount, mount } from '@vue/test-utils'
import TeamDecision from '../components/TeamDecision.vue'
import ManualTicketDetailPanel from '../components/ManualTicketDetailPanel.vue'
import Select from '../components/ui/Select.vue'
import type { TopKPrediction } from '../types/api'
import type { QueueTicket } from '../stores/useTicketQueueStore'

enableAutoUnmount(afterEach)

// jsdom has no layout, so scrolling the team search into view is a no-op.
beforeAll(() => {
  Element.prototype.scrollIntoView ??= () => {}
})

const TEAMS = ['Network', 'Windows', 'Salesforce']
const SUGGESTIONS: TopKPrediction[] = [
  { label: 'Network', probability: 0.72 },
  { label: 'Windows', probability: 0.18 },
]

function mountDecision(props: { predictions?: TopKPrediction[]; pending?: boolean } = {}) {
  return mount(TeamDecision, {
    props: { teams: TEAMS, predictions: SUGGESTIONS, ...props },
    global: { plugins: [createPinia()] },
  })
}

function submitted(wrapper: ReturnType<typeof mountDecision>) {
  return wrapper.emitted('submit')?.map(([payload]) => payload)
}

async function searchTeam(wrapper: ReturnType<typeof mountDecision>, team: string) {
  wrapper.findComponent(Select).vm.$emit('update:modelValue', team)
  await wrapper.vm.$nextTick()
}

describe('TeamDecision', () => {
  it('stages the top suggestion and only submits on commit', async () => {
    const wrapper = mountDecision()

    expect(submitted(wrapper)).toBeUndefined()
    expect(wrapper.get('.team-decision__summary').text()).toContain('Network')

    await wrapper.get('form').trigger('submit')
    expect(submitted(wrapper)).toEqual([{ team: 'Network', predictionRank: 1 }])
  })

  it('submits the second suggestion with its rank', async () => {
    const wrapper = mountDecision()

    await wrapper.get('input[value="Windows"]').setValue(true)
    await wrapper.get('form').trigger('submit')

    expect(submitted(wrapper)).toEqual([{ team: 'Windows', predictionRank: 2 }])
  })

  it('marks a searched team outside the suggestions as an override', async () => {
    const wrapper = mountDecision()

    await searchTeam(wrapper, 'Salesforce')
    expect(wrapper.get('.team-decision__chip').text()).toBe('Overrides model')

    await wrapper.get('form').trigger('submit')
    expect(submitted(wrapper)).toEqual([{ team: 'Salesforce', predictionRank: null }])
  })

  it('keeps the suggestion rank when a suggested team is picked from search', async () => {
    const wrapper = mountDecision()

    await searchTeam(wrapper, 'Windows')
    expect(wrapper.get<HTMLInputElement>('input[value="Windows"]').element.checked).toBe(true)

    await wrapper.get('form').trigger('submit')
    expect(submitted(wrapper)).toEqual([{ team: 'Windows', predictionRank: 2 }])
  })

  it('requires an explicit team when there are no suggestions', async () => {
    const wrapper = mountDecision({ predictions: [] })
    const assign = wrapper.get('button[type="submit"]')

    expect(assign.attributes('disabled')).toBeDefined()
    await wrapper.get('form').trigger('submit')
    expect(submitted(wrapper)).toBeUndefined()
    // Committing with nothing staged opens the team search instead.
    const trigger = wrapper.findComponent(Select).get('[aria-expanded]')
    expect(trigger.attributes('aria-expanded')).toBe('true')

    await searchTeam(wrapper, 'Salesforce')
    expect(assign.attributes('disabled')).toBeUndefined()
    await wrapper.get('form').trigger('submit')
    expect(submitted(wrapper)).toEqual([{ team: 'Salesforce', predictionRank: null }])
  })

  it('follows refined suggestions until the user makes a choice', async () => {
    const wrapper = mountDecision({ predictions: [{ label: 'Network', probability: 0.5 }] })

    await wrapper.setProps({
      predictions: [
        { label: 'Windows', probability: 0.6 },
        { label: 'Network', probability: 0.3 },
      ],
    })
    expect(wrapper.get('.team-decision__summary').text()).toContain('Windows')

    await searchTeam(wrapper, 'Salesforce')
    await wrapper.setProps({ predictions: SUGGESTIONS })
    expect(wrapper.get('.team-decision__summary').text()).toContain('Salesforce')
  })

  it('ignores repeat commits until the pending request settles', async () => {
    const wrapper = mountDecision()

    await wrapper.get('form').trigger('submit')
    await wrapper.get('form').trigger('submit')
    expect(submitted(wrapper)).toHaveLength(1)

    await wrapper.setProps({ pending: true })
    await wrapper.setProps({ pending: false })
    await wrapper.get('form').trigger('submit')
    expect(submitted(wrapper)).toHaveLength(2)
  })

  it('keeps the submitted team while the model refines its suggestions', async () => {
    const wrapper = mountDecision()

    await wrapper.get('form').trigger('submit')
    await wrapper.setProps({
      pending: true,
      predictions: [
        { label: 'Windows', probability: 0.6 },
        { label: 'Network', probability: 0.3 }
      ]
    })

    expect(wrapper.get('.team-decision__summary strong').text()).toBe('Network')
    expect(submitted(wrapper)).toEqual([{ team: 'Network', predictionRank: 1 }])
  })

  it('commits from Enter on a focused suggestion', async () => {
    const wrapper = mountDecision()

    await wrapper.get('input[value="Windows"]').setValue(true)
    await wrapper.get('input[value="Windows"]').trigger('keydown', { key: 'Enter' })

    expect(submitted(wrapper)).toEqual([{ team: 'Windows', predictionRank: 2 }])
  })

  it('does not commit from a held Enter key', async () => {
    const wrapper = mountDecision()

    await wrapper.get('input[value="Network"]').trigger('keydown', { key: 'Enter', repeat: true })

    expect(submitted(wrapper)).toBeUndefined()
    await wrapper.get('input[value="Network"]').trigger('keydown', { key: 'Enter' })
    expect(submitted(wrapper)).toHaveLength(1)
  })

  it('reports whether reset undid a user choice', async () => {
    const wrapper = mountDecision()

    expect(wrapper.vm.reset()).toBe(false)
    await searchTeam(wrapper, 'Salesforce')
    expect(wrapper.vm.reset()).toBe(true)
    await wrapper.vm.$nextTick()
    expect(wrapper.get('.team-decision__summary').text()).toContain('Network')
  })
})

describe('manual decision save feedback', () => {
  const ticket: QueueTicket = {
    id: 'ticket-1',
    ref: 'TKT-1',
    title: 'Network access',
    description: 'Restore network access',
    status: 'resolved',
    timestamp: new Date('2026-01-01')
  }

  it('allows retrying a failed relabel and only shows success when acknowledged', async () => {
    const wrapper = mount(ManualTicketDetailPanel, {
      props: { ticket, teams: TEAMS },
      global: { plugins: [createPinia()] }
    })
    const decision = wrapper.findComponent(TeamDecision)
    await searchTeam(decision, 'Network')
    await decision.get('form').trigger('submit')
    await wrapper.setProps({ feedbackPending: true })
    expect(wrapper.find('.manual-detail__labeled-flash').exists()).toBe(false)

    await wrapper.setProps({ feedbackPending: false })
    expect(decision.get('button[type="submit"]').attributes('disabled')).toBeUndefined()
    await decision.get('form').trigger('submit')
    expect(wrapper.emitted('confirm')).toEqual([['Network'], ['Network']])

    wrapper.vm.markAssigned(ticket.id, 'Network')
    await wrapper.vm.$nextTick()
    expect(wrapper.get('.manual-detail__labeled-flash').text()).toContain('Network')
    expect(decision.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  })

  it('does not show a previous ticket success on the newly opened ticket', async () => {
    const wrapper = mount(ManualTicketDetailPanel, {
      props: { ticket, teams: TEAMS },
      global: { plugins: [createPinia()] }
    })

    await wrapper.setProps({ ticket: { ...ticket, id: 'ticket-2' } })
    wrapper.vm.markAssigned(ticket.id, 'Network')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.manual-detail__labeled-flash').exists()).toBe(false)
  })
})
