/** Workout logging, previous-session memory, programs, PRs, calendar (spec 29-39). */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Chip, DataSourceNote, EmptyState, LoadingState, NumberField, Segmented, SelectField, TextField } from '../components/ui'
import { BarChart } from '../components/charts'
import { IconPlus } from '../components/icons'
import { api } from '../lib/api'
import { isoDate, num, shortDate } from '../lib/format'
import type {
  CalendarDay, Exercise, LastSession, MuscleVolume, PersonalRecord, Program,
  ProgressionAdvice, TrainingSummary, VolumeAnalysis, WorkoutSummary
} from '../lib/types'

interface DraftSet { set_index: number; weight_kg: string; reps: string; rir: string; set_type: string; is_warmup: boolean }
interface DraftExercise { exercise: Exercise; sets: DraftSet[]; notes: string }

const STATUS_TONE: Record<string, 'accent' | 'success' | 'warning' | 'danger' | 'neutral'> = {
  completed: 'success', modified: 'accent', skipped: 'warning', rest: 'neutral', none: 'neutral'
}

type Tab = 'log' | 'history' | 'programs' | 'volume'

/* How a set was taken changes what it means. RIR is the honest effort signal:
   reps left in the tank, not a guess at a percentage of a maximum. */
const SET_TYPES = [
  { value: 'normal', label: 'Normal' },
  { value: 'drop', label: 'Drop set' },
  { value: 'myo_rep', label: 'Myo-rep' },
  { value: 'rest_pause', label: 'Rest-pause' },
  { value: 'amrap', label: 'AMRAP' },
  { value: 'failure', label: 'To failure' }
]

const VOLUME_STATUS_TONE: Record<string, 'accent' | 'success' | 'warning' | 'danger' | 'neutral'> = {
  below_mev: 'warning', maintenance: 'neutral', optimal: 'success',
  above_mrv: 'danger', none: 'neutral'
}

const VOLUME_STATUS_LABEL: Record<string, string> = {
  below_mev: 'Below minimum', maintenance: 'Maintenance', optimal: 'Productive',
  above_mrv: 'Above recoverable', none: 'Not trained'
}

/* A personal record only means something if the user can read it at a glance.
   Each type gets a plain name, the unit its number is in, and a one-line
   explanation of what it measures - so "e1rm 112.5" becomes "Estimated 1RM -
   112.5 kg", which is what the number actually is. */
const PR_META: Record<string, { label: string; unit: string; explain: string }> = {
  weight: {
    label: 'Heaviest weight', unit: 'kg',
    explain: 'The heaviest load you have lifted for any set of this exercise.'
  },
  e1rm: {
    label: 'Estimated 1RM', unit: 'kg',
    explain: 'Your best estimated one-rep max, worked out from the weight and reps you logged. An estimate, not a tested max.'
  },
  volume: {
    label: 'Best session volume', unit: 'kg',
    explain: 'The most total weight moved in a single session: every rep times its load, added up.'
  },
  reps: {
    label: 'Most reps', unit: 'reps',
    explain: 'The highest number of reps you have completed in one set of this exercise.'
  }
}

const TABS: { value: Tab; label: string }[] = [
  { value: 'log', label: 'Log a workout' },
  { value: 'history', label: 'History' },
  { value: 'programs', label: 'Programs' },
  { value: 'volume', label: 'Weekly volume' }
]

