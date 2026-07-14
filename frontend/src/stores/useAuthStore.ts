import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { apiService, setAuthToken, getAuthToken } from '@/services/api'
import type { LoginRequest, UserRegisterRequest, UserResponse } from '@/types/api'

const USER_STORAGE_KEY = 'humal-auth-user'

/**
 * Authentication state for the HumAL backend (JWT).
 *
 * The JWT itself is owned by the API service layer (module-level + localStorage)
 * so every request is authenticated automatically; this store mirrors the
 * token presence and the current user identity for the UI / route guard.
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getAuthToken())

  const savedUser = typeof localStorage !== 'undefined' ? localStorage.getItem(USER_STORAGE_KEY) : null
  const user = ref<UserResponse | null>(savedUser ? (JSON.parse(savedUser) as UserResponse) : null)

  const isAuthenticated = computed(() => !!token.value)

  function persistUser(next: UserResponse | null) {
    user.value = next
    if (typeof localStorage === 'undefined') return
    if (next) {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(next))
    } else {
      localStorage.removeItem(USER_STORAGE_KEY)
    }
  }

  function setToken(next: string | null) {
    token.value = next
    setAuthToken(next)
  }

  /** Authenticate and store the JWT. Resolves once the token is set. */
  async function login(credentials: LoginRequest): Promise<void> {
    const res = await apiService.login(credentials)
    setToken(res.access_token)
    // Best-effort: resolve identity; failure must not block login.
    try {
      persistUser(await apiService.getMe())
    } catch {
      persistUser({ user_id: '', username: credentials.username })
    }
  }

  /** Register a new user (does not log in automatically). */
  async function register(credentials: UserRegisterRequest): Promise<UserResponse> {
    return apiService.register(credentials)
  }

  /** Register then immediately log in. */
  async function registerAndLogin(credentials: UserRegisterRequest): Promise<void> {
    await register(credentials)
    await login(credentials)
  }

  function logout() {
    setToken(null)
    persistUser(null)
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    registerAndLogin,
    logout,
  }
})
