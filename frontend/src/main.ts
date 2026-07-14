import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'

import App from './App.vue'
import router from './router'
import { queryClient } from './lib/queryClient'
import { setUnauthorizedHandler } from './services/api'
import { useAuthStore } from './stores/useAuthStore'

import './assets/styles/index.scss'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(VueQueryPlugin, { queryClient })

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
