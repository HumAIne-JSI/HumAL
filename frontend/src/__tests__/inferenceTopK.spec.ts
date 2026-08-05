import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiService } from '../services/api'

describe('apiService.inferTopK', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sorts all predict_proba classes and returns the top two (body data)', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          classes: ['Network Team', 'Help Desk L1', 'Security'],
          probabilities: [[0.14, 0.82, 0.04]],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await expect(apiService.inferTopK(7, { ticketData: { title_anon: 'VPN issue' } }, 2)).resolves.toEqual({
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

  it('sorts predict_proba classes and returns the top two (ticket refs)', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          classes: ['Network Team', 'Help Desk L1', 'Security'],
          probabilities: [[0.14, 0.82, 0.04]],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await expect(apiService.inferTopK(7, { ticketRefs: ['R-1234'] }, 2)).resolves.toEqual({
      predictions: [
        { label: 'Help Desk L1', probability: 0.82 },
        { label: 'Network Team', probability: 0.14 },
      ],
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/activelearning/7/infer_proba?query_idx=R-1234',
      expect.objectContaining({ method: 'POST', body: undefined }),
    )
  })

  it('sorts predict_proba classes and returns the top two (multiple ticket refs)', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          classes: ['Network Team', 'Help Desk L1', 'Security'],
          probabilities: [[0.14, 0.82, 0.04]],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await expect(apiService.inferTopK(7, { ticketRefs: ['R-1234', 'R-1235'] }, 2)).resolves.toEqual({
      predictions: [
        { label: 'Help Desk L1', probability: 0.82 },
        { label: 'Network Team', probability: 0.14 },
      ],
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/activelearning/7/infer_proba?query_idx=R-1234&query_idx=R-1235',
      expect.objectContaining({ method: 'POST', body: undefined }),
    )
  })
})

describe('apiService.infer', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sends ticket refs as query params with no body', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify(['Network Team']),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.infer(7, undefined, ['R-1234'])

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/activelearning/7/infer?query_idx=R-1234',
      expect.objectContaining({ method: 'POST', body: undefined }),
    )
  })

  it('sends body data when no refs provided', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify(['Network Team']),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.infer(7, { title_anon: 'VPN issue' })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/activelearning/7/infer',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ title_anon: 'VPN issue' }),
      }),
    )
  })
})

describe('apiService XAI serialization', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('explain_lime sends ticket refs as query_idx params with no body', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([{ text: '', prediction: { label: 'A', probabilities: {} }, word_weights: [], error: null }]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.explainLime(7, { query_idx: ['R-1234'], top_k: 2 })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/xai/7/explain_lime?top_k=2&query_idx=R-1234',
      expect.objectContaining({ method: 'POST', body: undefined }),
    )
  })

  it('explain_lime sends the ticket_data body when no refs are provided', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([{ text: '', prediction: { label: 'A', probabilities: {} }, word_weights: [], error: null }]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.explainLime(7, { ticket_data: { title_anon: 'VPN issue' } })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/xai/7/explain_lime',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ title_anon: 'VPN issue' }),
      }),
    )
  })

  it('getNearest sends ticket refs as repeated query_idx query params with no body', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            query_idx: 'R-1234',
            predicted_class_neighbors: [],
            historical_neighbors: [],
          },
        ]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.getNearest(7, { query_idx: ['R-1234'], top_k: 2 })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/xai/7/nearest?top_k=2&query_idx=R-1234',
      expect.objectContaining({ method: 'POST', body: undefined }),
    )
  })

  it('getNearest sends multiple query_idx params for multiple refs', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            query_idx: 'R-1234',
            predicted_class_neighbors: [],
            historical_neighbors: [],
          },
        ]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.getNearest(7, { query_idx: ['R-1234', 'R-1235'] })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/xai/7/nearest?query_idx=R-1234&query_idx=R-1235',
      expect.objectContaining({ method: 'POST', body: undefined }),
    )
  })

  it('getNearest sends the ticket_data body when no refs are provided', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            query_idx: null,
            predicted_class_neighbors: [],
            historical_neighbors: [],
          },
        ]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.getNearest(7, { ticket_data: { title_anon: 'VPN issue' }, top_k: 2 })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/xai/7/nearest?top_k=2',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ title_anon: 'VPN issue' }) }),
    )
  })

  it('getNearestTicketsPerClass sends refs as repeated query_idx params with top_k query', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            query_idx: 'R-1234',
            predicted_class_neighbors: [],
            historical_neighbors: [],
          },
        ]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await apiService.getNearestTicketsPerClass(7, {
      ticket_refs: ['R-1234'],
      class_labels: ['Team A', 'Team B'],
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/xai/7/nearest?top_k=2&query_idx=R-1234',
      expect.objectContaining({ method: 'POST', body: undefined }),
    )
  })
})
