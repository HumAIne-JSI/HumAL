import { createRouter, createWebHistory } from 'vue-router'
import type { Component } from 'vue'
import {
  Home,
  Brain,
  Target,
  MessageSquareText,
  Zap,
  BarChart3,
  Inbox,
  Pencil,
} from 'lucide-vue-next'

export interface NavItem {
  path: string
  label: string
  icon: Component
  /** When true, the sidebar opens this entry in a new browser tab. */
  newTab?: boolean
}

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../pages/Home.vue'),
    meta: { label: 'Home', icon: Home, showInNav: true }
  },
  {
    path: '/training',
    name: 'training',
    component: () => import('../pages/Training.vue'),
    meta: { label: 'New Project', icon: Brain, showInNav: true }
  },
    {
    path: '/queue',
    name: 'ticket-queue',
    component: () => import('../pages/TicketQueue.vue'),
    meta: { label: 'Ticket Queue', icon: Inbox, showInNav: true }
  },
  {
    path: '/manual',
    name: 'manual-queue',
    component: () => import('../pages/ManualQueue.vue'),
    meta: { label: 'Manual Queue', icon: Pencil, showInNav: true }
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: () => import('../pages/Analytics.vue'),
    meta: { label: 'Performance', icon: BarChart3, showInNav: true }
  },
  // {
  //   path: '/dispatching',
  //   name: 'dispatching',
  //   component: () => import('../pages/Dispatching.vue'),
  //   meta: { label: 'Dispatch Labeling', icon: Target, showInNav: true }
  // },
  {
    path: '/ticket-resolution',
    name: 'ticket-resolution',
    component: () => import('../pages/TicketResolution.vue'),
    meta: { label: 'Ticket Resolution', icon: MessageSquareText, showInNav: true, newTab: true, standalone: true }
  },
  // {
  //   path: '/inference',
  //   name: 'inference',
  //   component: () => import('../pages/Inference.vue'),
  //   meta: { label: 'Inference', icon: Zap, showInNav: true }
  // },
  {
    path: '/login',
    name: 'login',
    component: () => import('../pages/Login.vue'),
    meta: { label: 'Login', showInNav: false, public: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../pages/NotFound.vue'),
    meta: { showInNav: false }
  },
]

export const navItems: NavItem[] = routes
  .filter(route => route.meta?.showInNav)
  .map(route => ({
    path: route.path,
    label: route.meta.label as string,
    icon: route.meta.icon as NavItem['icon'],
    newTab: route.meta.newTab as boolean | undefined
  }))

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Auth guard: redirect unauthenticated users to /login (preserving the target).
// Public routes (e.g. the login page itself) are always allowed.
router.beforeEach(async (to) => {
  const { useAuthStore } = await import('@/stores/useAuthStore')
  const authStore = useAuthStore()
  if (to.meta?.public) {
    // Already signed in? Skip the login page.
    if (to.name === 'login' && authStore.isAuthenticated) {
      return { path: '/' }
    }
    return true
  }
  if (!authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

// Auto page-view telemetry. Records `open_page` on every navigation with the
// duration the user just spent on the previous page so the analytics
// dashboard can compute time-on-page without each page wiring it manually.
// Listener is registered inside the file rather than per-component so we
// never miss a navigation.
let prevEntryAt: number | null = null
let prevPageName: string | null = null

router.afterEach(async (to, from) => {
  const now = Date.now()
  const prevDurationS = prevEntryAt != null ? (now - prevEntryAt) / 1000 : null
  const prevName = prevPageName ?? (from?.name ? String(from.name) : null)
  const toName = to.name ? String(to.name) : to.path

  prevEntryAt = now
  prevPageName = toName

  try {
    const { useInstanceStore } = await import('@/stores/useInstanceStore')
    const { useMockModeStore } = await import('@/stores/useMockModeStore')
    const { useTelemetryStore } = await import('@/stores/useTelemetryStore')
    const instanceStore = useInstanceStore()
    const mockStore = useMockModeStore()
    const telemetryStore = useTelemetryStore()
    const instanceId = instanceStore.selectedInstanceId
    const resolvedInstanceId = instanceId > 0 ? instanceId : null

    // Unified pipeline: record page-view telemetry in BOTH mock and live mode,
    // tagged with the mode so the benchmarking suite scopes each view correctly.
    // (The humaine-al-api backend has no generic telemetry endpoint, so this
    // remains client-side; human decisions reach the backend via label-with-info.)
    telemetryStore.addEvent({
      al_instance_id: resolvedInstanceId,
      action: 'open_page',
      latency_ms: prevDurationS != null ? Math.round(prevDurationS * 1000) : null,
      payload: {
        page: toName,
        path: to.path,
        prev_page: prevName,
        prev_duration_s: prevDurationS,
        object: 'Ticket',
      },
      mock: mockStore.mockEnabled,
    })
  } catch (err) {
    // Telemetry must never break navigation.
    console.warn('[telemetry] page-view event failed', err)
  }
})

export default router
