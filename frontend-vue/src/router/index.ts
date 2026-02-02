import { createRouter, createWebHistory } from 'vue-router'
import type { Component } from 'vue'
import {
  Home,
  BookOpen,
  Send,
  CheckCircle2,
  Brain,
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
    meta: { label: 'Training', icon: BookOpen, showInNav: true }
  },
  {
    path: '/dispatching',
    name: 'dispatching',
    component: () => import('../pages/Dispatching.vue'),
    meta: { label: 'Dispatching', icon: Send, showInNav: true }
  },
  {
    path: '/ticket-resolution',
    name: 'ticket-resolution',
    component: () => import('../pages/TicketResolution.vue'),
    meta: { label: 'Ticket Resolution', icon: CheckCircle2, showInNav: true }
  },
  {
    path: '/inference',
    name: 'inference',
    component: () => import('../pages/Inference.vue'),
    meta: { label: 'Inference', icon: Brain, showInNav: true }
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
