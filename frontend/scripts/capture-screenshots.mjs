// One-off screenshot capture for the demo deck.
// Reuses the existing dev session token (read from a temp file) so no login is needed.
// Usage: node scripts/capture-screenshots.mjs
import { chromium } from 'playwright'
import { mkdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = resolve(__dirname, '../../docs/images/screenshots')
const BASE = process.env.APP_BASE ?? 'http://localhost:5173'
const TOKEN = readFileSync(process.env.TOKEN_FILE, 'utf8').trim()
const USER = JSON.stringify({ user_id: '79c42c3d-6ba4-4964-9595-75d1510b2227', username: 'fpdo@gft.com' })

mkdirSync(OUT_DIR, { recursive: true })

const pages = [
  { path: '/', name: '01-home', wait: 1500 },
  { path: '/training', name: '02-new-project', wait: 1500 },
  { path: '/queue', name: '03-ticket-queue', wait: 3000, action: 'selectTicket' },
  { path: '/manual', name: '04-manual-queue', wait: 3000 },
  { path: '/analytics', name: '05-analytics', wait: 3500 },
  { path: '/ticket-resolution', name: '06-ticket-evolution', wait: 2500, action: 'generateResolution' },
]

async function runAction(page, action) {
  if (action === 'selectTicket') {
    try {
      await page.locator('text=/^TKT-\\d+/').first().click({ timeout: 8000 })
      await page.waitForTimeout(2500)
    } catch (e) {
      console.log('  (selectTicket skipped:', e.message.split('\n')[0], ')')
    }
  }
  if (action === 'generateResolution') {
    try {
      await page.getByPlaceholder('Enter ticket title...').fill('VPN connection keeps dropping every few minutes')
      await page
        .getByPlaceholder('Enter ticket description...')
        .fill(
          'Since this morning my VPN disconnects every 5-10 minutes. I have to reconnect constantly and it interrupts my work. I am on the corporate laptop over home Wi-Fi.',
        )
      await page.getByRole('button', { name: /Generate solution/i }).click({ timeout: 8000 })
      await page.waitForTimeout(3500)
      // Bring the generated reply card into view for the screenshot.
      try {
        await page.getByText('Suggested Response', { exact: false }).first().scrollIntoViewIfNeeded({ timeout: 5000 })
      } catch {
        await page.getByText('Suggested Team', { exact: false }).first().scrollIntoViewIfNeeded({ timeout: 5000 })
      }
      await page.waitForTimeout(700)
    } catch (e) {
      console.log('  (generateResolution skipped:', e.message.split('\n')[0], ')')
    }
  }
}

const launchOpts = [{ channel: 'msedge' }, { channel: 'chrome' }, {}]
let browser
for (const opts of launchOpts) {
  try {
    browser = await chromium.launch({ headless: true, ...opts })
    console.log('Launched with', opts.channel ?? 'bundled chromium')
    break
  } catch (e) {
    console.log('Launch failed for', opts.channel ?? 'chromium', '-', e.message.split('\n')[0])
  }
}
if (!browser) throw new Error('No browser available')

const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
})

// Seed auth + mock mode into localStorage before any app code runs.
await context.addInitScript(
  ([token, user]) => {
    localStorage.setItem('humal-auth-token', token)
    localStorage.setItem('humal-auth-user', user)
    localStorage.setItem('humal-mock-mode', 'true')
  },
  [TOKEN, USER],
)

const page = await context.newPage()

for (const p of pages) {
  const url = `${BASE}${p.path}`
  console.log('Capturing', url)
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 })
  } catch {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 })
  }
  await page.waitForTimeout(p.wait)
  if (p.action) await runAction(page, p.action)
  await page.screenshot({ path: resolve(OUT_DIR, `${p.name}.png`), fullPage: false })
  console.log('  ->', `${p.name}.png`)
}

await browser.close()
console.log('Done. Screenshots in', OUT_DIR)
