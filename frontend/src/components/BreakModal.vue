<script setup lang="ts">
import Button from '@/components/ui/Button.vue'
import { Coffee, RefreshCw, X } from 'lucide-vue-next'

defineProps<{ open: boolean }>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'resume'): void
}>()

function close() {
  emit('update:open', false)
}

function resume() {
  emit('update:open', false)
  emit('resume')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="break-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="break-modal-title"
      @click.self="close"
    >
      <div class="break-modal__panel">
        <button
          type="button"
          class="break-modal__close"
          aria-label="Close"
          @click="close"
        >
          <X :size="18" />
        </button>
        <div class="break-modal__icon">
          <Coffee :size="36" />
        </div>
        <h2 id="break-modal-title" class="break-modal__title">Time for a break</h2>
        <p class="break-modal__body">
          We've saved your spot. Step away, grab a coffee, and come back when you're ready —
          labeling quality matters more than speed.
        </p>
        <div class="break-modal__actions">
          <Button variant="ghost" @click="close">Stay here</Button>
          <Button variant="default" @click="resume">
            <RefreshCw :size="16" />
            I'm back — next ticket
          </Button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped lang="scss">
.break-modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(4px);
  animation: break-modal-fade 0.15s ease-out;

  &__panel {
    position: relative;
    width: 100%;
    max-width: 28rem;
    padding: 2rem 1.75rem 1.5rem;
    background-color: var(--card);
    color: var(--card-foreground);
    border: 1px solid var(--border);
    border-radius: calc(var(--radius) + 0.25rem);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    text-align: center;
  }

  &__close {
    position: absolute;
    top: 0.625rem;
    right: 0.625rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    padding: 0;
    background: transparent;
    border: none;
    border-radius: var(--radius);
    color: var(--muted-foreground);
    cursor: pointer;
    transition: background-color 0.15s ease, color 0.15s ease;

    &:hover {
      background-color: var(--muted);
      color: var(--foreground);
    }
  }

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3.5rem;
    height: 3.5rem;
    margin: 0 auto 0.75rem;
    border-radius: 9999px;
    background-color: var(--muted);
    color: var(--primary);
  }

  &__title {
    margin: 0 0 0.5rem;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--foreground);
  }

  &__body {
    margin: 0 0 1.5rem;
    font-size: 0.9375rem;
    line-height: 1.5;
    color: var(--muted-foreground);
  }

  &__actions {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.625rem;
    flex-wrap: wrap;
  }
}

@keyframes break-modal-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
