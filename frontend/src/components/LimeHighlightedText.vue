<script setup lang="ts">
import { computed } from 'vue'
import type { ExplainLimeResponse } from '@/types/api'

interface Props {
  text: string
  explanation?: ExplainLimeResponse | null
  enabled?: boolean
}

interface Token {
  kind: 'word' | 'gap'
  text: string
  weight?: number
}

const props = withDefaults(defineProps<Props>(), {
  explanation: null,
  enabled: false,
})

const wordWeights = computed(() => {
  const map = new Map<string, number>()
  const entries = props.explanation?.[0]?.word_weights ?? []

  for (const entry of entries) {
    const word = Array.isArray(entry) ? entry[0] : entry.word
    const weight = Array.isArray(entry) ? entry[1] : entry.weight
    if (!word || typeof weight !== 'number') continue

    const key = word.toLowerCase()
    const existing = map.get(key)
    if (existing === undefined || Math.abs(weight) > Math.abs(existing)) {
      map.set(key, weight)
    }
  }

  return map
})

const maxAbsWeight = computed(() => {
  let max = 0
  for (const weight of wordWeights.value.values()) {
    max = Math.max(max, Math.abs(weight))
  }
  return max || 1
})

const tokens = computed((): Token[] => {
  if (!props.text) return []

  const result: Token[] = []
  const regex = /([A-Za-z0-9]+(?:'[A-Za-z0-9]+)?)/g
  let last = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(props.text)) !== null) {
    if (match.index > last) {
      result.push({ kind: 'gap', text: props.text.slice(last, match.index) })
    }

    const word = match[0]
    result.push({
      kind: 'word',
      text: word,
      weight: wordWeights.value.get(word.toLowerCase()),
    })
    last = match.index + word.length
  }

  if (last < props.text.length) {
    result.push({ kind: 'gap', text: props.text.slice(last) })
  }

  return result
})

function highlightStyle(weight: number): string {
  const intensity = Math.min(1, Math.abs(weight) / maxAbsWeight.value)
  const percentage = (4 + intensity * 18).toFixed(1)
  const color = weight >= 0 ? 'var(--primary)' : 'var(--destructive)'
  return `background-color: color-mix(in srgb, ${color} ${percentage}%, transparent); border-bottom: 2px solid ${color};`
}

function tokenTitle(token: Token): string {
  if (token.kind !== 'word' || token.weight === undefined) return ''
  return `${token.text}: ${token.weight >= 0 ? '+' : ''}${token.weight.toFixed(3)}`
}
</script>

<template>
  <span class="lime-highlighted-text">
    <template v-if="enabled">
      <template v-for="(token, index) in tokens" :key="index">
        <mark
          v-if="token.kind === 'word' && token.weight !== undefined"
          :style="highlightStyle(token.weight)"
          :title="tokenTitle(token)"
          >{{ token.text }}</mark
        >
        <template v-else>{{ token.text }}</template>
      </template>
    </template>
    <template v-else>{{ text }}</template>
  </span>
</template>

<style scoped lang="scss">
.lime-highlighted-text {
  mark {
    background: transparent;
    color: inherit;
    padding: 0 0.08em;
    border-radius: 0.15em;
    cursor: help;
  }
}
</style>
