import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'humal-selected-instance'

export const useInstanceStore = defineStore('instance', () => {
  // Load initial value from localStorage
  const storedValue = localStorage.getItem(STORAGE_KEY)
  const selectedInstanceId = ref<number>(storedValue ? Number(storedValue) : 0)

  const hasSelectedInstance = computed(() => selectedInstanceId.value > 0)

  function setInstance(id: number | string) {
    const numId = typeof id === 'string' ? Number(id) : id
    selectedInstanceId.value = numId || 0
    if (numId > 0) {
      localStorage.setItem(STORAGE_KEY, String(numId))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  function clearInstance() {
    selectedInstanceId.value = 0
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    selectedInstanceId,
    hasSelectedInstance,
    setInstance,
    clearInstance,
  }
})
