import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'

import App from './App.vue'
import router from './router'
import { queryClient } from './lib/queryClient'
import { setUnauthorizedHandler } from './services/api'
import { useAuthStore } from './stores/useAuthStore'

import './assets/styles/index.scss'

// Restore deep links that arrived through the GitHub Pages 404.html shim:
// the shim rewrites /HumAL/<route> to /HumAL/?/<route>.
const shimRoute = (() => {
  if (typeof window === 'undefined') return null
  if (!window.location.search.startsWith('?/')) return null
  const decoded = window.location.search
    .slice(1)
    .split('&')
    .map(s => s.replace(/~and~/g, '&'))
    .join('?')
  window.history.replaceState(null, '', window.location.pathname + window.location.hash)
  return decoded
})()

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(VueQueryPlugin, { queryClient })

// Navigate to the restored deep link once the initial navigation is done.
if (shimRoute) {
  void router.isReady().then(() => router.replace(shimRoute))
}

// On any 401 from the API, drop the (now invalid) token and route to login,
// preserving the current location so the user returns after re-authenticating.
setUnauthorizedHandler(() => {
  const authStore = useAuthStore(pinia)
  if (!authStore.isAuthenticated) return
  authStore.logout()
  const current = router.currentRoute.value
  if (current.name !== 'login') {
    void router.replace({ name: 'login', query: { redirect: current.fullPath } })
  }
})

app.mount('#app')
