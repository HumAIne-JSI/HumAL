import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { setUseMockData } from '@/composables/useMockTickets'
import { setUseSampleData } from '@/composables/api/useAnalytics'

const STORAGE_KEY = 'humal-mock-mode'

export const useMockModeStore = defineStore('mockMode', () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  const mockEnabled = ref(
    saved !== null
      ? saved === 'true'
      : import.meta.env.DEV && !import.meta.env.VITE_USE_REAL_API,
  )

  // Sync all mock flags whenever the central toggle changes
  function sync() {
    setUseMockData(mockEnabled.value)
    setUseSampleData(mockEnabled.value)
  }

  // Initial sync
  sync()

  watch(mockEnabled, () => {
    localStorage.setItem(STORAGE_KEY, String(mockEnabled.value))
    sync()
  })

  function toggle() {
    mockEnabled.value = !mockEnabled.value
  }

  function setMockMode(value: boolean) {
    mockEnabled.value = value
  }

  return { mockEnabled, toggle, setMockMode }
})
