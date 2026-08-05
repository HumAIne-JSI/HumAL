/**
 * Standalone endpoint smoke-test for the HumAL backend.
 *
 * Exercises every endpoint the frontend depends on against a live server,
 * registering a throwaway user and cleaning up any AL instance it creates.
 *
 * Run (Node >= 23, which strips TS types natively):
 *   node scripts/test-api.ts
 *   node scripts/test-api.ts --url https://al-api.humaine-horizon.eu
 *
 * The base URL is resolved from (in order): --url arg, VITE_API_BASE_URL env,
 * then the deployed default.
 *
 * Exit code is 0 unless a hard failure (network error / 5xx) occurs.
 */

type Status = 'PASS' | 'WARN' | 'FAIL'

interface Result {
  name: string
  method: string
  path: string
  status: Status
  code: number | string
  detail?: string
}

const results: Result[] = []

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
function resolveBaseUrl(): string {
  const argIdx = process.argv.indexOf('--url')
  if (argIdx !== -1 && process.argv[argIdx + 1]) return process.argv[argIdx + 1]!
  if (process.env.VITE_API_BASE_URL) return process.env.VITE_API_BASE_URL
  return 'https://al-api.humaine-horizon.eu'
}

const BASE_URL = resolveBaseUrl().replace(/\/+$/, '')

// ---------------------------------------------------------------------------
// Low-level request helper
// ---------------------------------------------------------------------------
interface ReqOptions {
  method?: string
  body?: unknown
  token?: string | null
  query?: Record<string, string | string[] | number | undefined>
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
    if (Array.isArray(value)) value.forEach((v) => params.append(key, String(v)))
    else params.append(key, String(value))
  }
  const s = params.toString()
  return s ? `?${s}` : ''
}

