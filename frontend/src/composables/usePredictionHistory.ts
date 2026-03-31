import { ref, watch } from 'vue'
import type { InferenceData, InferenceResponse } from '@/types/api'

export interface PredictionHistoryItem {
  id: number
  timestamp: Date
  input: InferenceData
  output: InferenceResponse
  processingTime: number
}

const STORAGE_KEY = 'humal-prediction-history'
const MAX_ITEMS = 50

// Parse stored history from localStorage
function loadFromStorage(): PredictionHistoryItem[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return []
    const parsed = JSON.parse(stored)
    // Convert timestamp strings back to Date objects
    return parsed.map((item: PredictionHistoryItem) => ({
      ...item,
      timestamp: new Date(item.timestamp),
    }))
  } catch {
    return []
  }
}

// Save history to localStorage
function saveToStorage(items: PredictionHistoryItem[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // localStorage might be full or disabled
    console.warn('Failed to save prediction history to localStorage')
  }
}

// Shared state across composable instances
const history = ref<PredictionHistoryItem[]>(loadFromStorage())

// Watch for changes and persist
watch(
  history,
  (newHistory) => {
    saveToStorage(newHistory)
  },
  { deep: true }
)

/**
 * Composable for managing prediction history with localStorage persistence.
 * 
 * @example
 * ```ts
 * const { items, add, clear, todayCount, avgProcessingTime } = usePredictionHistory()
 * 
 * // Add a new prediction
 * add({
 *   input: ticketData,
 *   output: predictionResult,
 *   processingTime: 150
 * })
 * 
 * // Clear all history
 * clear()
 * ```
 */
export function usePredictionHistory() {
  /**
   * Add a new prediction to history.
   * Automatically assigns ID and timestamp, and prunes old entries.
   */
  const add = (item: Omit<PredictionHistoryItem, 'id' | 'timestamp'>): PredictionHistoryItem => {
    const newItem: PredictionHistoryItem = {
      ...item,
      id: Date.now(),
      timestamp: new Date(),
    }
    
    // Add to front of array
    history.value = [newItem, ...history.value].slice(0, MAX_ITEMS)
    
    return newItem
  }

  /**
   * Remove a specific item from history by ID.
   */
  const remove = (id: number): void => {
    history.value = history.value.filter((item) => item.id !== id)
  }

  /**
   * Clear all prediction history.
   */
  const clear = (): void => {
    history.value = []
  }

  /**
   * Get count of predictions made today.
   */
  const todayCount = (): number => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return history.value.filter((item) => new Date(item.timestamp) >= today).length
  }

  /**
   * Get average processing time in milliseconds.
   */
  const avgProcessingTime = (): number => {
    if (history.value.length === 0) return 0
    const total = history.value.reduce((sum, item) => sum + item.processingTime, 0)
    return Math.round(total / history.value.length)
  }

  return {
    /** All prediction history items (reactive) */
    items: history,
    /** Add a new prediction to history */
    add,
    /** Remove a specific item by ID */
    remove,
    /** Clear all history */
    clear,
    /** Get count of today's predictions */
    todayCount,
    /** Get average processing time */
    avgProcessingTime,
  }
}
