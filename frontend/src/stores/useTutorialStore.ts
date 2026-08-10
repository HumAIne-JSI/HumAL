import { ref } from 'vue'
import { defineStore } from 'pinia'

export type TourSegment = 'project' | 'manualQueue' | 'ticketQueue'
export type ActiveTour = TourSegment | null

const STORAGE_KEY = 'humal-tutorial-seen'

export const useTutorialStore = defineStore('tutorial', () => {
  const introChainSeen = ref(localStorage.getItem(STORAGE_KEY) === 'true')
  const activeTour = ref<ActiveTour>(null)

  function markIntroChainSeen() {
    introChainSeen.value = true
    localStorage.setItem(STORAGE_KEY, 'true')
  }

  /** Start (or restart) the full intro chain from the project segment. */
  function runChain() {
    activeTour.value = 'project'
  }

  /** Clear the "seen" flag so the chain can be replayed. */
  function reset() {
    introChainSeen.value = false
    localStorage.removeItem(STORAGE_KEY)
  }

  return { introChainSeen, activeTour, markIntroChainSeen, runChain, reset }
})