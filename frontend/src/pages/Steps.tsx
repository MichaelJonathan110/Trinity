/** Daily steps, history and goal (spec 40-42). */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button, Card, DataSourceNote, EmptyState, ErrorState, LoadingState, Metric,
  NumberField, Progress
} from '../components/ui'
import { BarChart } from '../components/charts'
import { api } from '../lib/api'
import { isoDate, num, shortDate } from '../lib/format'
import type { DayActivity, StepsHistoryDay } from '../lib/types'

export default function StepsPage() {
  const qc = useQueryClient()
  const [steps, setSteps] = useState('')
  const [goal, setGoal] = useState('')

  const today = useQuery({
    queryKey: ['activity', 'day'],
    queryFn: () => api.get<DayActivity>('/activity/steps')
  })
  const history = useQuery({
    queryKey: ['activity', 'history'],
    queryFn: () => api.get<StepsHistoryDay[]>('/activity/steps/history?days=30')
  })

  const save = useMutation({
    mutationFn: () => api.post('/activity/steps', { recorded_on: isoDate(), steps: Number(steps) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['activity'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
      setSteps('')
    }
  })

  const saveGoal = useMutation({
    mutationFn: () => api.put('/activity/steps/goal', { step_goal: Number(goal) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['activity'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
      setGoal('')
    }
  })

  const d = today.data
  const chartData = (history.data ?? []).filter((h) => h.logged).slice(-14).map((h) => ({
    label: shortDate(h.date), value: h.steps
  }))
  const loggedDays = history.data?.filter((h) => h.logged) ?? []

  return (
    <>
      <header className="page-head">
        <h1>Steps</h1>
        <p className="page-sub">Daily activity and how much you move outside training.</p>
      </header>

      {today.isLoading ? <LoadingState what="today's activity" /> : null}
      {today.isError ? (
        <ErrorState message={today.error instanceof Error ? today.error.message : 'Could not load activity'} onRetry={() => void today.refetch()} />
      ) : null}

      {d ? (
        <Card className="metric-hero">
          <Metric
            label="Steps today" value={num(d.steps)} unit="steps"
            note={`Goal ${num(d.step_goal)}`} tone="accent"
          />
          <div style={{ marginTop: 20 }}>
            <Progress
              label={`${Math.round((d.steps / d.step_goal) * 100)}% of goal`}
              value={d.steps} max={d.step_goal} showPct
              tone={d.steps >= d.step_goal ? 'success' : 'accent'}
            />
          </div>
          {d.distance_m || d.active_kcal || d.active_minutes ? (
            <div className="stat-row" style={{ marginTop: 24 }}>
              {d.distance_m ? (
                <div className="stat"><span className="stat-label">Distance</span><span className="stat-value">{num(d.distance_m / 1000, 2)} km</span></div>
              ) : null}
              {d.active_kcal ? (
                <div className="stat"><span className="stat-label">Active calories</span><span className="stat-value">{num(d.active_kcal)}</span></div>
              ) : null}
              {d.active_minutes ? (
                <div className="stat"><span className="stat-label">Active minutes</span><span className="stat-value">{d.active_minutes}</span></div>
              ) : null}
            </div>
          ) : (
            <p className="list-meta" style={{ marginTop: 16 }}>
              Distance and active calories appear when your source records them. Manual entries record steps only.
            </p>
          )}
        </Card>
      ) : null}

      <div className="grid grid-2" style={{ marginTop: 24 }}>
        <Card>
          <h2 style={{ marginBottom: 16 }}>Log steps</h2>
          <div className="stack">
            <NumberField label="Steps today" value={steps} onChange={setSteps} min={0} max={200000} placeholder="8421" />
            <Button onClick={() => save.mutate()} disabled={save.isPending || steps === ''}>
              {save.isPending ? 'Saving...' : 'Save steps'}
            </Button>
            {save.isSuccess ? <p className="form-ok">Steps saved.</p> : null}
            {save.isError ? <p className="form-error">{save.error instanceof Error ? save.error.message : 'Could not save'}</p> : null}
          </div>
        </Card>

        <Card>
          <h2 style={{ marginBottom: 16 }}>Daily goal</h2>
          <div className="stack">
            <NumberField
              label="Step goal" value={goal} onChange={setGoal} min={1000} max={100000}
              placeholder={String(d?.step_goal ?? 10000)}
              hint="10,000 is a common convention, not a requirement. Set what fits your life."
            />
            <Button variant="ghost" onClick={() => saveGoal.mutate()} disabled={saveGoal.isPending || goal === ''}>
              Update goal
            </Button>
          </div>
        </Card>
      </div>

      <Card style={{ marginTop: 24 }}>
        <h2 style={{ marginBottom: 16 }}>Recent activity</h2>
        {chartData.length > 0 ? (
          <BarChart data={chartData} goal={d?.step_goal} label="Steps per logged day" />
        ) : (
          <EmptyState title="No step data yet" body="Log today's steps and your activity history starts building." />
        )}
        {loggedDays.length > 0 ? (
          <p className="list-meta" style={{ marginTop: 12 }}>
            {loggedDays.length} logged days in the last 30. Average {num(loggedDays.reduce((s, h) => s + h.steps, 0) / loggedDays.length)} steps
            on days you logged.
          </p>
        ) : null}
      </Card>

      <DataSourceNote>
        TRINITY does not estimate steps. Every number here is one you entered or a value a connected source reported.
        Automatic health-data sync is planned and clearly marked as unavailable until it exists.
      </DataSourceNote>
    </>
  )
}
