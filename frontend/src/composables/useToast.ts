import { ref, computed } from 'vue'
import type { Component, VNode } from 'vue'

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

export type ToastVariant = 'default' | 'destructive'

export interface Toast {
  id: string
  title?: string
  description?: string
  action?: Component | VNode
  variant?: ToastVariant
  open?: boolean
}

type ToastInput = Omit<Toast, 'id'>

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

const toasts = ref<Toast[]>([])
const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

function addToRemoveQueue(toastId: string) {
  if (toastTimeouts.has(toastId)) {
    return
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    toasts.value = toasts.value.filter((t) => t.id !== toastId)
  }, TOAST_REMOVE_DELAY)

  toastTimeouts.set(toastId, timeout)
}

function toast(props: ToastInput) {
  const id = genId()

  const newToast: Toast = {
    ...props,
    id,
    open: true,
  }

  toasts.value = [newToast, ...toasts.value].slice(0, TOAST_LIMIT)

  return {
    id,
    dismiss: () => dismiss(id),
    update: (updateProps: Partial<Toast>) => {
      toasts.value = toasts.value.map((t) =>
        t.id === id ? { ...t, ...updateProps } : t
      )
    },
  }
}

function dismiss(toastId?: string) {
  if (toastId) {
    addToRemoveQueue(toastId)
    toasts.value = toasts.value.map((t) =>
      t.id === toastId ? { ...t, open: false } : t
    )
  } else {
    toasts.value.forEach((toast) => {
      addToRemoveQueue(toast.id)
    })
    toasts.value = toasts.value.map((t) => ({ ...t, open: false }))
  }
}

export function useToast() {
  return {
    toasts: computed(() => toasts.value),
    toast,
    dismiss,
  }
}

export { toast }
