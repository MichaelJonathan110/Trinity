/** Sleep logging, history, insights and training readiness (spec 23-28). */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button, Card, EmptyState, ErrorState, Legend, LoadingState, Metric, NumberField,
  SelectField, TextField
} from '../components/ui'
import { BarChart } from '../components/charts'
import { api } from '../lib/api'
import { isoDate, minutesToHm, num, shortDate } from '../lib/format'
import type { Readiness, RecoveryMetric, SleepAverage, SleepDay } from '../lib/types'

/* What each point on the 1-5 scales means, so the numbers are not guesswork.
   Quality is subjective by design: the scale measures how you felt, not a sensor. */
const SLEEP_QUALITY = [
  { key: '1', label: 'Terrible - woke often, feel unrested' },
  { key: '2', label: 'Poor - broken or too short' },
  { key: '3', label: 'Okay - neither good nor bad' },
  { key: '4', label: 'Good - slept through, feel rested' },
  { key: '5', label: 'Excellent - deep, unbroken, fully refreshed' }
]

const RECOVERED = [
  { key: '1', label: 'Drained - no energy for a session' },
  { key: '2', label: 'Tired - below par' },
  { key: '3', label: 'Normal - ready to train' },
  { key: '4', label: 'Fresh - good energy' },
  { key: '5', label: 'Excellent - fully charged' }
]

const SORENESS = [
  { key: '1', label: 'None - no muscle soreness' },
  { key: '2', label: 'Mild - noticeable, no impact' },
  { key: '3', label: 'Moderate - feel it on movement' },
  { key: '4', label: 'High - stiff, affects performance' },
  { key: '5', label: 'Severe - hard to move normally' }
]

