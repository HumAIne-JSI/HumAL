import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/Home.vue')
  },
  {
    path: '/training',
    name: 'Training',
    component: () => import('@/pages/Training.vue')
  },
  {
    path: '/dispatch-labeling',
    name: 'DispatchLabeling',
    component: () => import('@/pages/DispatchLabeling.vue')
  },
  {
    path: '/ticket-resolution',
    name: 'TicketResolution',
    component: () => import('@/pages/TicketResolution.vue')
  },
  {
    path: '/inference',
    name: 'Inference',
    component: () => import('@/pages/Inference.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
