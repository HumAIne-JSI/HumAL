<script setup lang="ts">
import { CollapsibleRoot, type CollapsibleRootEmits, type CollapsibleRootProps } from 'radix-vue'

const props = defineProps<CollapsibleRootProps>()
const emit = defineEmits<CollapsibleRootEmits>()
</script>

<template>
  <CollapsibleRoot v-bind="props" @update:open="emit('update:open', $event)">
    <slot />
  </CollapsibleRoot>
</template>
