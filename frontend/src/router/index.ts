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
} from 'lucide-vue-next'

export interface NavItem {
  path: string
  label: string
  icon: Component
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
    meta: { label: 'Training', icon: Brain, showInNav: true }
  },
    {
    path: '/queue',
    name: 'ticket-queue',
    component: () => import('../pages/TicketQueue.vue'),
    meta: { label: 'Ticket Queue', icon: Inbox, showInNav: true }
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: () => import('../pages/Analytics.vue'),
    meta: { label: 'Analytics', icon: BarChart3, showInNav: true }
  },
  // {
  //   path: '/dispatching',
  //   name: 'dispatching',
  //   component: () => import('../pages/Dispatching.vue'),
  //   meta: { label: 'Dispatch Labeling', icon: Target, showInNav: true }
  // },
  // {
  //   path: '/ticket-resolution',
  //   name: 'ticket-resolution',
  //   component: () => import('../pages/TicketResolution.vue'),
  //   meta: { label: 'Ticket Resolution', icon: MessageSquareText, showInNav: true }
  // },
  // {
  //   path: '/inference',
  //   name: 'inference',
  //   component: () => import('../pages/Inference.vue'),
  //   meta: { label: 'Inference', icon: Zap, showInNav: true }
  // },
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
    label: route.meta.label,
    icon: route.meta.icon
  }))

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
