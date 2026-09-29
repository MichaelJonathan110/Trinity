/**
 * Responsive shell. Mobile gets a bottom tab bar; desktop gets a sidebar.
 * Today sits behind the wordmark, so the bar carries the working sections.
 * Preparation earns a primary slot: a cut/bulk/recomp phase is a daily concern,
 * not something to bury in Account, so the bar carries six sections.
 */
import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  IconAccount, IconExercise, IconNutrition, IconPrep, IconRest, IconSteps, IconToday
} from './icons'
import { useAuth } from '../stores/auth'
import { usePrefs } from '../stores/prefs'
import { apply, resolve } from '../lib/theme'
import { OfflineBanner } from './OfflineBanner'

export interface NavItem {
  to: string
  label: string
  Icon: (p: { size?: number }) => JSX.Element
}

export const NAV: NavItem[] = [
  { to: '/nutrition', label: 'Nutrition', Icon: IconNutrition },
  { to: '/exercise', label: 'Exercise', Icon: IconExercise },
  { to: '/preparation', label: 'Preparation', Icon: IconPrep },
  { to: '/rest', label: 'Rest', Icon: IconRest },
  { to: '/steps', label: 'Steps', Icon: IconSteps },
  { to: '/account', label: 'Account', Icon: IconAccount }
]

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const logout = useAuth((s) => s.logout)
  const themePref = usePrefs((s) => s.themePref)
  const setTheme = usePrefs((s) => s.setTheme)

  const resolved = resolve(themePref)
  const cycleTheme = () => {
    const next = resolved === 'day' ? 'night' : 'day'
    setTheme(next)
    apply(next)
  }

  return (
    <div className="shell">
      <OfflineBanner />
      <aside className="sidebar">
        <button className="wordmark" onClick={() => navigate('/')} aria-label="TRINITY home">
          <span className="wordmark-mark" aria-hidden="true" />
          <span className="wordmark-text">TRINITY</span>
        </button>
        <p className="wordmark-tagline">Fuel. Recover. Perform.</p>
        <nav aria-label="Primary">
          <ul className="nav-list">
            <li>
              <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
                <IconToday size={20} />
                <span>Today</span>
              </NavLink>
            </li>
            {NAV.map(({ to, label, Icon }) => (
              <li key={to}>
                <NavLink to={to} className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
                  <Icon size={20} />
                  <span>{label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="sidebar-foot">
          <button className="theme-toggle" onClick={cycleTheme}>
            {resolved === 'day' ? 'Night' : 'Day'} theme
          </button>
          {me ? <p className="sidebar-user">{me.email}</p> : null}
          <button className="link-btn" onClick={() => { logout(); navigate('/login') }}>
            Sign out
          </button>
        </div>
      </aside>

      <header className="topbar">
        <button className="wordmark wordmark-compact" onClick={() => navigate('/')} aria-label="TRINITY home">
          <span className="wordmark-mark" aria-hidden="true" />
          <span className="wordmark-text">TRINITY</span>
        </button>
        <button className="theme-toggle" onClick={cycleTheme} aria-label="Switch theme">
          {resolved === 'day' ? 'Night' : 'Day'}
        </button>
      </header>

      <main className="content">{children}</main>

      <nav className="tabbar" aria-label="Primary">
        <ul>
          {NAV.map(({ to, label, Icon }) => (
            <li key={to}>
              <NavLink to={to} className={({ isActive }) => `tab${isActive ? ' is-active' : ''}`}>
                <Icon size={22} />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}
