import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'humal-experiment-timer'
type SavedTimer = { selectedMinutes: number; endsAt: number | null; pausedSeconds: number; isRunning: boolean }

export const useExperimentTimerStore = defineStore('experimentTimer', () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  let initial: Partial<SavedTimer> = {}
  try { initial = saved ? JSON.parse(saved) : {} } catch { initial = {} }

  const selectedMinutes = ref<number | null>(initial.selectedMinutes ?? null)
  const endsAt = ref<number | null>(initial.endsAt ?? null)
  const pausedSeconds = ref(initial.pausedSeconds ?? 0)
  const isRunning = ref(Boolean(initial.isRunning && initial.endsAt))
  const now = ref(Date.now())

  const remainingSeconds = computed(() => {
    if (!selectedMinutes.value) return 0
    if (isRunning.value && endsAt.value) return Math.max(0, Math.ceil((endsAt.value - now.value) / 1000))
    return pausedSeconds.value
  })

  const intervalId = setInterval(() => {
    now.value = Date.now()
    if (isRunning.value && remainingSeconds.value === 0) {
      isRunning.value = false
      endsAt.value = null
      pausedSeconds.value = 0
    }
  }, 250)

  watch([selectedMinutes, endsAt, pausedSeconds, isRunning], () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ selectedMinutes: selectedMinutes.value, endsAt: endsAt.value, pausedSeconds: pausedSeconds.value, isRunning: isRunning.value }))
  }, { deep: true })

  function selectDuration(minutes: number) {
    selectedMinutes.value = minutes
    pausedSeconds.value = minutes * 60
    endsAt.value = Date.now() + pausedSeconds.value * 1000
    isRunning.value = true
  }
  function reset() { selectedMinutes.value = null; endsAt.value = null; pausedSeconds.value = 0; isRunning.value = false }

  return { selectedMinutes, isRunning, remainingSeconds, selectDuration, reset, dispose: () => clearInterval(intervalId) }
})
