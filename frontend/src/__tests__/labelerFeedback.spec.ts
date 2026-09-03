import { describe, expect, it } from 'vitest'
import { usePendingLabelerFeedback } from '../composables/usePendingLabelerFeedback'
import { buildQueueLabelInfo } from '../composables/api/useTicketQueue'

describe('usePendingLabelerFeedback', () => {
  it('toggles both flags independently and resets them', () => {
    const feedback = usePendingLabelerFeedback()

    feedback.toggle('I_AM_TIRED')
    feedback.toggle('DIFFICULT_TICKET')

    expect(feedback.isTired.value).toBe(true)
    expect(feedback.isDifficult.value).toBe(true)
    expect(feedback.hasPendingFeedback.value).toBe(true)

    feedback.toggle('I_AM_TIRED')

    expect(feedback.isTired.value).toBe(false)
    expect(feedback.isDifficult.value).toBe(true)

    feedback.reset()

    expect(feedback.isTired.value).toBe(false)
    expect(feedback.isDifficult.value).toBe(false)
    expect(feedback.hasPendingFeedback.value).toBe(false)
  })
})

describe('buildQueueLabelInfo', () => {
  const endMs = Date.parse('2026-08-04T12:00:05.000Z')

  it('requires a label for non-IDK decisions and includes selected flags', () => {
    const payload = buildQueueLabelInfo(
      {
        ticketId: 'T-1',
        label: 'Network',
        prediction: 'Hardware',
        secondPrediction: 'Desktop',
        durationMs: 5000,
        isTired: true,
        isDifficult: true,
      },
      endMs,
    )

    expect(payload).toMatchObject({
      ticket_id: 'T-1',
      label: 'Network',
      model_prediction: 'Hardware',
      second_model_prediction: 'Desktop',
      is_tired: true,
      is_difficult: true,
    })
    expect(payload.i_dont_know).toBeUndefined()
    expect(payload.start_time).toBe('2026-08-04T12:00:00.000Z')
    expect(payload.end_time).toBe('2026-08-04T12:00:05.000Z')
  })

  it('omits second_model_prediction when no second prediction is available', () => {
    const payload = buildQueueLabelInfo(
      {
        ticketId: 'T-1b',
        label: 'Network',
        prediction: 'Hardware',
        durationMs: 5000,
      },
      endMs,
    )

    expect(payload).toMatchObject({ ticket_id: 'T-1b', label: 'Network' })
    expect(payload.second_model_prediction).toBeUndefined()
  })

  it('omits the label and preserves flags for an IDK retirement', () => {
    const payload = buildQueueLabelInfo(
      {
        ticketId: 'T-2',
        durationMs: 2000,
        prediction: 'Hardware',
        secondPrediction: 'Desktop',
        isTired: true,
        isDifficult: true,
        iDontKnow: true,
      },
      endMs,
    )

    expect(payload).not.toHaveProperty('label')
    expect(payload).toMatchObject({
      ticket_id: 'T-2',
      model_prediction: 'Hardware',
      second_model_prediction: 'Desktop',
      is_tired: true,
      is_difficult: true,
      i_dont_know: true,
    })
  })

  it('rejects an unlabeled decision unless IDK is selected', () => {
    expect(() =>
      buildQueueLabelInfo({
        ticketId: 'T-3',
      }),
    ).toThrow('A label is required')
  })
})