export default function ExercisePage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('log')
  const [query, setQuery] = useState('')
  const [title, setTitle] = useState('')
  const [duration, setDuration] = useState('')
  const [notes, setNotes] = useState('')
  const [draft, setDraft] = useState<DraftExercise[]>([])
  const year = new Date().getFullYear()

  const exercises = useQuery({
    queryKey: ['exercises', query],
    queryFn: () => api.get<Exercise[]>(`/training/exercises?q=${encodeURIComponent(query)}&limit=60`)
  })
  const workouts = useQuery({
    queryKey: ['workouts'],
    queryFn: () => api.get<WorkoutSummary[]>('/training/workouts?days=90')
  })
  const programs = useQuery({
    queryKey: ['programs'],
    queryFn: () => api.get<Program[]>('/training/programs')
  })
  const prs = useQuery({
    queryKey: ['prs'],
    queryFn: () => api.get<PersonalRecord[]>('/training/prs')
  })
  const summary = useQuery({
    queryKey: ['training', 'summary', year],
    queryFn: () => api.get<TrainingSummary>(`/training/summary?year=${year}`)
  })
  const calendar = useQuery({
    queryKey: ['training', 'calendar', year],
    queryFn: () => api.get<CalendarDay[]>(`/training/calendar?year=${year}`)
  })
  const volume = useQuery({
    queryKey: ['training', 'volume'],
    queryFn: () => api.get<VolumeAnalysis>('/training/volume?weeks=4')
  })

  const saveWorkout = useMutation({
    mutationFn: () => api.post('/training/workouts', {
      performed_on: isoDate(),
      title: title.trim(),
      duration_min: duration ? Number(duration) : undefined,
      notes: notes.trim() || undefined,
      status: 'completed',
      exercises: draft.map((d, i) => ({
        exercise_id: d.exercise.id,
        position: i,
        notes: d.notes.trim() || undefined,
        sets: d.sets
          .filter((s) => s.reps !== '' || s.weight_kg !== '')
          .map((s) => ({
            set_index: s.set_index,
            weight_kg: s.weight_kg === '' ? undefined : Number(s.weight_kg),
            reps: s.reps === '' ? undefined : Number(s.reps),
            rir: s.rir === '' ? undefined : Number(s.rir),
            set_type: s.set_type || 'normal',
            is_warmup: s.is_warmup
          }))
      }))
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['workouts'] })
      await qc.invalidateQueries({ queryKey: ['prs'] })
      await qc.invalidateQueries({ queryKey: ['training'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
      setDraft([]); setTitle(''); setDuration(''); setNotes('')
    }
  })

  const exerciseById = useMemo(() => {
    const m = new Map<number, string>()
    exercises.data?.forEach((e) => m.set(e.id, e.name))
    return m
  }, [exercises.data])

  function addExercise(ex: Exercise) {
    setDraft((d) => [...d, { exercise: ex, sets: [{ set_index: 1, weight_kg: '', reps: '', rir: '', set_type: 'normal', is_warmup: false }], notes: '' }])
    setQuery('')
  }

  function updateSet(exIndex: number, setIndex: number, patch: Partial<DraftSet>) {
    setDraft((d) => d.map((ex, i) => i !== exIndex ? ex : {
      ...ex, sets: ex.sets.map((s, j) => j === setIndex ? { ...s, ...patch } : s)
    }))
  }

  return (
    <>
      <header className="page-head">
        <h1>Exercise</h1>
        <p className="page-sub">Log your sessions, see what you lifted last time, and track progress.</p>
      </header>

      <div style={{ marginBottom: 24 }}>
        <Segmented label="Exercise view" value={tab} onChange={setTab} options={TABS} />
      </div>

      {tab === 'log' ? (
        <>
          <Card>
            <h2 style={{ marginBottom: 16 }}>Today's session</h2>
            <div className="grid grid-2">
              <TextField label="Session name" required value={title} onChange={setTitle} placeholder="Upper body - push" />
              <NumberField label="Duration" value={duration} onChange={setDuration} min={5} max={300} placeholder="75" hint="Minutes (optional)" />
            </div>

            <div style={{ marginTop: 16 }}>
              <TextField label="Find an exercise" value={query} onChange={setQuery} placeholder="Bench press, squat, row..." />
              {exercises.data && query.trim().length >= 2 ? (
                <ul className="list" style={{ marginTop: 8 }}>
                  {exercises.data.slice(0, 6).map((ex) => (
                    <li className="list-row" key={ex.id}>
                      <div className="list-main">
                        <span className="list-title">{ex.name}</span>
                        <span className="list-meta">{ex.primary_muscle}{ex.equipment ? ` - ${ex.equipment}` : ''}</span>
                      </div>
                      <Button variant="ghost" onClick={() => addExercise(ex)}>
                        <IconPlus size={16} /> Add
                      </Button>
                    </li>
                  ))}
                  {exercises.data.length === 0 ? (
                    <li className="list-row"><span className="list-meta">No exercise matches that name.</span></li>
                  ) : null}
                </ul>
              ) : null}
            </div>
          </Card>

          {draft.map((d, exIndex) => (
            <ExerciseDraft
              key={`${d.exercise.id}-${exIndex}`}
              draft={d}
              onChangeSet={(setIndex, patch) => updateSet(exIndex, setIndex, patch)}
              onAddSet={() => setDraft((all) => all.map((ex, i) => i !== exIndex ? ex : {
                ...ex, sets: [...ex.sets, { set_index: ex.sets.length + 1, weight_kg: '', reps: '', rir: '', set_type: 'normal', is_warmup: false }]
              }))}
              onRemoveSet={(setIndex) => setDraft((all) => all.map((ex, i) => i !== exIndex ? ex : {
                ...ex, sets: ex.sets.filter((_, j) => j !== setIndex).map((s, j) => ({ ...s, set_index: j + 1 }))
              }))}
              onChangeNotes={(v) => setDraft((all) => all.map((ex, i) => i !== exIndex ? ex : { ...ex, notes: v }))}
              onRemove={() => setDraft((all) => all.filter((_, i) => i !== exIndex))}
            />
          ))}

          {draft.length > 0 ? (
            <Card style={{ marginTop: 24 }}>
              <TextField label="Session notes" value={notes} onChange={setNotes} placeholder="How did it feel? What to change next time?" />
              <div className="row" style={{ marginTop: 16 }}>
                <Button onClick={() => saveWorkout.mutate()} disabled={saveWorkout.isPending || !title.trim()}>
                  {saveWorkout.isPending ? 'Saving...' : 'Finish and save workout'}
                </Button>
                {saveWorkout.isSuccess ? <p className="form-ok">Workout saved.</p> : null}
                {saveWorkout.isError ? (
                  <p className="form-error">{saveWorkout.error instanceof Error ? saveWorkout.error.message : 'Could not save'}</p>
                ) : null}
              </div>
            </Card>
          ) : (
            <Card style={{ marginTop: 24 }}>
              <EmptyState
                title="No exercises added yet"
                body="Search for an exercise above to start building today's session."
              />
            </Card>
          )}
        </>
      ) : null}

      {tab === 'history' ? (
        <>
          {summary.data ? (
            <Card>
              <h2 style={{ marginBottom: 16 }}>{year} training summary</h2>
              <div className="stat-row">
                <div className="stat"><span className="stat-label">Sessions completed</span><span className="stat-value">{summary.data.completed}</span></div>
                <div className="stat"><span className="stat-label">Skipped</span><span className="stat-value">{summary.data.skipped}</span></div>
                <div className="stat"><span className="stat-label">Rest days</span><span className="stat-value">{summary.data.rest_days}</span></div>
                <div className="stat"><span className="stat-label">Average per week</span><span className="stat-value">{num(summary.data.avg_per_week, 1)}</span></div>
              </div>
              <p className="list-meta" style={{ marginTop: 12 }}>
                Consistency: {summary.data.consistency_pct !== null ? `${num(summary.data.consistency_pct, 1)}% of planned sessions` : 'no planned sessions to compare yet'}
              </p>
            </Card>
          ) : null}

          {calendar.data ? (
            <Card style={{ marginTop: 24 }}>
              <h2 style={{ marginBottom: 12 }}>Training calendar</h2>
              <Heatmap days={calendar.data} />
            </Card>
          ) : null}

          <PersonalRecords prs={prs.data} isLoading={prs.isLoading} exerciseById={exerciseById} />

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 12 }}>Recent workouts</h2>
            {workouts.isLoading ? <LoadingState what="workouts" /> : null}
            {workouts.data && workouts.data.length === 0 ? (
              <EmptyState title="No workouts logged yet" body="Log your first session and it appears here with its volume and PRs." />
            ) : null}
            {workouts.data && workouts.data.length > 0 ? (
              <ul className="list">
                {workouts.data.slice(0, 15).map((w) => (
                  <li className="list-row" key={w.id}>
                    <div className="list-main">
                      <span className="list-title">{w.title}</span>
                      <span className="list-meta">
                        {shortDate(w.performed_on)} - {w.exercises} exercises, {w.sets} sets
                        {w.duration_min ? ` - ${w.duration_min} min` : ''}
                      </span>
                    </div>
                    <Chip tone={STATUS_TONE[w.status] ?? 'neutral'}>{w.status}</Chip>
                  </li>
                ))}
              </ul>
            ) : null}
          </Card>
        </>
      ) : null}

      {tab === 'programs' ? (
        <>
          <Card>
            <h2 style={{ marginBottom: 12 }}>Your programs</h2>
            {programs.data && programs.data.length === 0 ? (
              <EmptyState
                title="No programs yet"
                body="Create a weekly split to plan your training days. Programs are yours to customise."
              />
            ) : (
              <ul className="list">
                {programs.data?.map((p) => (
                  <li className="list-row" key={p.id}>
                    <div className="list-main">
                      <span className="list-title">{p.name}</span>
                      <span className="list-meta">
                        {p.days.length} days{p.goal ? ` - ${p.goal}` : ''}
                        {p.source_name ? ` - based on ${p.source_name}` : ''}
                      </span>
                      <span className="list-meta">
                        {p.days.map((d) => d.is_rest ? 'Rest' : d.title).join(' / ')}
                      </span>
                      {p.attribution_note ? <span className="list-meta">{p.attribution_note}</span> : null}
                    </div>
                    {p.is_active ? <Chip tone="accent">Active</Chip> : (
                      <Button variant="ghost" onClick={() => activate(p.id)}>Set active</Button>
                    )}
                  </li>
                ))}
              </ul>
            )}
            <NewProgramForm onCreated={() => void qc.invalidateQueries({ queryKey: ['programs'] })} />
          </Card>
        </>
      ) : null}

      {tab === 'volume' ? (
        <VolumePanel volume={volume.data} isLoading={volume.isLoading} />
      ) : null}
    </>
  )

  async function activate(id: number) {
    await api.post(`/training/programs/${id}/activate`)
    await qc.invalidateQueries({ queryKey: ['programs'] })
    await qc.invalidateQueries({ queryKey: ['training'] })
  }
}

