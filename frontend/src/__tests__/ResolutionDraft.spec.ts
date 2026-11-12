import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ResolutionDraft from '../components/ResolutionDraft.vue'
import type { AssistedResolution } from '../composables/api/useResolution'

const RESULT: AssistedResolution = {
  classification: 'Access',
  predicted_class: 'Access',
  predicted_team: 'Service Desk',
  team_confidence: 0.8,
  response: 'Please re-map the drive.',
  similar_replies: [],
  retrieval_k: 5,
  judge_scores: [],
  votes_applied: 0
}

function mountDraft(saving: boolean) {
  return mount(ResolutionDraft, {
    props: {
      response: RESULT.response,
      result: RESULT,
      drafting: false,
      showProgress: false,
      phase: 'idle',
      phases: [],
      saving,
      undoReason: 'Draft replaced with a past reply.',
      error: null,
      exportData: []
    },
    global: { stubs: { ExportButton: true } }
  })
}

const buttonNamed = (wrapper: ReturnType<typeof mountDraft>, name: string) =>
  wrapper.findAll('button').find((button) => button.text().trim() === name)!

describe('ResolutionDraft', () => {
  it('locks the draft while it is being sent so the sent text cannot change', () => {
    const idle = mountDraft(false)
    expect(idle.get('textarea').attributes('disabled')).toBeUndefined()
    expect(buttonNamed(idle, 'Regenerate').attributes('disabled')).toBeUndefined()

    const sending = mountDraft(true)
    expect(sending.get('textarea').attributes('disabled')).toBeDefined()
    for (const name of ['Regenerate', 'Reassign', 'Undo']) {
      expect(buttonNamed(sending, name).attributes('disabled')).toBeDefined()
    }
  })
})
