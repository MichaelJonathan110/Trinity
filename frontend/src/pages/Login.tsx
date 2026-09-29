import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, TextField } from '../components/ui'
import { useAuth } from '../stores/auth'

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const login = useAuth((s) => s.login)
  const register = useAuth((s) => s.register)
  const navigate = useNavigate()

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (mode === 'login') await login(email.trim(), password)
      else await register(email.trim(), password, displayName.trim())
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="wordmark">
            <span className="wordmark-mark" aria-hidden="true" />
            <span className="wordmark-text">TRINITY</span>
          </span>
          <p className="page-sub">Fuel. Recover. Perform.</p>
        </div>

        <Card>
          <h1 style={{ marginBottom: 8 }}>{mode === 'login' ? 'Sign in' : 'Create your account'}</h1>
          <p className="page-sub" style={{ marginBottom: 24 }}>
            {mode === 'login'
              ? 'Your training, nutrition and recovery in one place.'
              : 'Start tracking the three pillars that drive performance.'}
          </p>

          <form className="stack" onSubmit={submit}>
            {mode === 'register' ? (
              <TextField
                label="Name" required value={displayName} onChange={setDisplayName}
                placeholder="Your Name" hint="Shown only to you."
              />
            ) : null}
            <TextField
              label="Email" type="email" required value={email} onChange={setEmail}
              placeholder="you@example.com"
            />
            <TextField
              label="Password" type="password" required value={password} onChange={setPassword}
              placeholder="At least 8 characters"
              hint={mode === 'register' ? 'Mix letters and numbers.' : undefined}
            />
            {error ? <p className="form-error" role="alert">{error}</p> : null}
            <Button type="submit" full disabled={busy}>
              {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>

          <div className="auth-switch">
            <span>{mode === 'login' ? 'New here?' : 'Already have an account?'}</span>
            <button
              className="link-btn"
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null) }}
            >
              {mode === 'login' ? 'Create an account' : 'Sign in'}
            </button>
          </div>
        </Card>
      </div>
    </div>
  )
}