/** Personal records, grouped by exercise and written in plain language.
 *
 * The raw record_type (weight|e1rm|volume|reps) is jargon, so each record is
 * shown as a name, its number with the right unit, what it means, and when it
 * was set. Records are grouped under the exercise they belong to so a lifter
 * can see all of their bests for a movement in one place. */
function PersonalRecords({
  prs, isLoading, exerciseById
}: { prs?: PersonalRecord[]; isLoading: boolean; exerciseById: Map<number, string> }) {
  if (isLoading) return <Card style={{ marginTop: 24 }}><LoadingState what="your personal records" /></Card>
  if (!prs || prs.length === 0) {
    return (
      <Card style={{ marginTop: 24 }}>
        <h2 style={{ marginBottom: 12 }}>Personal records</h2>
        <EmptyState
          title="No personal records yet"
          body="Log a workout with weights and your bests appear here - heaviest set, best estimated 1RM and more, with the date you set them."
        />
      </Card>
    )
  }

  // Group by exercise, keeping the most recently achieved record first inside
  // each group so the newest achievement is what the eye lands on.
  const groups = new Map<number, PersonalRecord[]>()
  for (const pr of prs) {
    const list = groups.get(pr.exercise_id) ?? []
    list.push(pr)
    groups.set(pr.exercise_id, list)
  }
  const ordered = [...groups.entries()]
    .map(([id, list]) => ({
      id,
      name: list[0]?.exercise_name ?? exerciseById.get(id) ?? `Exercise ${id}`,
      list: [...list].sort((a, b) => b.achieved_on.localeCompare(a.achieved_on))
    }))
    .sort((a, b) => a.name.localeCompare(b.name))

  return (
    <Card style={{ marginTop: 24 }}>
      <h2 style={{ marginBottom: 4 }}>Personal records</h2>
      <p className="list-meta" style={{ marginBottom: 16 }}>
        Your best result for each exercise, and the day you set it. These update automatically when you
        log a session that beats them.
      </p>
      <div className="stack">
        {ordered.map((group) => (
          <div key={group.id}>
            <h3 style={{ marginBottom: 8 }}>{group.name}</h3>
            <ul className="list">
              {group.list.map((pr) => {
                const meta = PR_META[pr.record_type]
                const label = pr.label ?? meta?.label ?? pr.record_type
                const unit = pr.unit ?? meta?.unit ?? ''
                return (
                  <li className="list-row" key={pr.id}>
                    <div className="list-main">
                      <span className="list-title">{label}</span>
                      <span className="list-meta">
                        Set {shortDate(pr.achieved_on)}
                        {pr.detail ?? (meta ? ` - ${meta.explain}` : '')}
                      </span>
                    </div>
                    <span className="list-value">
                      {num(pr.value, 1)}{unit ? ` ${unit}` : ''}
                    </span>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </div>
      <DataSourceNote>
        Estimated 1RM uses the Epley formula and is an estimate, not a tested maximum. Records are kept
        only when a session actually beats the stored best.
      </DataSourceNote>
    </Card>
  )
}

function ExerciseDraft({
  draft, onChangeSet, onAddSet, onRemoveSet, onChangeNotes, onRemove
}: {
  draft: DraftExercise
  onChangeSet: (i: number, patch: Partial<DraftSet>) => void
  onAddSet: () => void
  onRemoveSet: (i: number) => void
  onChangeNotes: (v: string) => void
  onRemove: () => void
}) {
  const last = useQuery({
    queryKey: ['last-session', draft.exercise.id],
    queryFn: () => api.get<LastSession>(`/training/exercises/${draft.exercise.id}/last-session`)
  })

  return (
    <Card style={{ marginTop: 16 }}>
      <div className="section-title">
        <div>
          <h3>{draft.exercise.name}</h3>
          <p className="list-meta">{draft.exercise.primary_muscle}</p>
        </div>
        <Button variant="ghost" onClick={onRemove}>Remove</Button>
      </div>

      {last.data?.exists ? (
        <div className="card" style={{ background: 'var(--surface-2)', marginBottom: 16 }}>
          <p className="list-meta" style={{ marginBottom: 6 }}>
            Last session - {last.data.performed_on ? shortDate(last.data.performed_on) : ''}
            {last.data.volume ? ` - volume ${num(last.data.volume)} kg` : ''}
          </p>
          <p className="list-title num">
            {last.data.sets?.filter((s) => !s.is_warmup).map((s, i) => (
              <span key={i} style={{ marginRight: 12 }}>
                {s.weight_kg !== null ? `${num(s.weight_kg, 1)} kg` : 'bodyweight'} x {s.reps ?? '--'}
                {s.rir !== null && s.rir !== undefined ? ` @${s.rir} RIR` : ''}
              </span>
            ))}
          </p>
          {last.data.best_e1rm ? (
            <p className="list-meta" style={{ marginTop: 4 }}>Best estimated 1RM: {num(last.data.best_e1rm, 1)} kg</p>
          ) : null}
        </div>
      ) : null}

      <div className="stack">
        {draft.sets.map((s, i) => (
          <div className="row" key={i} style={{ alignItems: 'flex-end' }}>
            <span className="list-meta" style={{ minWidth: 44 }}>Set {s.set_index}</span>
            <div style={{ flex: '1 1 120px' }}>
              <NumberField label="Weight kg" value={s.weight_kg} onChange={(v) => onChangeSet(i, { weight_kg: v })} min={0} max={600} placeholder="80" />
            </div>
            <div style={{ flex: '1 1 100px' }}>
              <NumberField label="Reps" value={s.reps} onChange={(v) => onChangeSet(i, { reps: v })} min={0} max={200} placeholder="10" />
            </div>
            <div style={{ flex: '0 1 90px' }}>
              <NumberField label="RIR" value={s.rir} onChange={(v) => onChangeSet(i, { rir: v })} min={0} max={10} placeholder="2" hint="Reps left" />
            </div>
            <div style={{ flex: '1 1 140px' }}>
              <SelectField
                label="Set type" value={s.set_type}
                onChange={(v) => onChangeSet(i, { set_type: v })}
                options={SET_TYPES}
              />
            </div>
            <Button variant="ghost" onClick={() => onRemoveSet(i)}>Remove set</Button>
          </div>
        ))}
      </div>

      <div className="row" style={{ marginTop: 12 }}>
        <Button variant="ghost" onClick={onAddSet}><IconPlus size={16} /> Add set</Button>
      </div>

      <div style={{ marginTop: 12 }}>
        <TextField
          label="Exercise notes" value={draft.notes} onChange={onChangeNotes}
          placeholder="Felt strong. Try 82.5 kg next session."
        />
      </div>
    </Card>
  )
}

function Heatmap({ days }: { days: CalendarDay[] }) {
  return (
    <>
      <div className="heatmap" role="img" aria-label="Training activity by day for the year">
        {days.map((d) => (
          <span
            key={d.day} className={`heat-cell heat-${d.status}`}
            title={`${d.day}: ${d.title ? `${d.status} - ${d.title}` : d.status}`}
          />
        ))}
      </div>
      <div className="heat-legend" style={{ marginTop: 12 }}>
        <span><i className="heat-swatch heat-completed" /> Completed</span>
        <span><i className="heat-swatch heat-modified" /> Modified</span>
        <span><i className="heat-swatch heat-skipped" /> Skipped</span>
        <span><i className="heat-swatch heat-rest" /> Rest</span>
        <span><i className="heat-swatch heat-none" /> No entry</span>
      </div>
    </>
  )
}

function NewProgramForm({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [goal, setGoal] = useState('hypertrophy')
  const [days, setDays] = useState<string[]>(['', '', '', '', '', '', ''])
  const save = useMutation({
    mutationFn: () => api.post('/training/programs', {
      name: name.trim(),
      goal,
      days: days.map((t, i) => ({ day_index: i, title: t.trim() || 'Rest', is_rest: !t.trim() }))
    }),
    onSuccess: () => { setOpen(false); setName(''); onCreated() }
  })
  const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

  if (!open) {
    return <Button variant="ghost" style={{ marginTop: 16 }} onClick={() => setOpen(true)}>Create a program</Button>
  }
  return (
    <div className="stack" style={{ marginTop: 16 }}>
      <TextField label="Program name" value={name} onChange={setName} placeholder="Upper / Lower" />
      <SelectField
        label="Focus" value={goal} onChange={setGoal}
        options={[
          { value: 'hypertrophy', label: 'Hypertrophy' },
          { value: 'strength', label: 'Strength' },
          { value: 'general', label: 'General fitness' }
        ]}
      />
      <div className="grid grid-2">
        {dayNames.map((d, i) => (
          <TextField
            key={d} label={d} value={days[i]}
            onChange={(v) => setDays((all) => all.map((x, j) => j === i ? v : x))}
            placeholder="Rest"
          />
        ))}
      </div>
      <p className="field-hint">Leave a day blank for a rest day.</p>
      <div className="row">
        <Button onClick={() => save.mutate()} disabled={save.isPending || !name.trim()}>
          {save.isPending ? 'Saving...' : 'Save program'}
        </Button>
        <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
      </div>
      {save.isError ? <p className="form-error">{save.error instanceof Error ? save.error.message : 'Could not save'}</p> : null}
    </div>
  )
}


/** Weekly volume per muscle, against the MEV/MAV/MRV landmarks, plus a concrete
 *  next step for a chosen exercise. Both read only from logged sessions. */
function VolumePanel({ volume, isLoading }: { volume?: VolumeAnalysis; isLoading: boolean }) {
  const [adviceFor, setAdviceFor] = useState<Exercise | null>(null)

  if (isLoading) return <Card><LoadingState what="your weekly volume" /></Card>
  if (!volume) {
    return (
      <Card>
        <EmptyState title="No volume data yet" body="Log a workout and your weekly sets per muscle group appear here." />
      </Card>
    )
  }

  const trained = volume.muscles.filter((m) => m.sets_per_week > 0)
  const chart = trained.map((m) => ({ label: m.muscle.split(' ')[0], value: m.sets_per_week }))

  return (
    <>
      <Card>
        <h2 style={{ marginBottom: 12 }}>Weekly sets per muscle group</h2>
        <p className="list-meta" style={{ marginBottom: 16 }}>
          Averaged over the last {volume.weeks} weeks. {volume.trained_count} muscle groups trained.
        </p>
        {chart.length > 0 ? (
          <BarChart data={chart} label={`Sets per week per muscle (last ${volume.weeks} weeks)`} unit=" sets" />
        ) : (
          <EmptyState title="Nothing logged yet" body="Once you log workouts, your weekly sets per muscle appear here." />
        )}
      </Card>

      {trained.length > 0 ? (
        <Card style={{ marginTop: 24 }}>
          <h2 style={{ marginBottom: 12 }}>Against the landmarks</h2>
          <ul className="list">
            {trained.map((m: MuscleVolume) => (
              <li className="list-row" key={m.muscle}>
                <div className="list-main">
                  <span className="list-title">{m.muscle}</span>
                  <span className="list-meta">
                    MEV {m.mev} - MAV {m.mav} - MRV {m.mrv} sets/week
                  </span>
                </div>
                <span className="list-value">{num(m.sets_per_week, 1)}</span>
                <Chip tone={VOLUME_STATUS_TONE[m.status] ?? 'neutral'}>
                  {VOLUME_STATUS_LABEL[m.status] ?? m.status}
                </Chip>
              </li>
            ))}
          </ul>
          <DataSourceNote>{volume.note}</DataSourceNote>
        </Card>
      ) : null}

      <Card style={{ marginTop: 24 }}>
        <h2 style={{ marginBottom: 12 }}>Progressive overload advice</h2>
        <p className="state-body" style={{ marginBottom: 12 }}>
          Pick an exercise and see a concrete next step from your two most recent sessions.
        </p>
        <ExerciseAdvicePicker onPick={setAdviceFor} />
        {adviceFor ? <AdviceCard exercise={adviceFor} /> : null}
      </Card>
    </>
  )
}

function ExerciseAdvicePicker({ onPick }: { onPick: (e: Exercise) => void }) {
  const [q, setQ] = useState('')
  const exercises = useQuery({
    queryKey: ['exercises', 'advice', q],
    queryFn: () => api.get<Exercise[]>(`/training/exercises?q=${encodeURIComponent(q)}&limit=8`),
    enabled: q.trim().length >= 2
  })
  return (
    <>
      <TextField label="Find an exercise" value={q} onChange={setQ} placeholder="Bench press, squat..." />
      {exercises.data && exercises.data.length > 0 ? (
        <ul className="list" style={{ marginTop: 8 }}>
          {exercises.data.map((ex) => (
            <li className="list-row" key={ex.id}>
              <div className="list-main">
                <span className="list-title">{ex.name}</span>
                <span className="list-meta">{ex.primary_muscle}</span>
              </div>
              <Button variant="ghost" onClick={() => onPick(ex)}>Show advice</Button>
            </li>
          ))}
        </ul>
      ) : null}
    </>
  )
}

function AdviceCard({ exercise }: { exercise: Exercise }) {
  const advice = useQuery({
    queryKey: ['advice', exercise.id],
    queryFn: () => api.get<ProgressionAdvice>(`/training/progression/${exercise.id}/advice`)
  })
  if (advice.isLoading) return <div style={{ marginTop: 12 }}><LoadingState what="advice" /></div>
  if (!advice.data?.exists) {
    return <p className="list-meta" style={{ marginTop: 12 }}>{advice.data?.note ?? 'No history for this exercise yet.'}</p>
  }
  const label = advice.data.action === 'increase' ? 'Add load'
    : advice.data.action === 'baseline' ? 'Baseline' : 'Hold'
  const tone = advice.data.action === 'increase' ? 'accent' : 'neutral'
  return (
    <div className="card" style={{ background: 'var(--surface-2)', marginTop: 12 }}>
      <div className="section-title">
        <h3>{exercise.name}</h3>
        <Chip tone={tone}>{label}</Chip>
      </div>
      <p className="state-body">{advice.data.detail}</p>
      {advice.data.current ? (
        <p className="list-meta" style={{ marginTop: 8 }}>
          Last session: {advice.data.current.set_count} sets, best est. 1RM{' '}
          {advice.data.current.best_e1rm !== null ? `${num(advice.data.current.best_e1rm, 1)} kg` : '--'}
          {advice.data.current.avg_rir !== null ? `, avg ${advice.data.current.avg_rir} RIR` : ''}
        </p>
      ) : null}
    </div>
  )
}
