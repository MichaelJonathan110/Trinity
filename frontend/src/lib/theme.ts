/**
 * Automatic Day/Night theme (spec 45, 46).
 * Day 06:00-17:59, Night 18:00-05:59, in the DEVICE'S local timezone.
 * The boundary is re-checked every 30s so the app flips without a refresh.
 */
export type ThemePref = 'auto' | 'day' | 'night'
export type ResolvedTheme = 'day' | 'night'

const KEY = 'trinity.theme'
const DAY_START = 6
const DAY_END = 18

export function getPref(): ThemePref {
  const raw = localStorage.getItem(KEY)
  return raw === 'day' || raw === 'night' ? raw : 'auto'
}

export function setPref(pref: ThemePref): void {
  localStorage.setItem(KEY, pref)
  apply(pref)
}

export function resolve(pref: ThemePref, now: Date = new Date()): ResolvedTheme {
  if (pref !== 'auto') return pref
  const h = now.getHours()
  return h >= DAY_START && h < DAY_END ? 'day' : 'night'
}

export function apply(pref: ThemePref = getPref()): ResolvedTheme {
  const resolved = resolve(pref)
  document.documentElement.setAttribute('data-theme', resolved)
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', resolved === 'day' ? '#FAFAF8' : '#0E1116')
  return resolved
}

/** Starts the boundary watcher. Returns a cleanup function. */
export function watch(onChange: (t: ResolvedTheme) => void): () => void {
  let last = apply()
  const tick = () => {
    const next = apply()
    if (next !== last) { last = next; onChange(next) }
  }
  const id = window.setInterval(tick, 30_000)
  const onVisible = () => { if (document.visibilityState === 'visible') tick() }
  document.addEventListener('visibilitychange', onVisible)
  return () => { window.clearInterval(id); document.removeEventListener('visibilitychange', onVisible) }
}