async function req(path: string, options: ReqOptions = {}): Promise<ReqResult> {
  const url = `${BASE_URL}${path}${buildQuery(options.query)}`
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (options.token) headers['Authorization'] = `Bearer ${options.token}`

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

function detailOf(r: ReqResult): string | undefined {
  if (r.networkError) return r.networkError
  if (r.data && typeof r.data === 'object' && 'detail' in r.data) {
    const d = (r.data as { detail: unknown }).detail
    return typeof d === 'string' ? d : JSON.stringify(d)
  }
  return undefined
}

/**
 * Classify + record a call.
 *  - 2xx        -> PASS
 *  - 400/401/422 (expected client-side rejections) -> WARN
 *  - 404        -> WARN (treated as "not deployed" for optional endpoints)
 *  - 5xx / network -> FAIL
 */
function record(name: string, method: string, path: string, r: ReqResult): ReqResult {
  let status: Status
  if (r.status >= 200 && r.status < 300) status = 'PASS'
  else if (r.status === 0 || r.status >= 500) status = 'FAIL'
  else status = 'WARN'
  results.push({ name, method, path, status, code: r.status || 'ERR', detail: detailOf(r) })
  return r
}

// ---------------------------------------------------------------------------
// Test flow
// ---------------------------------------------------------------------------
function pickString(data: unknown, keys: string[]): string[] {
  if (!data || typeof data !== 'object') return []
  for (const key of keys) {
    const v = (data as Record<string, unknown>)[key]
    if (Array.isArray(v)) return v.map((x) => String(x))
  }
  // Some endpoints return a bare array.
  if (Array.isArray(data)) return (data as unknown[]).map((x) => String(x))
  return []
}

async function main() {
  const stamp = `${Date.now()}_${Math.floor(Math.random() * 1e6)}`
  const primary = { username: `smoketest_${stamp}`, password: 'Test-1234!' }
  const secondary = { username: `smoketest_${stamp}_b`, password: 'Test-1234!' }

  console.log(`\nHumAL API smoke test → ${BASE_URL}\n${'-'.repeat(60)}`)

  // --- Auth -----------------------------------------------------------------
  record('register primary user', 'POST', '/users/register',
    await req('/users/register', { method: 'POST', body: primary }))

  const loginRes = record('login primary user', 'POST', '/users/login',
    await req('/users/login', { method: 'POST', body: primary }))
  const token =
    loginRes.data && typeof loginRes.data === 'object' && 'access_token' in loginRes.data
      ? String((loginRes.data as { access_token: unknown }).access_token)
      : null

  record('get current user', 'GET', '/users/me', await req('/users/me', { token }))

  // Second user for delegation.
  record('register secondary user', 'POST', '/users/register',
    await req('/users/register', { method: 'POST', body: secondary }))

  // --- Config ---------------------------------------------------------------
  const modelsRes = record('list models', 'GET', '/config/models',
    await req('/config/models', { token }))
  const stratRes = record('list query strategies', 'GET', '/config/query-strategies',
    await req('/config/query-strategies', { token }))
  record('list capabilities', 'GET', '/config/capabilities',
    await req('/config/capabilities', { token }))

  const models = pickString(modelsRes.data, ['models'])
  const strategies = pickString(stratRes.data, ['strategies', 'query_strategies'])

  // --- Data -----------------------------------------------------------------
  const teamsRes = record('list teams', 'GET', '/data/teams', await req('/data/teams', { token }))
  record('list categories', 'GET', '/data/categories', await req('/data/categories', { token }))
  record('list subcategories', 'GET', '/data/subcategories', await req('/data/subcategories', { token }))
  const teams = pickString(teamsRes.data, ['teams'])

  // --- Active learning instance --------------------------------------------
  const modelName = models[0]
  const strategy = strategies[0]
  // class_list must cover every label present in the training data, otherwise
  // the classifier rejects it ("y contains previously unseen labels").
  const classList = teams
  let instanceId: number | null = null

  if (modelName && strategy && classList.length >= 2) {
    const createRes = record('create instance', 'POST', '/activelearning/new',
      await req('/activelearning/new', {
        method: 'POST',
        token,
        body: { model_name: modelName, qs_strategy: strategy, class_list: classList },
      }))
    if (createRes.data && typeof createRes.data === 'object' && 'instance_id' in createRes.data) {
      instanceId = Number((createRes.data as { instance_id: unknown }).instance_id)
    }
  } else {
    results.push({
      name: 'create instance', method: 'POST', path: '/activelearning/new',
      status: 'WARN', code: 'skip',
      detail: 'insufficient config/teams to build a NewInstance request',
    })
  }

  let queryIdx: string | null = null
  if (instanceId != null && Number.isFinite(instanceId)) {
    const id = instanceId

    const nextRes = record('next instance', 'GET', `/activelearning/${id}/next`,
      await req(`/activelearning/${id}/next`, { token, query: { batch_size: 1 } }))
    const idxs = pickString(nextRes.data, ['query_idx'])
    queryIdx = idxs[0] ?? null

    // Fetch ticket detail for the selected index.
    if (queryIdx) {
      record('get tickets', 'POST', '/data/tickets',
        await req('/data/tickets', { method: 'POST', token, body: [queryIdx] }))
    }

     // Inference — by ticket ref (query_idx path).
    if (queryIdx) {
      record('infer (by query_idx)', 'POST', `/activelearning/${id}/infer`,
        await req(`/activelearning/${id}/infer`, { method: 'POST', token, query: { query_idx: [queryIdx] } }))
    }

    // Inference — ad-hoc body variant.
    record('infer (body)', 'POST', `/activelearning/${id}/infer`,
      await req(`/activelearning/${id}/infer`, {
        method: 'POST', token, body: { title_anon: 'VPN not connecting', description_anon: 'timeout' },
      }))

    // Class probabilities — by ticket ref (query_idx path).
    if (queryIdx) {
      record('infer_proba (by query_idx)', 'POST', `/activelearning/${id}/infer_proba`,
        await req(`/activelearning/${id}/infer_proba`, { method: 'POST', token, query: { query_idx: [queryIdx] } }))
    }

    // Class probabilities — ad-hoc body variant.
    record('infer_proba (body)', 'POST', `/activelearning/${id}/infer_proba`,
      await req(`/activelearning/${id}/infer_proba`, {
        method: 'POST', token, body: { title_anon: 'VPN not connecting', description_anon: 'timeout' },
      }))

    // XAI — synchronous LIME by ticket ref (query_idx query params).
    if (queryIdx) {
      record('explain_lime (by query_idx)', 'POST', `/xai/${id}/explain_lime`,
        await req(`/xai/${id}/explain_lime`, {
          method: 'POST', token, query: { query_idx: [queryIdx], top_k: 1 },
        }))
    }

    // XAI — synchronous LIME by body.
    record('explain_lime (body)', 'POST', `/xai/${id}/explain_lime`,
      await req(`/xai/${id}/explain_lime`, {
        method: 'POST', token, query: { top_k: 1 },
        body: { title_anon: 'VPN not connecting', description_anon: 'timeout' },
      }))

    // XAI — nearest neighbours by ticket ref (repeated query_idx query params).
    if (queryIdx) {
      record('nearest (by query_idx)', 'POST', `/xai/${id}/nearest`,
        await req(`/xai/${id}/nearest`, {
          method: 'POST', token, query: { query_idx: [queryIdx], top_k: 1 },
        }))
    }

    // XAI — nearest neighbours by body.
    record('nearest (body)', 'POST', `/xai/${id}/nearest`,
      await req(`/xai/${id}/nearest`, {
        method: 'POST', token, query: { top_k: 1 },
        body: { title_anon: 'VPN not connecting', description_anon: 'timeout' },
      }))

    // Label-with-info (records decision + booleans).
    if (queryIdx) {
      const now = new Date()
      const start = new Date(now.getTime() - 4000)
      record('label-with-info', 'POST', `/activelearning/${id}/label-with-info`,
        await req(`/activelearning/${id}/label-with-info`, {
          method: 'POST', token,
          body: [{
            ticket_id: queryIdx,
            label: classList[0],
            model_prediction: classList[0],
            start_time: start.toISOString(),
            end_time: now.toISOString(),
            most_helpful_feature: 'lime',
            is_tired: false,
            is_difficult: false,
            i_dont_know: false,
          }],
        }))
    }

    // Metrics.
    record('instance info', 'GET', `/activelearning/${id}/info`,
      await req(`/activelearning/${id}/info`, { token }))

    // Delegation (owner only).
    record('delegate instance', 'POST', `/activelearning/${id}/delegate`,
      await req(`/activelearning/${id}/delegate`, { method: 'POST', token, body: { username: secondary.username } }))
    record('list delegates', 'GET', `/activelearning/${id}/delegates`,
      await req(`/activelearning/${id}/delegates`, { token }))
    record('revoke delegation', 'DELETE', `/activelearning/${id}/delegate/{username}`,
      await req(`/activelearning/${id}/delegate/${encodeURIComponent(secondary.username)}`, { method: 'DELETE', token }))
  }

  // Instances list (owned + delegated).
  record('list instances', 'GET', '/activelearning/instances', await req('/activelearning/instances', { token }))

  // --- Optional / possibly-undeployed endpoints -----------------------------
  record('resolution process', 'POST', '/resolution/process',
    await req('/resolution/process', {
      method: 'POST', token,
      body: { ticket_title: 'VPN not connecting', ticket_description: 'timeout errors' },
    }))
  record('analytics overview', 'GET', '/analytics/overview', await req('/analytics/overview', { token }))

  // --- Cleanup --------------------------------------------------------------
  if (instanceId != null && Number.isFinite(instanceId)) {
    record('delete instance (cleanup)', 'DELETE', `/activelearning/${instanceId}`,
      await req(`/activelearning/${instanceId}`, { method: 'DELETE', token }))
  }

  // --- Report ---------------------------------------------------------------
  const icon = (s: Status) => (s === 'PASS' ? '✓' : s === 'WARN' ? '!' : '✗')
  console.log(`${'-'.repeat(60)}`)
  for (const r of results) {
    const line = `${icon(r.status)} [${String(r.code).padStart(3)}] ${r.method.padEnd(6)} ${r.path}`
    console.log(r.detail ? `${line}\n        ↳ ${r.detail}` : line)
  }

  const counts = results.reduce(
    (acc, r) => ({ ...acc, [r.status]: (acc[r.status] ?? 0) + 1 }),
    {} as Record<Status, number>,
  )
  console.log(`${'-'.repeat(60)}`)
  console.log(`PASS: ${counts.PASS ?? 0}   WARN: ${counts.WARN ?? 0}   FAIL: ${counts.FAIL ?? 0}`)
  console.log(
    'Note: WARN = endpoint reachable but request rejected (4xx) or optional/not-deployed (404). ' +
      'FAIL = network error or 5xx.\n',
  )

  process.exit((counts.FAIL ?? 0) > 0 ? 1 : 0)
}

main().catch((e) => {
  console.error('Fatal error running smoke test:', e)
  process.exit(1)
})
