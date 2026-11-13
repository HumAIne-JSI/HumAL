import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ResolutionSteps from '../components/ResolutionSteps.vue'

describe('ResolutionSteps', () => {
  it('keeps every step non-interactive unless it is reachable', () => {
    const wrapper = mount(ResolutionSteps, { props: { current: 'review' } })

    expect(wrapper.findAll('button')).toHaveLength(0)
  })

  it('lets the user jump to a reachable step but never to the current one', async () => {
    const wrapper = mount(ResolutionSteps, {
      props: { current: 'review', reachable: ['intake', 'review'] }
    })
    const buttons = wrapper.findAll('button')

    expect(buttons.map((button) => button.attributes('aria-label'))).toEqual([
      'Go to step 1: Ticket'
    ])
    expect(wrapper.get('[aria-current="step"]').text()).toContain('Review draft')

    await buttons[0]!.trigger('click')

    expect(wrapper.emitted('select')).toEqual([['intake']])
  })
})
