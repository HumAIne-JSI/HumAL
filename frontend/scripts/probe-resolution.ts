/**
 * Standalone response-shape probe for the external Resolution Task API
 * (`al-fr-api`). The published OpenAPI declares every response as a bare
 * `object` with no properties, so the real JSON shapes have to be discovered
 * against the live server before we can type the frontend data layer.
 *
 * It exercises the read-only endpoints by default and prints the raw JSON
 * (with long strings/arrays truncated) plus a top-level key summary for each.
 * Write endpoints (`/feedback`, `/save_ticket`) mutate the knowledge base /
 * feedback DB and are only called when `--write` is passed.
 *
 * Run (Node >= 23, which strips TS types natively):
 *   node scripts/probe-resolution.ts
 *   node scripts/probe-resolution.ts --url https://al-fr-api.humaine-horizon.eu
 *   node scripts/probe-resolution.ts --write   # also probes /feedback + /save_ticket
 *
 * The base URL is resolved from (in order): --url arg,
 * VITE_RESOLUTION_API_BASE_URL env, then the deployed default.
 */

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
function resolveBaseUrl(): string {
  const argIdx = process.argv.indexOf('--url')
  if (argIdx !== -1 && process.argv[argIdx + 1]) return process.argv[argIdx + 1]!
  if (process.env.VITE_RESOLUTION_API_BASE_URL) return process.env.VITE_RESOLUTION_API_BASE_URL
  return 'https://al-fr-api.humaine-horizon.eu'
}

const BASE_URL = resolveBaseUrl().replace(/\/+$/, '')
// `--write` probes /feedback (harmless: adds a feedback row for a real id).
// `--write-kb` additionally probes /save_ticket (mutates the knowledge-base CSV).
const ALLOW_WRITE = process.argv.includes('--write') || process.argv.includes('--write-kb')
const ALLOW_WRITE_KB = process.argv.includes('--write-kb')

// A representative ticket used across the retrieval/generation probes.
const SAMPLE = {
  title: 'VPN connection keeps dropping every few minutes',
  description:
    'Since this morning my corporate VPN disconnects roughly every 5 minutes. ' +
    'Reconnecting works but it drops again shortly after. Windows 11, latest client.',
  top_k: 3,
}

// ---------------------------------------------------------------------------
// Low-level request helper
// ---------------------------------------------------------------------------
interface ReqOptions {
  method?: string
  body?: unknown
  query?: Record<string, string | number | undefined>
}

interface ReqResult {
  ok: boolean
  status: number
  data: unknown
  networkError?: string
}

function buildQuery(query?: ReqOptions['query']): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined) continue
    params.append(key, String(value))
  }
  const s = params.toString()
  return s ? `?${s}` : ''
}

async function req(path: string, options: ReqOptions = {}): Promise<ReqResult> {
  const url = `${BASE_URL}${path}${buildQuery(options.query)}`
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  try {
    const response = await fetch(url, {
      method: options.method ?? 'GET',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })
    let data: unknown = null
    try {
      data = await response.json()
    } catch {
      data = null
    }
    return { ok: response.ok, status: response.status, data }
  } catch (e) {
    return { ok: false, status: 0, data: null, networkError: e instanceof Error ? e.message : String(e) }
  }
}

// ---------------------------------------------------------------------------
// Pretty printing
// ---------------------------------------------------------------------------
/** Deep-clone a value, truncating long strings and long arrays for readability. */
function truncate(value: unknown, depth = 0): unknown {
  if (typeof value === 'string') {
    return value.length > 200 ? `${value.slice(0, 200)}… (${value.length} chars)` : value
  }
  if (Array.isArray(value)) {
    const head = value.slice(0, 3).map((v) => truncate(v, depth + 1))
    if (value.length > 3) head.push(`… (+${value.length - 3} more, ${value.length} total)`)
    return head
  }
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value)) out[k] = truncate(v, depth + 1)
    return out
  }
  return value
}

function topLevelKeys(value: unknown): string {
  if (Array.isArray(value)) {
    const first = value[0]
    if (first && typeof first === 'object') return `array<${Object.keys(first).join(', ')}>[${value.length}]`
    return `array[${value.length}]`
  }
  if (value && typeof value === 'object') return Object.keys(value).join(', ')
  return typeof value
}

function report(name: string, method: string, path: string, r: ReqResult): ReqResult {
  const line = '─'.repeat(72)
  console.log(`\n${line}`)
  console.log(`▶ ${name}  [${method} ${path}]  → ${r.networkError ? 'NETWORK ERROR' : r.status}`)
  if (r.networkError) {
    console.log(`  ✖ ${r.networkError}`)
    console.log('  (likely CORS/DNS/unreachable — note this for the direct-call approach)')
    return r
  }
  console.log(`  keys: ${topLevelKeys(r.data)}`)
  console.log(JSON.stringify(truncate(r.data), null, 2))
  return r
}

