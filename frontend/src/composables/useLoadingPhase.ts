import { ref, computed } from 'vue'

export type LoadingPhase =
  | 'idle'
  | 'analyzing'
  | 'classifying'
  | 'generating'
  | 'retrieving'
  | 'complete'

export interface PhaseProgress {
  phase: LoadingPhase
  elapsedMs: number
  estimatedRemainingMs: number | null
}

const PHASE_SEQUENCE: LoadingPhase[] = [
  'idle',
  'analyzing',
  'classifying',
  'generating',
  'retrieving',
  'complete',
]

// Estimated durations per phase in milliseconds (tunable)
const PHASE_DURATION_MS: Record<LoadingPhase, number> = {
  idle: 0,
  analyzing: 2000,
  classifying: 1500,
  generating: 3000,
  retrieving: 1000,
  complete: 0,
}

export function useLoadingPhase() {
  const currentPhase = ref<LoadingPhase>('idle')
  const phaseTimestamps = ref<Record<LoadingPhase, number | null>>({
    idle: null,
    analyzing: null,
    classifying: null,
    generating: null,
    retrieving: null,
    complete: null,
  })

  const isLoading = computed(
    () => currentPhase.value !== 'idle' && currentPhase.value !== 'complete'
  )

  const startPhase = (phase: LoadingPhase): void => {
    currentPhase.value = phase
    phaseTimestamps.value[phase] = Date.now()
  }

  const completePhase = (): void => {
    const currentIndex = PHASE_SEQUENCE.indexOf(currentPhase.value)
    if (currentIndex >= 0 && currentIndex < PHASE_SEQUENCE.length - 1) {
      const nextPhase = PHASE_SEQUENCE[currentIndex + 1]
      if (nextPhase) {
        startPhase(nextPhase)
      }
    }
  }

  const reset = (): void => {
    currentPhase.value = 'idle'
    Object.keys(phaseTimestamps.value).forEach((phase) => {
      phaseTimestamps.value[phase as LoadingPhase] = null
    })
  }

  const getPhaseProgress = (): PhaseProgress => {
    const phase = currentPhase.value
    const timestamp = phaseTimestamps.value[phase]
    const elapsedMs = timestamp ? Date.now() - timestamp : 0
    const estimatedRemainingMs =
      phase === 'idle' || phase === 'complete'
        ? null
        : Math.max(0, PHASE_DURATION_MS[phase] - elapsedMs)

    return {
      phase,
      elapsedMs,
      estimatedRemainingMs,
    }
  }

  return {
    currentPhase,
    isLoading,
    phaseTimestamps,
    startPhase,
    completePhase,
    reset,
    getPhaseProgress,
  }
}
