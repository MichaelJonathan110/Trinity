/**
 * Preparation: cut / bulk / recomp phase management (spec 66, 67).
 *
 * Every judgement on this page is made on WEEKLY AVERAGE bodyweight, never a
 * single weigh-in, because daily weight moves with water, sodium and glycogen as
 * well as tissue. The page says so where it matters, and it never shows a rate
 * before two full weeks of data exist.
 */
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button, Card, Chip, DataSourceNote, EmptyState, ErrorState, Legend, LoadingState,
  Metric, NumberField, Progress, Segmented, SelectField, TextField
} from '../components/ui'
import { LineChart } from '../components/charts'
import { api } from '../lib/api'
import { isoDate, kg, num, shortDate } from '../lib/format'
import type { PreparationStatus, RefeedEntry, WeightSeries } from '../lib/types'

const PHASES = [
  { value: 'cut', label: 'Cut - lose fat' },
  { value: 'recomp', label: 'Recomp - hold weight' },
  { value: 'bulk', label: 'Bulk - gain size' },
  { value: 'maintain', label: 'Maintain' }
]

/* What each phase is for, and the rate it usually targets. A phase is a plan with
   a clock, so the user must be able to see what the plan actually is. */
const PHASE_LEGEND = [
  { key: 'Cut', label: 'Lose fat while holding muscle. A sensible pace is 0.5-1% of bodyweight per week.' },
  { key: 'Bulk', label: 'Gain size. A lean-gain pace is about 0.25-0.5% per week; faster adds fat.' },
  { key: 'Recomp', label: 'Hold bodyweight and change composition. The scale stays flat on purpose.' },
  { key: 'Maintain', label: 'Hold what you have. No intended change either way.' }
]

const VERDICT_TONE: Record<string, 'accent' | 'success' | 'warning' | 'danger' | 'neutral'> = {
  on_plan: 'success', too_slow: 'warning', too_fast: 'warning', unknown: 'neutral'
}

type Granularity = 'daily' | 'weekly' | 'monthly'

const GRANULARITY_OPTIONS: { value: Granularity; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' }
]

