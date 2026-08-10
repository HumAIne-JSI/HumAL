import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LimeHighlightedText from '../components/LimeHighlightedText.vue'

describe('LimeHighlightedText', () => {
  it('highlights weighted words while preserving the original text', () => {
    const wrapper = mount(LimeHighlightedText, {
      props: {
        text: 'Cannot access network drive Z:',
        enabled: true,
        explanation: [
          {
            text: 'Cannot access network drive Z:',
            prediction: { label: 'Network', probabilities: {} },
            word_weights: [{ word: 'NETWORK', weight: 0.8 }, ['drive', -0.4]],
          },
        ],
      },
    })

    expect(wrapper.text()).toBe('Cannot access network drive Z:')
    expect(wrapper.findAll('mark').map((mark) => mark.text())).toEqual(['network', 'drive'])
    expect(wrapper.find('mark').attributes('title')).toBe('network: +0.800')
    expect(wrapper.findAll('mark')[1]?.attributes('title')).toBe('drive: -0.400')
    expect(wrapper.findAll('mark')[1]?.attributes('style')).toContain('var(--destructive)')
  })

  it('renders plain text when no explanation is available', () => {
    const wrapper = mount(LimeHighlightedText, {
      props: { text: 'No explanation yet.' },
    })

    expect(wrapper.text()).toBe('No explanation yet.')
    expect(wrapper.findAll('mark')).toHaveLength(0)
  })

  it('renders plain text until highlighting is enabled', () => {
    const wrapper = mount(LimeHighlightedText, {
      props: {
        text: 'Cannot access network drive Z:',
        explanation: [
          {
            text: 'Cannot access network drive Z:',
            prediction: { label: 'Network', probabilities: {} },
            word_weights: [{ word: 'network', weight: 0.8 }],
          },
        ],
      },
    })

    expect(wrapper.text()).toBe('Cannot access network drive Z:')
    expect(wrapper.findAll('mark')).toHaveLength(0)
  })
})
