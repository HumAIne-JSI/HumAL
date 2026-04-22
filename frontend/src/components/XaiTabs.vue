<script setup lang="ts">
import { ref } from 'vue'
import LimeExplanation from '@/components/LimeExplanation.vue'
import NearestTicket from '@/components/NearestTicket.vue'
import Progress from '@/components/ui/Progress.vue'
import type { ExplainLimeResponse, NearestTicketResponse } from '@/types/api'

defineProps<{
  explanation: ExplainLimeResponse | null
  nearestTickets: NearestTicketResponse | null
  loadingLime?: boolean
  loadingNearest?: boolean
}>()

const activeTab = ref<'keywords' | 'similar'>('keywords')
</script>

<template>
  <div class="xai-tabs">
    <div class="xai-tabs__bar">
      <button
        :class="['xai-tabs__tab', { 'xai-tabs__tab--active': activeTab === 'keywords' }]"
        @click="activeTab = 'keywords'"
      >
        Key Words
      </button>
      <button
        :class="['xai-tabs__tab', { 'xai-tabs__tab--active': activeTab === 'similar' }]"
        @click="activeTab = 'similar'"
      >
        Similar Ticket
      </button>
    </div>

    <div class="xai-tabs__content">
      <template v-if="activeTab === 'keywords'">
        <LimeExplanation
          :explanation="explanation"
          :loading="loadingLime"
          :collapsible="false"
        />
      </template>
      <template v-else>
        <NearestTicket
          :nearest-ticket="nearestTickets"
          :loading="loadingNearest"
          show-details
        />
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
.xai-tabs {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  // overflow: hidden;

  &__bar {
    display: flex;
    border-bottom: 1px solid var(--border);
    background: var(--muted);
  }

  &__tab {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border: none;
    background: transparent;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--muted-foreground);
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      color: var(--foreground);
    }

    &--active {
      background: var(--card);
      color: var(--foreground);
      font-weight: 600;
      box-shadow: inset 0 -2px 0 var(--primary);
    }
  }

  &__content {
    padding: 0.75rem;
    background: var(--card);
  }
}
</style>