/** Best-effort scan for id-like fields (needed to type /feedback + /feedback_stats). */
function findIdFields(value: unknown, prefix = ''): string[] {
  const hits: string[] = []
  const visit = (v: unknown, p: string) => {
    if (Array.isArray(v)) {
      if (v[0] && typeof v[0] === 'object') visit(v[0], `${p}[0]`)
      return
    }
    if (v && typeof v === 'object') {
      for (const [k, val] of Object.entries(v)) {
        if (/(^|_)(id|ref|uuid|idx)$/i.test(k)) hits.push(`${p ? p + '.' : ''}${k} = ${JSON.stringify(val)}`)
        visit(val, `${p ? p + '.' : ''}${k}`)
      }
    }
  }
  visit(value, prefix)
  return hits
}

// ---------------------------------------------------------------------------
// Probe flow
// ---------------------------------------------------------------------------
async function main() {
  console.log(`Resolution Task API probe → ${BASE_URL}`)
  console.log(`Write endpoints: ${ALLOW_WRITE ? 'ENABLED (--write)' : 'skipped (pass --write to include)'}`)

  // 1. Liveness / config (read-only)
  report('Health', 'GET', '/health', await req('/health'))
  report('Config', 'GET', '/config', await req('/config'))

  // 2. Retrieve similar replies
  const retrieveRes = report(
    'Retrieve',
    'POST',
    '/retrieve',
    await req('/retrieve', { method: 'POST', body: { title: SAMPLE.title, description: SAMPLE.description, top_k: SAMPLE.top_k } }),
  )
  const idHits = findIdFields(retrieveRes.data)
  console.log(`\n  id-like fields in /retrieve response:\n   ${idHits.length ? idHits.join('\n   ') : '(none found — /feedback ids may need client-side synthesis)'}`)

  // 3. Generate a proposed reply
  report(
    'Generate',
    'POST',
    '/generate',
    await req('/generate', { method: 'POST', body: { title: SAMPLE.title, description: SAMPLE.description, top_k: SAMPLE.top_k } }),
  )

  // 4. Judge (needs similar_replies — reuse whatever /retrieve returned)
  const similarReplies = Array.isArray(retrieveRes.data)
    ? retrieveRes.data
    : (retrieveRes.data as { results?: unknown[]; retrieved?: unknown[] })?.results
      ?? (retrieveRes.data as { retrieved?: unknown[] })?.retrieved
      ?? []
  report(
    'Judge',
    'POST',
    '/judge',
    await req('/judge', {
      method: 'POST',
      body: { title: SAMPLE.title, description: SAMPLE.description, similar_replies: similarReplies, top_k: SAMPLE.top_k },
    }),
  )

  // 5. Judge + Retrieve (the one-click orchestration primitive)
  report(
    'Judge & Retrieve',
    'POST',
    '/judge_and_retrieve',
    await req('/judge_and_retrieve', {
      method: 'POST',
      body: { title: SAMPLE.title, description: SAMPLE.description, similar_replies: similarReplies, top_k: SAMPLE.top_k },
    }),
  )

  // 6. Feedback stats (read-only) — try to reuse a discovered retrieved_id
  const retrievedId = idHits.find((h) => /retrieved_id|(^|\.)id /.test(h))?.split('=')[1]?.trim()?.replace(/^"|"$/g, '')
  report(
    'Feedback stats',
    'GET',
    '/feedback_stats',
    await req('/feedback_stats', { query: { retrieved_id: retrievedId ?? 'probe-unknown-id' } }),
  )

  // 7. Write endpoints (mutate KB / feedback DB) — opt-in
  if (ALLOW_WRITE) {
    report(
      'Feedback (label=1)',
      'POST',
      '/feedback',
      await req('/feedback', {
        method: 'POST',
        body: { query_id: `probe-${Date.now()}`, retrieved_id: retrievedId ?? 'probe-unknown-id', label: 1, user_id: 'probe' },
      }),
    )
    // Re-read stats so we can see how a submitted label is aggregated.
    report(
      'Feedback stats (after)',
      'GET',
      '/feedback_stats',
      await req('/feedback_stats', { query: { retrieved_id: retrievedId ?? 'probe-unknown-id' } }),
    )
  } else {
    console.log('\n(skipping /feedback — pass --write to probe it)')
  }

  if (ALLOW_WRITE_KB) {
    report(
      'Save ticket',
      'POST',
      '/save_ticket',
      await req('/save_ticket', {
        method: 'POST',
        body: { title: `[PROBE] ${SAMPLE.title}`, description: SAMPLE.description, response: 'Probe response — safe to delete.' },
      }),
    )
  } else {
    console.log('(skipping /save_ticket — pass --write-kb to probe it; it mutates the KB CSV)')
  }

  console.log(`\n${'═'.repeat(72)}`)
  console.log('Probe complete. Use the printed shapes to finalise the TypeScript types.')
}

main().catch((e) => {
  console.error('Probe crashed:', e)
  process.exit(1)
})
