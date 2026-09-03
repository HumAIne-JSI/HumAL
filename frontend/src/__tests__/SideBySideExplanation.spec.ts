import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SideBySideExplanation from '../components/SideBySideExplanation.vue'

describe('SideBySideExplanation', () => {
  it('renders historical and predicted-class neighbors separately', () => {
    const wrapper = mount(SideBySideExplanation, {
      props: {
        historicalTickets: [
          {
            ref: 'H-1',
            label: 'Historical Team',
            similarity: 0.81,
            title: 'Historical ticket one',
            bestSentence: 'Historical best sentence one.',
            description: 'Historical description one.',
          },
          {
            ref: 'H-2',
            label: 'Historical Team',
            similarity: 0.74,
            title: 'Historical ticket two',
            bestSentence: 'Historical best sentence two.',
            description: 'Historical description two.',
          },
        ],
        predictedClassTickets: [
          {
            ref: 'P-1',
            label: 'Predicted Team',
            similarity: 0.81,
            title: 'Predicted ticket one',
            bestSentence: 'Predicted best sentence one.',
            description: 'Predicted description one.',
          },
          {
            ref: 'P-2',
            label: 'Predicted Team',
            similarity: 0.74,
            title: 'Predicted ticket two',
            bestSentence: 'Predicted best sentence two.',
            description: 'Predicted description two.',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('Closest past tickets')
    expect(wrapper.text()).toContain('Closest predicted class tickets')
    expect(
      wrapper.findAll('[data-track-region="historical_neighbor"] .side-by-side__card'),
    ).toHaveLength(2)
    expect(
      wrapper.findAll('[data-track-region="predicted_class_neighbor"] .side-by-side__card'),
    ).toHaveLength(2)
    expect(wrapper.text()).toContain('H-1')
    expect(wrapper.text()).toContain('H-2')
    expect(wrapper.text()).toContain('P-1')
    expect(wrapper.text()).toContain('P-2')
    expect(wrapper.text()).toContain('Historical best sentence one.')
    expect(wrapper.text()).toContain('Predicted best sentence one.')
    expect(wrapper.text()).not.toContain('Historical description one.')
    expect(wrapper.text()).not.toContain('Predicted description one.')
    expect(wrapper.findAll('mark')).toHaveLength(0)
    expect(wrapper.text()).not.toContain('Current ticket')
  })

  it('expands cards independently and falls back to the first description sentence', async () => {
    const wrapper = mount(SideBySideExplanation, {
      props: {
        historicalTickets: [
          {
            ref: 'H-1',
            title: 'Historical ticket',
            description: 'Fallback sentence. Second sentence.',
          },
          {
            ref: 'H-2',
            title: 'Another historical ticket',
            description: 'Another first sentence. Another second sentence.',
          },
        ],
        predictedClassTickets: [
          {
            ref: 'P-1',
            title: 'Predicted ticket',
            description: 'Predicted first sentence. Predicted second sentence.',
          },
        ],
      },
    })

    const historicalCards = wrapper.findAll(
      '[data-track-region="historical_neighbor"] .side-by-side__card',
    )
    const predictedCard = wrapper.find(
      '[data-track-region="predicted_class_neighbor"] .side-by-side__card',
    )

    expect(historicalCards[0]?.text()).toContain('Fallback sentence.')
    expect(historicalCards[0]?.text()).not.toContain('Second sentence.')
    await historicalCards[0]?.trigger('click')
    expect(historicalCards[0]?.text()).toContain('Second sentence.')
    expect(historicalCards[1]?.text()).not.toContain('Another second sentence.')
    expect(predictedCard.text()).not.toContain('Predicted second sentence.')
    await predictedCard.trigger('click')
    expect(predictedCard.text()).toContain('Predicted second sentence.')
    expect(historicalCards[0]?.text()).toContain('Second sentence.')
  })

  it('keeps missing neighbor roles independent', () => {
    const wrapper = mount(SideBySideExplanation, {
      props: {
        historicalTickets: [],
        predictedClassTickets: [{ ref: 'P-1', title: 'Predicted ticket' }],
      },
    })

    expect(wrapper.text()).toContain('No historical tickets found.')
    expect(wrapper.text()).not.toContain('No predicted class tickets found.')
    expect(wrapper.text()).toContain('Predicted ticket')
  })

  it('marks tickets that appear in both neighbor lists', () => {
    const wrapper = mount(SideBySideExplanation, {
      props: {
        historicalTickets: [{ ref: 'D-1', title: 'Duplicate ticket' }],
        predictedClassTickets: [{ ref: 'D-1', title: 'Duplicate ticket' }],
      },
    })

    expect(wrapper.text()).toContain(
      'A ticket may appear in both lists when it is relevant by both criteria.',
    )
    expect(wrapper.findAll('.side-by-side__card--cross-listed')).toHaveLength(2)
    expect(wrapper.text()).toContain('Also closest predicted ticket')
    expect(wrapper.text()).toContain('Also closest past ticket')
    expect(wrapper.findAll('.side-by-side__ref-badge--cross-listed')).toHaveLength(2)
  })

  it('does not render empty reference badges and gives pairs distinct colors', () => {
    const wrapper = mount(SideBySideExplanation, {
      props: {
        historicalTickets: [
          { ref: 'D-1', title: 'First pair' },
          { ref: 'D-2', title: 'Second pair' },
        ],
        predictedClassTickets: [
          { ref: 'D-1', title: 'First pair' },
          { ref: 'D-2', title: 'Second pair' },
          { ref: '   ', title: 'No reference' },
        ],
      },
    })

    expect(wrapper.findAll('.side-by-side__card--cross-listed-info')).toHaveLength(2)
    expect(wrapper.findAll('.side-by-side__card--cross-listed-success')).toHaveLength(2)
    expect(wrapper.findAll('.side-by-side__ref-badge')).toHaveLength(4)
    expect(wrapper.findAll('.side-by-side__ref-badge').some((badge) => badge.text() === '')).toBe(
      false,
    )
  })
})
