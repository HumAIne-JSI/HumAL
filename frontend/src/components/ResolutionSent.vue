<script setup lang="ts">
import { useId } from 'vue'
import { ArrowRight, Check, Plus } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import type { LabeledTicket } from '@/stores/useLabeledTicketsStore'

defineProps<{
  team: string
  title: string
  ticketRef?: string
  response: string
  nextTicket: LabeledTicket | null
  remaining: number
}>()

const emit = defineEmits<{
  next: []
  'new-ticket': []
}>()

const headingId = useId()
</script>

<template>
  <section class="sent" :aria-labelledby="headingId">
    <span class="sent__mark" aria-hidden="true"><Check :size="22" :stroke-width="2.5" /></span>
    <h2 :id="headingId" class="sent__heading" data-stage-heading tabindex="-1">
      Sent to {{ team }}
    </h2>
    <p class="sent__ticket">
      {{ title.trim() || 'Untitled ticket' }}
      <span v-if="ticketRef" class="sent__ref">{{ ticketRef }}</span>
    </p>
    <p class="sent__note">
      The reply was saved to the knowledge base, so it can inform future suggestions.
      <template v-if="ticketRef">The ticket was removed from your queue.</template>
    </p>

    <div v-if="nextTicket" class="sent__next">
      <span class="sent__next-label">
        Next in queue · {{ remaining }} ticket{{ remaining === 1 ? '' : 's' }} left
      </span>
      <span class="sent__next-title">
        <span class="sent__ref">{{ nextTicket.ref }}</span>
        {{ nextTicket.title || 'Untitled ticket' }}
      </span>
    </div>

    <div class="sent__actions">
      <Button v-if="nextTicket" type="button" @click="emit('next')">
        Resolve next queued ticket
        <ArrowRight :size="16" />
      </Button>
      <Button
        :variant="nextTicket ? 'outline' : 'default'"
        type="button"
        @click="emit('new-ticket')"
      >
        <Plus :size="16" />
        New ticket
      </Button>
    </div>

    <details class="sent__reply">
      <summary>Show the reply that was sent</summary>
      <p>{{ response }}</p>
    </details>
  </section>
</template>

<style scoped lang="scss">
.sent {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  max-width: 38rem;
  margin: 0 auto;
  padding: 2.5rem 2rem 2rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
  text-align: center;
}

.sent__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  background: var(--success-muted);
  color: var(--success-muted-foreground);
}

.sent__heading {
  margin: 0.25rem 0 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.015em;

  &:focus {
    outline: none;
  }
}

.sent__ticket {
  margin: 0;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.sent__ref {
  margin-left: 0.25rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8125rem;
  color: var(--muted-foreground);

  .sent__next-title & {
    margin: 0 0.375rem 0 0;
  }
}

.sent__note {
  max-width: 30rem;
  margin: 0;
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.sent__next {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  box-sizing: border-box;
  width: 100%;
  margin-top: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: var(--radius);
  background: var(--muted);
  text-align: left;
}

.sent__next-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted-foreground);
}

.sent__next-title {
  font-size: 0.9375rem;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.sent__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.sent__reply {
  width: 100%;
  margin-top: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  text-align: left;

  summary {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--muted-foreground);
    cursor: pointer;

    &:hover {
      color: var(--foreground);
    }
  }

  p {
    margin: 0.75rem 0 0;
    font-size: 0.875rem;
    line-height: 1.6;
    white-space: pre-line;
  }
}

@media (max-width: 640px) {
  .sent {
    padding: 2rem 1.125rem 1.5rem;
  }

  .sent__actions {
    flex-direction: column;
    width: 100%;
  }
}
</style>
