import { describe, expect, it } from 'vitest'
import { h } from 'vue'
import { mount } from '@vue/test-utils'
import PredictionResult from '../components/PredictionResult.vue'

describe('PredictionResult top-two choices', () => {
  const predictions = [
    { label: 'Network Team', probability: 0.82 },
    { label: 'Help Desk L1', probability: 0.14 },
    { label: 'Security', probability: 0.04 },
  ]

  it('renders only the two highest-ranked predictions and exposes actions for each', () => {
    const wrapper = mount(PredictionResult, {
      props: {
        prediction: 'Network Team',
        confidence: 0.82,
        predictions,
      },
      slots: {
        'prediction-action': ({ prediction }: { prediction: (typeof predictions)[number] }) =>
          h('button', { class: 'confirm-prediction' }, `Confirm ${prediction.label}`),
      },
    })

    expect(wrapper.text()).toContain('AI Suggestions')
    expect(wrapper.text()).toContain('Network Team')
    expect(wrapper.text()).toContain('Help Desk L1')
    expect(wrapper.text()).not.toContain('Security')
    expect(wrapper.findAll('.confirm-prediction')).toHaveLength(2)
  })
})