export default function RestPage() {
  const qc = useQueryClient()
  const [bedtime, setBedtime] = useState('23:00')
  const [wake, setWake] = useState('07:00')
  const [quality, setQuality] = useState('4')
  const [goal, setGoal] = useState('8.0')
  const [subjective, setSubjective] = useState('4')
  const [soreness, setSoreness] = useState('2')

  const history = useQuery({
    queryKey: ['sleep'],
    queryFn: () => api.get<SleepDay[]>('/recovery/sleep?days=30')
  })
  const average = useQuery({
    queryKey: ['sleep', 'average'],
    queryFn: () => api.get<SleepAverage>('/recovery/sleep/average?days=7')
  })
  const readiness = useQuery({
    queryKey: ['readiness'],
    queryFn: () => api.get<Readiness>('/recovery/readiness')
  })
  const sleepGoal = useQuery({
    queryKey: ['sleep', 'goal'],
    queryFn: () => api.get<{ target_minutes: number }>('/recovery/sleep/goal')
  })
  const metrics = useQuery({
    queryKey: ['recovery', 'metrics'],
    queryFn: () => api.get<RecoveryMetric[]>('/recovery/metrics?days=30')
  })

  const saveSleep = useMutation({
    mutationFn: () => {
      const today = isoDate()
      const bed = new Date(`${today}T${bedtime}:00`)
      // A bedtime after noon belongs to the previous evening.
      if (Number(bedtime.slice(0, 2)) >= 12) bed.setDate(bed.getDate() - 1)
      const wakeAt = new Date(`${today}T${wake}:00`)
      return api.post('/recovery/sleep', {
        bedtime: bed.toISOString(), wake_at: wakeAt.toISOString(), quality: Number(quality)
      })
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['sleep'] })
      await qc.invalidateQueries({ queryKey: ['readiness'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
    }
  })

  const saveGoal = useMutation({
    mutationFn: () => api.put('/recovery/sleep/goal', { target_minutes: Math.round(Number(goal) * 60) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['sleep'] })
      await qc.invalidateQueries({ queryKey: ['readiness'] })
    }
  })

  const saveRecovery = useMutation({
    mutationFn: () => api.post('/recovery/metrics', {
      recorded_on: isoDate(), subjective_score: Number(subjective), soreness_score: Number(soreness)
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['recovery'] })
      await qc.invalidateQueries({ queryKey: ['readiness'] })
    }
  })

  const chartData = (history.data ?? []).slice(-14).map((h) => ({
    label: shortDate(h.date), value: h.duration_min / 60
  }))
  const targetHours = (sleepGoal.data?.target_minutes ?? 480) / 60
  const qualityWord = SLEEP_QUALITY.find((q) => q.key === quality)?.label ?? ''

  return (
    <>
      <header className="page-head">
        <h1>Rest</h1>
        <p className="page-sub">Sleep and recovery, and how they shape your training readiness.</p>
      </header>

      {readiness.isLoading ? <LoadingState what="your readiness estimate" /> : null}
      {readiness.isError ? (
        <ErrorState message={readiness.error instanceof Error ? readiness.error.message : 'Could not load readiness'} onRetry={() => void readiness.refetch()} />
      ) : null}

      {readiness.data ? (
        <Card className="metric-hero">
          <Metric
            label="TRINITY Training Readiness"
            value={readiness.data.score ?? '--'}
            unit={readiness.data.score ? '/100' : ''}
            note={readiness.data.label.replace('_', ' ')}
            tone="accent"
          />
          <p className="source-note" style={{ marginTop: 12 }}>{readiness.data.note}</p>
          <p className="list-meta" style={{ marginTop: 8 }}>
            Last night: {minutesToHm(readiness.data.sleep_minutes ?? null)} of {minutesToHm(readiness.data.sleep_target_minutes ?? 480)}.
            Built from {readiness.data.inputs} of 4 possible inputs.
          </p>
        </Card>
      ) : null}

      {average.data && average.data.days > 0 ? (
        <Card style={{ marginTop: 24 }}>
          <h2 style={{ marginBottom: 16 }}>Last 7 nights</h2>
          <div className="stat-row">
            <div className="stat">
              <span className="stat-label">Average duration</span>
              <span className="stat-value">{minutesToHm(average.data.avg_minutes)}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Average score</span>
              <span className="stat-value">{num(average.data.avg_score)}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Schedule consistency</span>
              <span className="stat-value">
                {average.data.consistency ? `${num(average.data.consistency)}%` : 'Needs 3+ nights'}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Nights logged</span>
              <span className="stat-value">{average.data.days}</span>
            </div>
          </div>
          <p className="source-note" style={{ marginTop: 16 }}>
            Sleep score is a TRINITY estimate from duration and your own quality rating. It is not a medical measurement.
          </p>
        </Card>
      ) : null}

      <div className="grid grid-2" style={{ marginTop: 24 }}>
        <Card>
          <h2 style={{ marginBottom: 16 }}>Log a night</h2>
          <div className="stack">
            <TextField label="Bedtime" type="time" value={bedtime} onChange={setBedtime} />
            <TextField label="Wake time" type="time" value={wake} onChange={setWake} />
            <SelectField
              label="Sleep quality" value={quality} onChange={setQuality}
              options={SLEEP_QUALITY.map((q) => ({ value: q.key, label: `${q.key} of 5` }))}
              hint={`${quality} of 5 - ${qualityWord}`}
            />
            <Legend title="What the sleep quality scale means" items={SLEEP_QUALITY} />
            <Button onClick={() => saveSleep.mutate()} disabled={saveSleep.isPending}>
              {saveSleep.isPending ? 'Saving...' : 'Save sleep'}
            </Button>
            {saveSleep.isSuccess ? <p className="form-ok">Sleep logged.</p> : null}
            {saveSleep.isError ? (
              <p className="form-error">{saveSleep.error instanceof Error ? saveSleep.error.message : 'Could not save'}</p>
            ) : null}
          </div>
        </Card>

        <Card>
          <h2 style={{ marginBottom: 16 }}>Recovery check-in</h2>
          <div className="stack">
            <SelectField
              label="How recovered do you feel?" value={subjective} onChange={setSubjective}
              options={RECOVERED.map((r) => ({ value: r.key, label: `${r.key} of 5` }))}
              hint={`${subjective} of 5 - ${RECOVERED.find((r) => r.key === subjective)?.label}`}
            />
            <SelectField
              label="Muscle soreness" value={soreness} onChange={setSoreness}
              options={SORENESS.map((s) => ({ value: s.key, label: `${s.key} of 5` }))}
              hint={`${soreness} of 5 - ${SORENESS.find((s) => s.key === soreness)?.label}`}
            />
            <Legend title="What the recovery scale means" items={RECOVERED} />
            <Button onClick={() => saveRecovery.mutate()} disabled={saveRecovery.isPending}>
              {saveRecovery.isPending ? 'Saving...' : 'Save check-in'}
            </Button>
            {saveRecovery.isSuccess ? <p className="form-ok">Check-in saved.</p> : null}
            <div style={{ marginTop: 8 }}>
              <NumberField
                label="Sleep goal" value={goal} onChange={setGoal} min={4} max={12} step="0.5"
                hint={`Hours. Currently ${minutesToHm(sleepGoal.data?.target_minutes ?? 480)}.`}
              />
              <Button variant="ghost" onClick={() => saveGoal.mutate()} disabled={saveGoal.isPending}>
                Update sleep goal
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <Card style={{ marginTop: 24 }}>
        <h2 style={{ marginBottom: 16 }}>Sleep duration, last 14 nights</h2>
        {history.data && history.data.length > 0 ? (
          <BarChart data={chartData} unit="h" goal={targetHours} label="Hours slept per night" />
        ) : (
          <EmptyState title="No sleep data yet" body="Log your first night above and the trend appears here." />
        )}
      </Card>

      {metrics.data && metrics.data.length > 0 ? (
        <Card style={{ marginTop: 24 }}>
          <h2 style={{ marginBottom: 12 }}>Recent check-ins</h2>
          <ul className="list">
            {metrics.data.slice(0, 7).map((m) => (
              <li className="list-row" key={m.id}>
                <div className="list-main">
                  <span className="list-title">{shortDate(m.recorded_on)}</span>
                  <span className="list-meta">
                    Recovered {m.subjective_score ?? '--'}/5, soreness {m.soreness_score ?? '--'}/5
                  </span>
                </div>
                <span className="list-value">
                  {m.readiness_score !== null ? `${m.readiness_score}/100` : '--'}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {history.data && history.data.length > 0 ? (
        <Card style={{ marginTop: 24 }}>
          <h2 style={{ marginBottom: 12 }}>Nights</h2>
          <ul className="list">
            {[...history.data].reverse().slice(0, 14).map((h) => (
              <li className="list-row" key={h.date}>
                <div className="list-main">
                  <span className="list-title">{shortDate(h.date)}</span>
                  <span className="list-meta">
                    {new Date(h.bedtime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })} to{' '}
                    {new Date(h.wake_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                    {h.quality ? ` - quality ${h.quality}/5 (${SLEEP_QUALITY.find((q) => q.key === String(h.quality))?.label.split(' - ')[0]})` : ''}
                  </span>
                </div>
                <span className="list-value">{minutesToHm(h.duration_min)}</span>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </>
  )
}
