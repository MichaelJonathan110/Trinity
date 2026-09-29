import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { LoadingState } from './components/ui'
import { useAuth } from './stores/auth'
import { watch } from './lib/theme'
import { usePrefs } from './stores/prefs'
import LoginPage from './pages/Login'
import OnboardingPage from './pages/Onboarding'
import TodayPage from './pages/Today'
import NutritionPage from './pages/Nutrition'
import RestPage from './pages/Rest'
import ExercisePage from './pages/Exercise'
import PreparationPage from './pages/Preparation'
import StepsPage from './pages/Steps'
import AccountPage from './pages/Account'

export default function App() {
  const status = useAuth((s) => s.status)
  const load = useAuth((s) => s.load)
  const setTheme = usePrefs((s) => s.setTheme)

  useEffect(() => { void load() }, [load])

  // Flip Day/Night automatically when the local-time boundary is crossed (spec 45).
  useEffect(() => watch(() => setTheme(usePrefs.getState().themePref)), [])

  if (status === 'unknown') {
    return (
      <div className="auth-wrap">
        <LoadingState what="your session" />
      </div>
    )
  }

  if (status === 'anonymous') {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<TodayPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/nutrition" element={<NutritionPage />} />
        <Route path="/rest" element={<RestPage />} />
        <Route path="/exercise" element={<ExercisePage />} />
        <Route path="/preparation" element={<PreparationPage />} />
        <Route path="/steps" element={<StepsPage />} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}
