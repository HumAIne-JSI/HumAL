<script setup lang="ts">
/**
 * LabelingInsights.vue
 *
 * Mocked context panel shown next to a ticket the user is about to label.
 * Surfaces the five insights agreed for the demo iteration:
 *   (a) top-2 predicted classes with probabilities
 *   (b) LIME-style feature explanation per predicted class
 *   (c) features that distinguish the two predicted classes
 *       (i.e. those appearing in (b) for only one of them)
 *   (d) two already-classified samples (from different classes) most similar
 *       to the current item, with the snippets that make them similar
 *   (e) top-2 most similar items from the labeling history (and the label
 *       chosen at that time) to provide the prior decision context
 *
 * All values are mocked deterministically from the ticket text + queryIndex
 * so the panel is stable across re-renders within a session and obviously
 * fake for the design review.
 */
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'
import {
  Sparkles,
  Lightbulb,
  GitCompareArrows,
  Users,
  History,
} from 'lucide-vue-next'
import type { Ticket } from '@/types/api'

interface Props {
  ticket: Ticket
  queryIndex: string
  classList: string[]
  /**
   * Optional pre-labeled history items. Each entry mimics what a previous
   * labeling round produced. When empty the component falls back to a
   * built-in mock history derived from the available classes.
   */
  history?: Array<{
    ref: string
    title: string
    description?: string
    label: string
    similarity?: number
  }>
}

const props = withDefaults(defineProps<Props>(), {
  history: () => [],
})

// ---------------------------------------------------------------------------
// Deterministic pseudo-random helpers (seeded from the ticket ref / index)
// so the same ticket always shows the same mock insights.
// ---------------------------------------------------------------------------
function hashString(input: string): number {
  let h = 2166136261 >>> 0
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i)
    h = Math.imul(h, 16777619) >>> 0
  }
  return h >>> 0
}

function mulberry32(seed: number) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const seed = computed(() =>
  hashString(`${props.queryIndex}|${props.ticket.Ref ?? ''}|${props.ticket.Title_anon ?? ''}`),
)

// Stop-words and tokenizer so we can pull "feature words" from the ticket.
const STOP_WORDS = new Set([
  'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'has', 'are',
  'was', 'were', 'but', 'not', 'can', 'cannot', 'all', 'any', 'will', 'when',
  'where', 'what', 'which', 'into', 'about', 'been', 'because', 'just',
  'only', 'over', 'under', 'after', 'before', 'while', 'still', 'also',
  'their', 'there', 'they', 'them', 'then', 'than', 'these', 'those',
  'your', 'yours', 'mine', 'ours', 'his', 'her', 'its', 'our', 'one', 'two',
  'some', 'such', 'very', 'much', 'many', 'most', 'more', 'less', 'each',
  'every', 'other', 'another', 'who', 'whom', 'how', 'why', 'too', 'now',
  'tried', 'using', 'use', 'get', 'got', 'see', 'seen', 'make', 'made',
  'need', 'needs', 'needed', 'please', 'thanks', 'thank',
])

function tokenize(text: string): string[] {
  if (!text) return []
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s\-]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length >= 4 && !STOP_WORDS.has(w))
}

const ticketWords = computed(() => {
  const text = `${props.ticket.Title_anon ?? ''} ${props.ticket.Description_anon ?? ''}`
  const seen = new Set<string>()
  const out: string[] = []
  for (const w of tokenize(text)) {
    if (!seen.has(w)) {
      seen.add(w)
      out.push(w)
    }
  }
  return out
})

// ---------------------------------------------------------------------------
// (a) Top-2 predicted classes with probability
// ---------------------------------------------------------------------------
const topPredictions = computed(() => {
  const rng = mulberry32(seed.value)
  const classes = props.classList.length >= 2
    ? props.classList
    : ['Class A', 'Class B', 'Class C']
  const i1 = Math.floor(rng() * classes.length)
  let i2 = Math.floor(rng() * classes.length)
  if (i2 === i1) i2 = (i1 + 1) % classes.length
  const p1 = 0.45 + rng() * 0.4
  const remaining = 1 - p1
  const p2 = Math.min(remaining * (0.55 + rng() * 0.35), p1 - 0.02)
  return [
    { label: classes[i1] as string, probability: Number(p1.toFixed(3)) },
    { label: classes[i2] as string, probability: Number(Math.max(0.05, p2).toFixed(3)) },
  ]
})

// ---------------------------------------------------------------------------
// (b) Per-prediction feature explanation (LIME-style)
// ---------------------------------------------------------------------------
interface FeatureWeight {
  word: string
  importance: number
}

