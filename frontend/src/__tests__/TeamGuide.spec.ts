import { afterEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { enableAutoUnmount, mount } from '@vue/test-utils'
import TeamGuide from '../components/TeamGuide.vue'

enableAutoUnmount(afterEach)

describe('TeamGuide', () => {
  it('shows only the available teams and their descriptions', async () => {
    const wrapper = mount(TeamGuide, {
      props: {
        teams: ['(GI-UX) Network Access', '(GI-UX) Windows'],
      },
    })

    await wrapper.get('[data-testid="team-guide-trigger"]').trigger('click')

    expect(document.body.textContent).toContain('(GI-UX) Network Access')
    expect(document.body.textContent).toContain('encrypted connection')
    expect(document.body.textContent).toContain('(GI-UX) Windows')
    expect(document.body.textContent).not.toContain('(GI-UX) Salesforce')
  })

  it('searches descriptions as well as team names', async () => {
    const wrapper = mount(TeamGuide, {
      props: {
        teams: ['(GI-UX) Network Access', '(GI-UX) Windows'],
      },
    })

    await wrapper.get('[data-testid="team-guide-trigger"]').trigger('click')
    const search = document.body.querySelector<HTMLInputElement>('.team-guide__search input')
    expect(search).not.toBeNull()

    await search!.dispatchEvent(new Event('input', { bubbles: true }))
    search!.value = 'encrypted connection'
    await search!.dispatchEvent(new Event('input', { bubbles: true }))

    const guideText = document.body.querySelector('[data-testid="team-guide"]')?.textContent ?? ''
    expect(guideText).toContain('(GI-UX) Network Access')
    expect(guideText).not.toContain('(GI-UX) Windows')
  })

  it('emits the selected team without submitting a label', async () => {
    const wrapper = mount(TeamGuide, {
      props: {
        teams: ['(GI-UX) Windows'],
      },
    })

    await wrapper.get('[data-testid="team-guide-trigger"]').trigger('click')
    const useTeam = document.body.querySelector<HTMLButtonElement>('.team-guide__entry button')
    expect(useTeam).not.toBeNull()

    useTeam!.click()
    await nextTick()
    expect(wrapper.emitted('select')).toEqual([['(GI-UX) Windows']])
    expect(document.body.querySelector('[data-testid="team-guide"]')).toBeNull()
  })
})
