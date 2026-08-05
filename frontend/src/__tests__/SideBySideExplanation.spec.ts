import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SideBySideExplanation from '../components/SideBySideExplanation.vue'

describe('SideBySideExplanation', () => {
  it('renders historical and predicted-class neighbors separately', () => {
    const wrapper = mount(SideBySideExplanation, {
      props: {
        historicalTicket: {
          ref: 'H-1',
          label: 'Historical Team',
          similarity: 0.81,
          title: 'Historical ticket',
          description: 'Historical description',
        },
        predictedClassTicket: {
          ref: 'P-1',
          label: 'Predicted Team',
          similarity: 0.74,
          title: 'Predicted ticket',
          description: 'Predicted description',
        },
      },
    })

    expect(wrapper.text()).toContain('Closest past ticket')
    expect(wrapper.text()).toContain('Closest predicted class ticket')
    expect(wrapper.text()).toContain('H-1')
    expect(wrapper.text()).toContain('P-1')
    expect(wrapper.text()).toContain('Historical description')
    expect(wrapper.text()).toContain('Predicted description')
    expect(wrapper.findAll('mark')).toHaveLength(0)
    expect(wrapper.text()).not.toContain('Current ticket')
  })

  it('keeps missing neighbor roles independent', () => {
    const wrapper = mount(SideBySideExplanation, {
      props: {
        historicalTicket: null,
        predictedClassTicket: {
          ref: 'P-1',
          title: 'Predicted ticket',
        },
      },
    })

    expect(wrapper.text()).toContain('No historical ticket found.')
    expect(wrapper.text()).not.toContain('No predicted class ticket found.')
    expect(wrapper.text()).toContain('Predicted ticket')
  })
})
