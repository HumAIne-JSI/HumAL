import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const SPECIALIST_SESSION_KEY = 'humal-specialist-session'

/**
 * Mock sign-in for the Tier 2 workspace, which behaves like a separate app.
 *
 * No credentials are verified: the session only gates the workspace UI and is
 * independent of the main app's JWT. It lives in sessionStorage so every new tab
 * starts at the sign-in page while a reload keeps the user signed in.
 */
export const useSpecialistAuthStore = defineStore('specialistAuth', () => {
  const username = ref<string | null>(sessionStorage.getItem(SPECIALIST_SESSION_KEY))
  const isAuthenticated = computed(() => !!username.value)

  function login(name: string) {
    username.value = name
    sessionStorage.setItem(SPECIALIST_SESSION_KEY, name)
  }

  function logout() {
    username.value = null
    sessionStorage.removeItem(SPECIALIST_SESSION_KEY)
  }

  return { username, isAuthenticated, login, logout }
})