function pickFeatures(rngSeed: number, count: number): FeatureWeight[] {
  const rng = mulberry32(rngSeed)
  const pool = ticketWords.value.length > 0
    ? ticketWords.value
    : ['ticket', 'request', 'issue', 'system', 'access', 'report']
  const shuffled = [...pool]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j] as string, shuffled[i] as string]
  }
  return shuffled.slice(0, Math.min(count, shuffled.length)).map((word, i) => {
    const sign = i >= count - 2 && rng() < 0.5 ? -1 : 1
    const magnitude = (0.85 - i * 0.1) * (0.7 + rng() * 0.3)
    return { word, importance: Number((sign * Math.max(0.05, magnitude)).toFixed(3)) }
  })
}

const featuresClassA = computed(() => pickFeatures(seed.value ^ 0xa5a5a5a5, 6))
const featuresClassB = computed(() => pickFeatures(seed.value ^ 0x5a5a5a5a, 6))

const maxAbsImportance = computed(() => {
  const all = [...featuresClassA.value, ...featuresClassB.value]
  if (all.length === 0) return 1
  return Math.max(...all.map((f) => Math.abs(f.importance)))
})

function barWidth(value: number): string {
  const pct = (Math.abs(value) / maxAbsImportance.value) * 100
  return `${Math.min(100, Math.max(4, pct))}%`
}

// ---------------------------------------------------------------------------
// (c) Distinctive features — words appearing in (b) for only one class
// ---------------------------------------------------------------------------
const distinctiveFeatures = computed(() => {
  const aWords = new Set(featuresClassA.value.map((f) => f.word))
  const bWords = new Set(featuresClassB.value.map((f) => f.word))
  const onlyA = featuresClassA.value.filter((f) => !bWords.has(f.word))
  const onlyB = featuresClassB.value.filter((f) => !aWords.has(f.word))
  return { onlyA, onlyB }
})

// ---------------------------------------------------------------------------
// (d) Two classified samples from different classes, most similar to current
// ---------------------------------------------------------------------------
const similarSamples = computed(() => {
  const rng = mulberry32(seed.value ^ 0x13572468)
  const [pred1, pred2] = topPredictions.value
  const words = ticketWords.value
  const pickSnippet = (offset: number) => {
    if (words.length === 0) return 'no overlapping terms found'
    const i = Math.floor(rng() * Math.max(1, words.length - 2))
    const slice = words.slice(i, Math.min(words.length, i + 3 + offset))
    return slice.join(' ')
  }
  const refBase = (props.ticket.Ref ?? `Q${props.queryIndex}`).toString()
  return [
    {
      ref: `${refBase}-S1`,
      label: pred1?.label ?? 'Class A',
      similarity: Number((0.78 + rng() * 0.15).toFixed(2)),
      excerpt: `…${pickSnippet(0)}…`,
      reason: `Shares the terms "${pickSnippet(1)}" with the current ticket.`,
    },
    {
      ref: `${refBase}-S2`,
      label: pred2?.label ?? 'Class B',
      similarity: Number((0.65 + rng() * 0.15).toFixed(2)),
      excerpt: `…${pickSnippet(1)}…`,
      reason: `Same context "${pickSnippet(0)}" but resolved into the second-best class.`,
    },
  ]
})

// ---------------------------------------------------------------------------
// (e) Top-2 from labeling history most similar to current
// ---------------------------------------------------------------------------
const historyMatches = computed(() => {
  const rng = mulberry32(seed.value ^ 0x24681357)
  if (props.history.length > 0) {
    return [...props.history]
      .map((h) => ({ ...h, similarity: h.similarity ?? Number((0.5 + rng() * 0.4).toFixed(2)) }))
      .sort((a, b) => (b.similarity ?? 0) - (a.similarity ?? 0))
      .slice(0, 2)
  }
  const classes = props.classList.length >= 2 ? props.classList : ['Class A', 'Class B']
  const words = ticketWords.value
  const snippet = (off: number) => {
    if (words.length === 0) return 'previous ticket text'
    const i = Math.floor(rng() * Math.max(1, words.length - 2))
    return words.slice(i, Math.min(words.length, i + 3 + off)).join(' ')
  }
  const cls1 = classes[Math.floor(rng() * classes.length)] as string
  let cls2 = classes[Math.floor(rng() * classes.length)] as string
  if (cls2 === cls1 && classes.length > 1) {
    cls2 = classes[(classes.indexOf(cls1) + 1) % classes.length] as string
  }
  return [
    {
      ref: `H-${(seed.value % 9000) + 1000}`,
      title: `Earlier ticket about ${snippet(1)}`,
      description: `Similar wording around "${snippet(0)}". Resolved by labeling as ${cls1}.`,
      label: cls1,
      similarity: Number((0.74 + rng() * 0.15).toFixed(2)),
    },
    {
      ref: `H-${(seed.value % 9000) + 1500}`,
      title: `Earlier ticket about ${snippet(2)}`,
      description: `Closely related summary "${snippet(1)}". Resolved by labeling as ${cls2}.`,
      label: cls2,
      similarity: Number((0.62 + rng() * 0.15).toFixed(2)),
    },
  ]
})

