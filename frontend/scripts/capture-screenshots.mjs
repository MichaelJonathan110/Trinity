/**
 * Capture real screenshots of the running TRINITY web app.
 *
 * Env: BASE_URL   (default http://127.0.0.1:5173)  web app origin
 *      API_BASE   (default http://127.0.0.1:8000)  API origin (login + seeding)
 *      OUT_DIR    (default ../docs/screenshots)
 *      CHANNEL    (default chrome)
 *      DEMO_EMAIL (default demo@trinity.app)     the seeded demo athlete
 *      DEMO_PASSWORD (default TrinityDemo123!)
 *
 * It signs in as the seeded demo athlete so every screen shows real data.
 * No placeholder images: if a page cannot be reached the script fails loudly.
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:5173'
const API_BASE = process.env.API_BASE ?? 'http://127.0.0.1:8000'
const OUT_DIR = process.env.OUT_DIR ?? '../docs/screenshots'
const CHANNEL = process.env.CHANNEL ?? 'chrome'
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? 'demo@trinity.app'
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? 'TrinityDemo123!'

async function authTokens() {
  const headers = { 'Content-Type': 'application/json' }
  // Prefer the seeded demo athlete (has a week of history).
  let res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST', headers,
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
  })
  if (!res.ok) throw new Error(`demo login failed: ${res.status} ${await res.text()}`)
  return await res.json()
}

// Real routes, read from src/App.tsx.
const SCREENS = [
  ['today', '/'],
  ['nutrition', '/nutrition'],
  ['rest', '/rest'],
  ['exercise', '/exercise'],
  ['steps', '/steps'],
  ['account', '/account'],
]
const VIEWPORTS = [
  ['desktop', 1280, 900],
  ['mobile', 390, 844],
]

const tokens = await authTokens()
mkdirSync(OUT_DIR, { recursive: true })
const browser = await chromium.launch({ channel: CHANNEL })

for (const [vp, width, height] of VIEWPORTS) {
  const ctx = await browser.newContext({ viewport: { width, height } })
  await ctx.addInitScript(
    ([a, r]) => {
      localStorage.setItem('trinity.access', a)
      localStorage.setItem('trinity.refresh', r)
    },
    [tokens.access_token, tokens.refresh_token],
  )
  const page = await ctx.newPage()
  for (const [name, path] of SCREENS) {
    await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1500)
    await page.screenshot({ path: `${OUT_DIR}/${name}-${vp}.png`, fullPage: true })
    console.log(`captured ${name}-${vp}`)
  }
  await ctx.close()
}

// The sign-in screen is captured unauthenticated, at desktop width.
const loginCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } })
const loginPage = await loginCtx.newPage()
await loginPage.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
await loginPage.waitForTimeout(1000)
await loginPage.screenshot({ path: `${OUT_DIR}/login-desktop.png`, fullPage: true })
console.log('captured login-desktop')
await loginCtx.close()

await browser.close()
console.log('capture complete')
