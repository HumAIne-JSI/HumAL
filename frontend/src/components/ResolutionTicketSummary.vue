<script setup lang="ts">
import { computed, useId } from 'vue'
import { Pencil } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{
  title: string
  description: string
  ticketRef?: string
  category?: string
  subcategory?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  edit: []
}>()

const headingId = useId()

const tags = computed(() => {
  const list: string[] = []
  if (props.ticketRef) list.push(`Queue · ${props.ticketRef}`)
  if (props.category) {
    list.push(props.subcategory ? `${props.category} › ${props.subcategory}` : props.category)
  }
  return list
})
</script>

<template>
  <section class="summary" :aria-labelledby="headingId">
    <div class="summary__head">
      <h3 :id="headingId" class="summary__label">Ticket</h3>
      <Button variant="ghost" size="sm" type="button" :disabled="disabled" @click="emit('edit')">
        <Pencil :size="14" />
        Edit ticket
      </Button>
    </div>
    <p class="summary__title">{{ title.trim() || 'Untitled ticket' }}</p>
    <p v-if="description.trim()" class="summary__desc">{{ description }}</p>
    <ul v-if="tags.length" class="summary__tags">
      <li v-for="tag in tags" :key="tag" class="summary__tag">{{ tag }}</li>
    </ul>
  </section>
</template>

<style scoped lang="scss">
.summary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 1rem 1.125rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
}

.summary__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin: -0.25rem -0.375rem 0 0;
}

.summary__label {
  margin: 0;
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted-foreground);
}

.summary__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.summary__desc {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  font-size: 0.875rem;
  color: var(--muted-foreground);
  white-space: pre-line;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
}

.summary__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin: 0.25rem 0 0;
  padding: 0;
  list-style: none;
}

.summary__tag {
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  background: var(--muted);
  font-size: 0.75rem;
}
</style>
