import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiService } from '../services/api'

describe('apiService.inferTopK', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sorts all predict_proba classes and returns the top two', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          classes: ['Network Team', 'Help Desk L1', 'Security'],
          probabilities: [[0.14, 0.82, 0.04]],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await expect(apiService.inferTopK(7, { title_anon: 'VPN issue' }, 2)).resolves.toEqual({
      predictions: [
        { label: 'Help Desk L1', probability: 0.82 },
        { label: 'Network Team', probability: 0.14 },
      ],
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/activelearning/7/infer_proba',
      expect.objectContaining({ method: 'POST' }),
    )
  })
})