export default function PreparationPage() {
  const qc = useQueryClient()
  const status = useQuery({
    queryKey: ['prep'],
    queryFn: () => api.get<PreparationStatus>('/prep/phase')
  })
  const refeeds = useQuery({
    queryKey: ['prep', 'refeeds'],
    queryFn: () => api.get<RefeedEntry[]>('/prep/refeeds')
  })

  const [granularity, setGranularity] = useState<Granularity>('weekly')
  const series = useQuery({
    queryKey: ['prep', 'weight-series', granularity],
    queryFn: () => api.get<WeightSeries>(`/prep/weight-series?granularity=${granularity}&months=12`)
  })

  const [form, setForm] = useState({
    phase_type: 'cut', target_weight_kg: '', target_rate_pct_per_week: '', target_weeks: '', notes: ''
  })
  const [weighIn, setWeighIn] = useState({ measured_on: isoDate(), weight_kg: '' })
  const [refeed, setRefeed] = useState({ occurred_on: isoDate(), kind: 'refeed', days: '1', notes: '' })

  // Prefill the rate box with the phase's default whenever the phase changes, so
  // the user edits a real number instead of guessing what "0.5%" should look like.
  useEffect(() => {
    const defaults: Record<string, string> = { cut: '-0.7', bulk: '0.35', recomp: '0', maintain: '0' }
    setForm((f) => ({ ...f, target_rate_pct_per_week: defaults[f.phase_type] ?? '' }))
  }, [form.phase_type])

  const start = useMutation({
    mutationFn: () => api.post('/prep/phase', {
      phase_type: form.phase_type,
      target_weight_kg: form.target_weight_kg ? Number(form.target_weight_kg) : undefined,
      target_rate_pct_per_week: form.target_rate_pct_per_week !== ''
        ? Number(form.target_rate_pct_per_week) : undefined,
      target_weeks: form.target_weeks ? Number(form.target_weeks) : undefined,
      notes: form.notes.trim() || undefined
    }),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['prep'] }) }
  })

  const logWeight = useMutation({
    mutationFn: () => api.post('/profile/metrics', {
      measured_on: weighIn.measured_on,
      weight_kg: Number(weighIn.weight_kg)
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['prep'] })
      await qc.invalidateQueries({ queryKey: ['prep', 'weight-series'] })
      setWeighIn({ measured_on: isoDate(), weight_kg: '' })
    }
  })

  const accept = useMutation({
    mutationFn: (delta: number) => api.post('/prep/phase/adjustment', { delta_kcal: delta, apply: true }),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['prep'] }) }
  })

  const end = useMutation({
    mutationFn: () => api.post('/prep/phase/end'),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['prep'] }) }
  })

  const addRefeed = useMutation({
    mutationFn: () => api.post('/prep/refeeds', {
      occurred_on: refeed.occurred_on,
      kind: refeed.kind,
      days: Number(refeed.days) || 1,
      notes: refeed.notes.trim() || undefined
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['prep'] })
      setRefeed({ occurred_on: isoDate(), kind: 'refeed', days: '1', notes: '' })
    }
  })

  const data = status.data
  const active = data?.active && data.phase
  const targetWeeks = data?.phase?.target_weeks ?? null
  const points = (series.data?.points ?? []).map((p) => ({ x: shortDate(p.date), y: p.value }))

  return (
    <>
      <header className="page-head">
        <h1>Preparation</h1>
        <p className="page-sub">
          Run a cut, bulk or recomp against a target rate and a target number of weeks, judged on
          weekly average bodyweight.
        </p>
      </header>

      {status.isLoading ? <LoadingState what="your phase" /> : null}
      {status.isError ? (
        <ErrorState
          message={status.error instanceof Error ? status.error.message : 'Could not load your phase'}
          onRetry={() => void status.refetch()}
        />
      ) : null}

      {data && !active ? (
        <Card>
          <h2 style={{ marginBottom: 12 }}>Start a phase</h2>
          <EmptyState
            title="No phase is running"
            body={data.note ?? 'Start a phase to track a cut, bulk or recomp against a target rate.'}
          />
        </Card>
      ) : null}

      {active && data.phase ? (
        <>
          <Card>
            <div className="section-title">
              <div>
                <h2 style={{ textTransform: 'capitalize' }}>{data.phase.phase_type}</h2>
                <p className="list-meta">
                  Started {shortDate(data.phase.started_on)} - week {data.phase.weeks_on_phase + 1}
                  {targetWeeks ? ` of ${targetWeeks}` : ''}
                  {data.planned_end_on ? ` (finish about ${shortDate(data.planned_end_on)})` : ''}
                </p>
              </div>
              <Chip tone={VERDICT_TONE[data.verdict?.verdict ?? 'unknown'] ?? 'neutral'}>
                {data.verdict?.label ?? 'Not enough data yet'}
              </Chip>
            </div>

            {targetWeeks ? (
              <div style={{ marginTop: 16 }}>
                <Progress
                  label={`Plan progress - week ${data.phase.weeks_on_phase} of ${targetWeeks}`}
                  value={data.phase.weeks_on_phase} max={targetWeeks} showPct
                />
                <p className="list-meta" style={{ marginTop: 8 }}>
                  {data.weeks_remaining && data.weeks_remaining > 0
                    ? `${data.weeks_remaining} ${data.weeks_remaining === 1 ? 'week' : 'weeks'} left on the plan.`
                    : 'The planned number of weeks has been reached.'}
                  {data.projected_finish_kg !== null && data.projected_finish_kg !== undefined
                    ? ` At the current rate you would finish around ${num(data.projected_finish_kg, 1)} kg.`
                    : ''}
                  {data.on_track === true ? ' That lands on your target.'
                    : data.on_track === false ? ' That is off your target weight.' : ''}
                </p>
              </div>
            ) : (
              <p className="list-meta" style={{ marginTop: 12 }}>
                No target duration set. Add one below to see how far through the plan you are.
              </p>
            )}

            <div className="stat-row">
              <div className="stat">
                <span className="stat-label">Current weight</span>
                <span className="stat-value">{data.current_weight_kg !== null ? num(data.current_weight_kg, 1) : '--'}</span>
                <span className="stat-note">kg</span>
              </div>
              <div className="stat">
                <span className="stat-label">Actual rate</span>
                <span className="stat-value">
                  {data.actual_pct_per_week !== null && data.actual_pct_per_week !== undefined
                    ? `${data.actual_pct_per_week > 0 ? '+' : ''}${num(data.actual_pct_per_week, 2)}` : '--'}
                </span>
                <span className="stat-note">% bodyweight / week</span>
              </div>
              <div className="stat">
                <span className="stat-label">Target rate</span>
                <span className="stat-value">
                  {data.phase.target_rate_pct_per_week !== null
                    ? `${data.phase.target_rate_pct_per_week > 0 ? '+' : ''}${num(data.phase.target_rate_pct_per_week, 2)}` : '--'}
                </span>
                <span className="stat-note">% bodyweight / week</span>
              </div>
              <div className="stat">
                <span className="stat-label">Change so far</span>
                <span className="stat-value">
                  {data.total_change_kg !== null && data.total_change_kg !== undefined
                    ? `${data.total_change_kg > 0 ? '+' : ''}${num(data.total_change_kg, 1)}` : '--'}
                </span>
                <span className="stat-note">kg since start</span>
              </div>
            </div>

            <p className="list-meta" style={{ marginTop: 12 }}>{data.verdict?.detail}</p>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 12 }}>Log a weigh-in</h2>
            <p className="state-body" style={{ marginBottom: 12 }}>
              Weigh in on the same days each week - first thing in the morning, before eating - so the
              weekly averages compare like with like. Every weigh-in you add appears in the chart below.
            </p>
            <div className="grid grid-2">
              <TextField
                label="Date" type="date" value={weighIn.measured_on}
                onChange={(v) => setWeighIn({ ...weighIn, measured_on: v })}
              />
              <NumberField
                label="Weight" value={weighIn.weight_kg}
                onChange={(v) => setWeighIn({ ...weighIn, weight_kg: v })}
                min={20} max={400} placeholder="82.4" hint="Kilograms"
              />
            </div>
            <div className="row" style={{ marginTop: 16 }}>
              <Button onClick={() => logWeight.mutate()} disabled={logWeight.isPending || !weighIn.weight_kg}>
                {logWeight.isPending ? 'Saving...' : 'Save weigh-in'}
              </Button>
              {logWeight.isSuccess ? <p className="form-ok">Weigh-in saved.</p> : null}
              {logWeight.isError ? (
                <p className="form-error">
                  {logWeight.error instanceof Error ? logWeight.error.message : 'Could not save'}
                </p>
              ) : null}
            </div>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <div className="section-title">
              <h2>Bodyweight trend</h2>
              <Segmented
                label="Weight chart resolution" value={granularity}
                onChange={setGranularity} options={GRANULARITY_OPTIONS}
              />
            </div>
            {series.isLoading ? <LoadingState what="your weight history" /> : null}
            {series.data && series.data.count >= 2 ? (
              <>
                <LineChart
                  points={points}
                  label={`${granularity === 'daily' ? 'Daily weight' : granularity === 'weekly' ? 'Weekly average weight' : 'Monthly average weight'}`}
                  unit=" kg" formatValue={(v) => v.toFixed(1)}
                />
                {series.data.change_kg !== null ? (
                  <p className="list-meta" style={{ marginTop: 8 }}>
                    {series.data.change_kg > 0 ? 'Up' : 'Down'} {num(Math.abs(series.data.change_kg), 1)} kg
                    over the last {series.data.months} months ({num(series.data.first_kg, 1)} kg to{' '}
                    {num(series.data.latest_kg, 1)} kg).
                  </p>
                ) : null}
              </>
            ) : null}
            {series.data && series.data.count < 2 ? (
              <EmptyState
                title="Not enough weigh-ins yet"
                body="Log at least two weigh-ins and your trend appears here. The chart needs two points before a line means anything."
              />
            ) : null}
            <DataSourceNote>{series.data?.note ?? 'Only real weigh-ins are shown; days with no entry are left out rather than filled in.'}</DataSourceNote>
          </Card>

          {data.suggestion ? (
            <Card style={{ marginTop: 24 }}>
              <h2 style={{ marginBottom: 12 }}>Calorie adjustment</h2>
              {data.suggestion.suggested_kcal !== 0 ? (
                <>
                  <Metric
                    value={`${data.suggestion.suggested_kcal > 0 ? '+' : ''}${num(data.suggestion.suggested_kcal)}`}
                    unit="kcal/day"
                    label="Suggested change"
                    tone="accent"
                  />
                  <p className="list-meta" style={{ marginTop: 12 }}>{data.suggestion.reason}</p>
                  <div className="row" style={{ marginTop: 16 }}>
                    <Button
                      onClick={() => accept.mutate(data.suggestion!.suggested_kcal)}
                      disabled={accept.isPending}
                    >
                      {accept.isPending ? 'Applying...' : 'Accept adjustment'}
                    </Button>
                    <span className="list-meta">
                      Current adjustment: {data.phase.kcal_adjustment > 0 ? '+' : ''}{num(data.phase.kcal_adjustment)} kcal/day
                    </span>
                  </div>
                  {accept.isError ? (
                    <p className="form-error" style={{ marginTop: 8 }}>
                      {accept.error instanceof Error ? accept.error.message : 'Could not apply'}
                    </p>
                  ) : null}
                </>
              ) : (
                <p className="state-body">{data.suggestion.reason}</p>
              )}
            </Card>
          ) : null}

          {data.refeed_due ? (
            <Card style={{ marginTop: 24 }}>
              <div className="section-title">
                <h2>{data.refeed_due.label}</h2>
                <Chip tone="accent">{data.refeed_due.kind === 'diet_break' ? 'Diet break' : 'Refeed'}</Chip>
              </div>
              <p className="state-body">{data.refeed_due.detail}</p>
            </Card>
          ) : null}

          <Card style={{ marginTop: 24 }}>
            <div className="section-title">
              <h2>Phase settings</h2>
              <Button variant="ghost" onClick={() => end.mutate()} disabled={end.isPending}>
                {end.isPending ? 'Ending...' : 'End phase'}
              </Button>
            </div>
            <p className="list-meta">
              Target weight: {data.phase.target_weight_kg !== null ? kg(data.phase.target_weight_kg) : 'not set'}
              {targetWeeks ? ` - Target duration: ${targetWeeks} weeks` : ''}
              {data.phase.notes ? ` - ${data.phase.notes}` : ''}
            </p>
            <div style={{ marginTop: 16 }}>
              <Legend title="What each phase means" items={PHASE_LEGEND}
                note="Rates are a percentage of bodyweight per week, because the same kilogram is a different amount of change for two different people." />
            </div>
          </Card>
        </>
      ) : null}

      <Card style={{ marginTop: 24 }}>
        <h2 style={{ marginBottom: 12 }}>{active ? 'Start a different phase' : 'Start a phase'}</h2>
        <div className="grid grid-2">
          <SelectField
            label="Phase" value={form.phase_type}
            onChange={(v) => setForm({ ...form, phase_type: v })}
            options={PHASES}
          />
          <NumberField
            label="Target weight" value={form.target_weight_kg}
            onChange={(v) => setForm({ ...form, target_weight_kg: v })}
            min={20} max={400} placeholder="80" hint="Kilograms, optional"
          />
          <NumberField
            label="Target rate" value={form.target_rate_pct_per_week}
            onChange={(v) => setForm({ ...form, target_rate_pct_per_week: v })}
            min={-2} max={2} step="0.05" placeholder="-0.7"
            hint="% of bodyweight per week (negative to lose)"
          />
          <NumberField
            label="Target duration" value={form.target_weeks}
            onChange={(v) => setForm({ ...form, target_weeks: v })}
            min={1} max={104} placeholder="12"
            hint="Weeks (e.g. a 12-week prep block)"
          />
          <TextField
            label="Notes" value={form.notes}
            onChange={(v) => setForm({ ...form, notes: v })}
            placeholder="Contest prep block 1"
          />
        </div>
        <div className="row" style={{ marginTop: 16 }}>
          <Button onClick={() => start.mutate()} disabled={start.isPending}>
            {start.isPending ? 'Starting...' : active ? 'Switch phase' : 'Start phase'}
          </Button>
          {active ? <span className="list-meta">Starting a new phase closes the current one.</span> : null}
          {start.isError ? (
            <p className="form-error">{start.error instanceof Error ? start.error.message : 'Could not start'}</p>
          ) : null}
        </div>
      </Card>

      <Card style={{ marginTop: 24 }}>
        <h2 style={{ marginBottom: 12 }}>Refeeds and diet breaks</h2>
        <p className="state-body" style={{ marginBottom: 12 }}>
          A refeed is a planned day or two at maintenance calories during a cut. A diet break is a
          longer week or two at maintenance. Log them here so the phase history is complete.
        </p>
        <div className="grid grid-2">
          <TextField
            label="Date" type="date" value={refeed.occurred_on}
            onChange={(v) => setRefeed({ ...refeed, occurred_on: v })}
          />
          <SelectField
            label="Type" value={refeed.kind}
            onChange={(v) => setRefeed({ ...refeed, kind: v })}
            options={[
              { value: 'refeed', label: 'Refeed (1-2 days)' },
              { value: 'diet_break', label: 'Diet break (1-2 weeks)' }
            ]}
          />
          <NumberField
            label="Days" value={refeed.days}
            onChange={(v) => setRefeed({ ...refeed, days: v })}
            min={1} max={21} placeholder="1"
          />
          <TextField
            label="Notes" value={refeed.notes}
            onChange={(v) => setRefeed({ ...refeed, notes: v })}
            placeholder="Optional"
          />
        </div>
        <div className="row" style={{ marginTop: 16 }}>
          <Button onClick={() => addRefeed.mutate()} disabled={addRefeed.isPending}>
            {addRefeed.isPending ? 'Saving...' : 'Log refeed'}
          </Button>
          {addRefeed.isError ? (
            <p className="form-error">{addRefeed.error instanceof Error ? addRefeed.error.message : 'Could not save'}</p>
          ) : null}
        </div>

        {refeeds.data && refeeds.data.length > 0 ? (
          <ul className="list" style={{ marginTop: 16 }}>
            {refeeds.data.map((r) => (
              <li className="list-row" key={r.id}>
                <div className="list-main">
                  <span className="list-title">
                    {r.kind === 'diet_break' ? 'Diet break' : 'Refeed'}
                  </span>
                  <span className="list-meta">
                    {shortDate(r.occurred_on)} - {r.days} {r.days === 1 ? 'day' : 'days'}
                    {r.notes ? ` - ${r.notes}` : ''}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </Card>
    </>
  )
}
