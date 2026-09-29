/** The central Today view: the four pillars, readiness and the headline insight (spec 43, 44, 91). */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card, ErrorState, LoadingState, Metric, Progress } from '../components/ui'
import { api } from '../lib/api'
import { longDate, minutesToHm, num } from '../lib/format'
import type { TodayPayload } from '../lib/types'

export default function TodayPage() {
  const q = useQuery({
    queryKey: ['today'],
    queryFn: () => api.get<TodayPayload>('/insights/today')
  })

  if (q.isLoading) return <LoadingState what="today's overview" />
  if (q.isError) {
    return <ErrorState message={q.error instanceof Error ? q.error.message : 'Could not load today'} onRetry={() => void q.refetch()} />
  }
  const d = q.data!
  const r = d.readiness

  return (
    <>
      <header className="page-head">
        <h1>{d.greeting}, {d.display_name}</h1>
        <p className="page-sub">{longDate(d.for_date)}</p>
      </header>

      {!d.has_data ? (
        <Card>
          <h2 style={{ marginBottom: 8 }}>Nothing logged for today yet</h2>
          <p className="state-body">
            Log a meal, a night of sleep, a session or your steps and this page fills in from your own data.
          </p>
          <div className="row" style={{ marginTop: 16 }}>
            <Link className="btn btn-primary" to="/nutrition">Log food</Link>
            <Link className="btn btn-ghost" to="/rest">Log sleep</Link>
          </div>
        </Card>
      ) : (
        <>
          {/* Readiness is the number this screen exists to show, so it carries the
              one accent on the page; the other three pillars stay neutral. */}
          <Card className="metric-hero">
            <Metric
              label="Training readiness" value={r.score ?? '--'} unit={r.score ? '/100' : ''}
              note={r.label.replace('_', ' ')} tone="accent"
            />
            <div className="stat-row" style={{ marginTop: 24 }}>
              <div className="stat">
                <span className="stat-label">Calories</span>
                <span className="stat-value">{num(d.pillars.find((p) => p.key === 'nutrition')?.score)}%</span>
                <span className="stat-note">of your target</span>
              </div>
              <div className="stat">
                <span className="stat-label">Sleep</span>
                <span className="stat-value">{minutesToHm(r.sleep_minutes)}</span>
                <span className="stat-note">{r.sleep_target_minutes ? `target ${minutesToHm(r.sleep_target_minutes)}` : 'no target set'}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Steps</span>
                <span className="stat-value">{num(d.pillars.find((p) => p.key === 'steps')?.score)}%</span>
                <span className="stat-note">of your goal</span>
              </div>
            </div>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 4 }}>Today's picture</h2>
            <p className="state-body" style={{ marginBottom: 16 }}>{d.headline}</p>
            <div className="pillars">
              {d.pillars.filter((p) => p.score !== null).map((p) => (
                <Progress
                  key={p.key} label={`${p.label} - ${p.detail}`}
                  value={p.score ?? 0} max={100} showPct
                  tone={(p.score ?? 0) >= 90 ? 'success' : (p.score ?? 0) >= 60 ? 'accent' : 'warning'}
                />
              ))}
            </div>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 8 }}>Insights</h2>
            {d.insights.length === 0 ? (
              <p className="state-body">No observations yet. Insights appear once there is enough logged data to compare.</p>
            ) : (
              d.insights.map((ins, i) => (
                <div className="insight" key={`${ins.title}-${i}`}>
                  <p className="insight-title">{ins.title}</p>
                  <p className="insight-body">{ins.body}</p>
                </div>
              ))
            )}
          </Card>

          <p className="source-note" style={{ marginTop: 24 }}>
            {r.note ?? 'Training readiness is an application estimate based on your logged data.'}
          </p>
        </>
      )}
    </>
  )
}