const pct = (value: number) => `${(value * 100).toFixed(1)}%`
</script>

<template>
  <div class="li">
    <div class="li__banner">
      <Sparkles :size="14" />
      <span>Labeling context (mocked preview)</span>
    </div>

    <!-- (a) Top 2 predictions ------------------------------------------- -->
    <section class="li__section">
      <h5 class="li__heading">
        <Lightbulb :size="14" />
        Top predicted classes
      </h5>
      <div class="li__predictions">
        <div
          v-for="(p, i) in topPredictions"
          :key="p.label + i"
          class="li__pred"
          :class="{ 'li__pred--primary': i === 0 }"
        >
          <div class="li__pred-row">
            <Badge :variant="i === 0 ? 'success' : 'info'">#{{ i + 1 }}</Badge>
            <span class="li__pred-label" :title="p.label">{{ p.label }}</span>
            <span class="li__pred-score">{{ pct(p.probability) }}</span>
          </div>
          <Progress
            :value="Math.round(p.probability * 100)"
            :max="100"
            :color="i === 0 ? 'success' : 'default'"
          />
        </div>
      </div>
    </section>

    <!-- (b) Per-prediction feature explanations ------------------------- -->
    <section class="li__section">
      <h5 class="li__heading">
        <Lightbulb :size="14" />
        Feature explanation per prediction
      </h5>
      <div class="li__explain-grid">
        <div
          v-for="(group, gi) in [
            { title: topPredictions[0]?.label, features: featuresClassA, accent: 'success' },
            { title: topPredictions[1]?.label, features: featuresClassB, accent: 'info' },
          ]"
          :key="gi"
          class="li__explain-col"
        >
          <div class="li__explain-title">
            <Badge :variant="(group.accent as 'success' | 'info')">#{{ gi + 1 }}</Badge>
            <span :title="group.title">{{ group.title }}</span>
          </div>
          <ul class="li__feature-list">
            <li
              v-for="f in group.features"
              :key="f.word"
              class="li__feature"
            >
              <span class="li__feature-word" :title="f.word">{{ f.word }}</span>
              <span class="li__feature-bar">
                <span
                  class="li__feature-fill"
                  :class="{ 'li__feature-fill--neg': f.importance < 0 }"
                  :style="{ width: barWidth(f.importance) }"
                />
              </span>
              <span
                class="li__feature-value"
                :class="{ 'li__feature-value--neg': f.importance < 0 }"
              >
                {{ f.importance.toFixed(2) }}
              </span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- (c) Distinctive features ---------------------------------------- -->
    <section class="li__section">
      <h5 class="li__heading">
        <GitCompareArrows :size="14" />
        Distinctive features
        <span class="li__heading-hint">— present for only one of the two classes</span>
      </h5>
      <div class="li__diff-grid">
        <div class="li__diff-col">
          <div class="li__diff-head">
            <Badge variant="success">Only in #1</Badge>
            <span :title="topPredictions[0]?.label">{{ topPredictions[0]?.label }}</span>
          </div>
          <div v-if="distinctiveFeatures.onlyA.length" class="li__chip-row">
            <Badge
              v-for="f in distinctiveFeatures.onlyA"
              :key="f.word"
              variant="outline"
              class="li__chip"
            >
              {{ f.word }}
              <span class="li__chip-value">{{ f.importance.toFixed(2) }}</span>
            </Badge>
          </div>
          <p v-else class="li__muted">No exclusive features (high overlap with #2).</p>
        </div>
        <div class="li__diff-col">
          <div class="li__diff-head">
            <Badge variant="info">Only in #2</Badge>
            <span :title="topPredictions[1]?.label">{{ topPredictions[1]?.label }}</span>
          </div>
          <div v-if="distinctiveFeatures.onlyB.length" class="li__chip-row">
            <Badge
              v-for="f in distinctiveFeatures.onlyB"
              :key="f.word"
              variant="outline"
              class="li__chip"
            >
              {{ f.word }}
              <span class="li__chip-value">{{ f.importance.toFixed(2) }}</span>
            </Badge>
          </div>
          <p v-else class="li__muted">No exclusive features (high overlap with #1).</p>
        </div>
      </div>
    </section>

    <!-- (d) Similar already-classified samples --------------------------- -->
    <section class="li__section">
      <h5 class="li__heading">
        <Users :size="14" />
        Similar classified samples (different classes)
      </h5>
      <div class="li__samples">
        <div
          v-for="(s, i) in similarSamples"
          :key="s.ref"
          class="li__sample"
        >
          <div class="li__sample-head">
            <Badge :variant="i === 0 ? 'success' : 'info'">#{{ i + 1 }}</Badge>
            <span class="li__sample-ref">{{ s.ref }}</span>
            <Badge variant="secondary" class="li__sample-label">{{ s.label }}</Badge>
            <span class="li__sample-sim">sim {{ pct(s.similarity) }}</span>
          </div>
          <p class="li__sample-excerpt">{{ s.excerpt }}</p>
          <p class="li__sample-reason">{{ s.reason }}</p>
        </div>
      </div>
    </section>

    <!-- (e) Most similar items from labeling history -------------------- -->
    <section class="li__section">
      <h5 class="li__heading">
        <History :size="14" />
        Most similar from labeling history
      </h5>
      <div class="li__history">
        <div
          v-for="(h, i) in historyMatches"
          :key="h.ref"
          class="li__history-item"
        >
          <div class="li__sample-head">
            <Badge variant="outline">#{{ i + 1 }}</Badge>
            <span class="li__sample-ref">{{ h.ref }}</span>
            <Badge variant="secondary" class="li__sample-label">labeled: {{ h.label }}</Badge>
            <span v-if="h.similarity !== undefined" class="li__sample-sim">
              sim {{ pct(h.similarity) }}
            </span>
          </div>
          <p v-if="h.title" class="li__sample-title">{{ h.title }}</p>
          <p v-if="h.description" class="li__sample-reason">{{ h.description }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.li {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding: 0.75rem 0.85rem;
  margin-top: 0.5rem;
  background: color-mix(in srgb, var(--muted) 60%, transparent);
  border: 1px dashed var(--border);
  border-radius: var(--radius);

  &__banner {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    align-self: flex-start;
    padding: 0.2rem 0.55rem;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted-foreground);
    background: var(--card);
    border-radius: 999px;
    border: 1px solid var(--border);
  }

  &__section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__heading {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin: 0;
    font-size: 0.825rem;
    font-weight: 600;
    color: var(--foreground);

    svg {
      color: var(--muted-foreground);
    }
  }

  &__heading-hint {
    font-weight: 400;
    color: var(--muted-foreground);
  }

  &__predictions {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  &__pred {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__pred-row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
  }

  &__pred-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 500;
  }

  &__pred-score {
    font-variant-numeric: tabular-nums;
    font-weight: 600;
  }

  &__explain-grid,
  &__diff-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;

    @media (max-width: 720px) {
      grid-template-columns: 1fr;
    }
  }

  &__explain-col,
  &__diff-col {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.5rem 0.6rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }

  &__explain-title,
  &__diff-head {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    font-weight: 600;
    overflow: hidden;

    span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  &__feature-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__feature {
    display: grid;
    grid-template-columns: 110px 1fr 48px;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
  }

  &__feature-word {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__feature-bar {
    height: 6px;
    background: var(--muted);
    border-radius: 3px;
    overflow: hidden;
  }

  &__feature-fill {
    display: block;
    height: 100%;
    background: var(--primary);
    border-radius: 3px;

    &--neg {
      background: var(--destructive);
    }
  }

  &__feature-value {
    text-align: right;
    font-family: monospace;
    color: var(--primary);

    &--neg {
      color: var(--destructive);
    }
  }

  &__chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  &__chip {
    font-size: 0.75rem;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
  }

  &__chip-value {
    font-family: monospace;
    color: var(--muted-foreground);
  }

  &__muted {
    margin: 0;
    font-size: 0.8rem;
    color: var(--muted-foreground);
  }

  &__samples,
  &__history {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__sample,
  &__history-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.5rem 0.6rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }

  &__sample-head {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.4rem;
    font-size: 0.8rem;
  }

  &__sample-ref {
    font-family: monospace;
    color: var(--muted-foreground);
  }

  &__sample-label {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__sample-sim {
    margin-left: auto;
    font-variant-numeric: tabular-nums;
    font-size: 0.78rem;
    color: var(--muted-foreground);
  }

  &__sample-title {
    margin: 0;
    font-size: 0.85rem;
    font-weight: 500;
  }

  &__sample-excerpt {
    margin: 0;
    font-size: 0.82rem;
    font-style: italic;
    color: var(--foreground);
  }

  &__sample-reason {
    margin: 0;
    font-size: 0.78rem;
    color: var(--muted-foreground);
  }
}
</style>
