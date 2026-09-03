import { computed, ref } from 'vue'
import type { LabelerFeedbackType } from '@/types/api'

export type LabelerFlagFeedback = Exclude<LabelerFeedbackType, 'I_DONT_KNOW'>

/**
 * Holds satisfaction flags until the current ticket receives a decision.
 * The flags are intentionally client-side only until label-with-info submits
 * the label or an I-don't-know retirement.
 */
export function usePendingLabelerFeedback() {
  const isTired = ref(false)
  const isDifficult = ref(false)

  function toggle(type: LabelerFlagFeedback): void {
    if (type === 'I_AM_TIRED') {
      isTired.value = !isTired.value
    } else {
      isDifficult.value = !isDifficult.value
    }
  }

  function reset(): void {
    isTired.value = false
    isDifficult.value = false
  }

  const hasPendingFeedback = computed(() => isTired.value || isDifficult.value)

  return {
    isTired,
    isDifficult,
    hasPendingFeedback,
    toggle,
    reset,
  }
}
