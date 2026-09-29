/** Profile, body metrics, goals, preferences, theme, privacy (spec 8, 9, 59, 64, 65). */
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button, Card, Chip, DataSourceNote, EmptyState, ErrorState, Legend, LoadingState,
  NumberField, Segmented, SelectField, TextField
} from '../components/ui'
import { LineChart } from '../components/charts'
import { api } from '../lib/api'
import { isoDate, kg, num, shortDate } from '../lib/format'
import { useAuth } from '../stores/auth'
import { usePrefs } from '../stores/prefs'
import type { BodyMetric, Goal, Profile, ProgressPhoto } from '../lib/types'

const GOALS = [
  { value: 'cut', label: 'Cut - lose fat' },
  { value: 'maintain', label: 'Maintain' },
  { value: 'lean_bulk', label: 'Lean bulk' },
  { value: 'bulk', label: 'Bulk' },
  { value: 'strength', label: 'Strength' },
  { value: 'custom', label: 'Custom' }
]

/* Same legend as onboarding: the activity level is a BMR multiplier, so its
   meaning must be visible wherever the user can change it. */
const ACTIVITY_LEGEND = [
  { key: 'Sedentary', label: 'Desk job, little walking. BMR x 1.2.' },
  { key: 'Light', label: 'Some walking, or 1-2 training sessions a week. BMR x 1.375.' },
  { key: 'Moderate', label: '3-4 training sessions a week. BMR x 1.55.' },
  { key: 'Active', label: '5-6 training sessions a week. BMR x 1.725.' },
  { key: 'Very active', label: 'Daily training or physical work. BMR x 1.9.' }
]

export default function AccountPage() {
  const qc = useQueryClient()
  const me = useAuth((s) => s.me)
  const logout = useAuth((s) => s.logout)
  const themePref = usePrefs((s) => s.themePref)
  const setTheme = usePrefs((s) => s.setTheme)

  const profile = useQuery({ queryKey: ['profile'], queryFn: () => api.get<Profile>('/profile') })
  const goals = useQuery({ queryKey: ['goals'], queryFn: () => api.get<Goal[]>('/profile/goals') })
  const metrics = useQuery({ queryKey: ['metrics'], queryFn: () => api.get<BodyMetric[]>('/profile/metrics') })

  const [form, setForm] = useState({ display_name: '', birth_date: '', sex: '', height_cm: '', body_fat_pct: '', activity_level: '', units: 'metric' })
  const [metric, setMetric] = useState({
    measured_on: isoDate(), weight_kg: '', body_fat_pct: '', waist_cm: '',
    neck_cm: '', shoulder_cm: '', chest_cm: '', arm_cm: '', forearm_cm: '',
    thigh_cm: '', hip_cm: '', calf_cm: ''
  })

  useEffect(() => {
    if (profile.data) {
      setForm({
        display_name: profile.data.display_name ?? '',
        birth_date: profile.data.birth_date ?? '',
        sex: profile.data.sex ?? '',
        height_cm: profile.data.height_cm?.toString() ?? '',
        body_fat_pct: profile.data.body_fat_pct?.toString() ?? '',
        activity_level: profile.data.activity_level ?? '',
        units: profile.data.units ?? 'metric'
      })
    }
  }, [profile.data])

  const saveProfile = useMutation({
    mutationFn: () => api.patch('/profile', {
      display_name: form.display_name || undefined,
      birth_date: form.birth_date || undefined,
      sex: form.sex || undefined,
      height_cm: form.height_cm ? Number(form.height_cm) : undefined,
      body_fat_pct: form.body_fat_pct ? Number(form.body_fat_pct) : undefined,
      activity_level: form.activity_level || undefined,
      units: form.units
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['profile'] })
      await qc.invalidateQueries({ queryKey: ['tdee'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
    }
  })

  const saveMetric = useMutation({
    mutationFn: () => api.post('/profile/metrics', {
      measured_on: metric.measured_on,
      weight_kg: metric.weight_kg ? Number(metric.weight_kg) : undefined,
      body_fat_pct: metric.body_fat_pct ? Number(metric.body_fat_pct) : undefined,
      waist_cm: metric.waist_cm ? Number(metric.waist_cm) : undefined,
      neck_cm: metric.neck_cm ? Number(metric.neck_cm) : undefined,
      shoulder_cm: metric.shoulder_cm ? Number(metric.shoulder_cm) : undefined,
      chest_cm: metric.chest_cm ? Number(metric.chest_cm) : undefined,
      arm_cm: metric.arm_cm ? Number(metric.arm_cm) : undefined,
      forearm_cm: metric.forearm_cm ? Number(metric.forearm_cm) : undefined,
      thigh_cm: metric.thigh_cm ? Number(metric.thigh_cm) : undefined,
      hip_cm: metric.hip_cm ? Number(metric.hip_cm) : undefined,
      calf_cm: metric.calf_cm ? Number(metric.calf_cm) : undefined
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['metrics'] })
      await qc.invalidateQueries({ queryKey: ['tdee'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
      setMetric({
        measured_on: isoDate(), weight_kg: '', body_fat_pct: '', waist_cm: '',
        neck_cm: '', shoulder_cm: '', chest_cm: '', arm_cm: '', forearm_cm: '',
        thigh_cm: '', hip_cm: '', calf_cm: ''
      })
    }
  })

  const saveGoal = useMutation({
    mutationFn: (goal_type: string) => api.post('/profile/goals', { goal_type }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['goals'] })
      await qc.invalidateQueries({ queryKey: ['tdee'] })
    }
  })

  const weightSeries = [...(metrics.data ?? [])]
    .reverse()
    .filter((m) => m.weight_kg !== null)
    .map((m) => ({ x: shortDate(m.measured_on), y: m.weight_kg }))

  const activeGoal = goals.data?.find((g) => g.is_active)

  return (
    <>
      <header className="page-head">
        <h1>Account</h1>
        <p className="page-sub">Your profile, body metrics, goals and preferences.</p>
      </header>

      {profile.isLoading ? <LoadingState what="your profile" /> : null}
      {profile.isError ? (
        <ErrorState message={profile.error instanceof Error ? profile.error.message : 'Could not load profile'} onRetry={() => void profile.refetch()} />
      ) : null}

      {profile.data ? (
        <>
          <Card>
            <h2 style={{ marginBottom: 16 }}>Athlete profile</h2>
            <div className="grid grid-2">
              <TextField label="Name" value={form.display_name} onChange={(v) => setForm({ ...form, display_name: v })} />
              <TextField label="Date of birth" type="date" value={form.birth_date} onChange={(v) => setForm({ ...form, birth_date: v })} />
              <SelectField
                label="Biological sex" value={form.sex} onChange={(v) => setForm({ ...form, sex: v })}
                options={[
                  { value: '', label: 'Not set' },
                  { value: 'male', label: 'Male' },
                  { value: 'female', label: 'Female' },
                  { value: 'unspecified', label: 'Prefer not to say' }
                ]}
              />
              <NumberField label="Height" value={form.height_cm} onChange={(v) => setForm({ ...form, height_cm: v })} min={100} max={250} hint="Centimetres" />
              <NumberField label="Body fat" value={form.body_fat_pct} onChange={(v) => setForm({ ...form, body_fat_pct: v })} min={2} max={70} hint="Percent, optional" />
              <SelectField
                label="Activity level" value={form.activity_level} onChange={(v) => setForm({ ...form, activity_level: v })}
                options={[
                  { value: '', label: 'Not set' },
                  { value: 'sedentary', label: 'Sedentary' },
                  { value: 'light', label: 'Light' },
                  { value: 'moderate', label: 'Moderate' },
                  { value: 'active', label: 'Active' },
                  { value: 'very_active', label: 'Very active' }
                ]}
              />
            </div>
            <div style={{ marginTop: 16 }}>
              <Legend title="What the activity levels mean" items={ACTIVITY_LEGEND}
                note="Your activity level scales your BMR into a daily energy estimate." />
            </div>
            <div className="row" style={{ marginTop: 16 }}>
              <Button onClick={() => saveProfile.mutate()} disabled={saveProfile.isPending}>
                {saveProfile.isPending ? 'Saving...' : 'Save profile'}
              </Button>
              {saveProfile.isSuccess ? <p className="form-ok">Profile saved.</p> : null}
              {saveProfile.isError ? <p className="form-error">{saveProfile.error instanceof Error ? saveProfile.error.message : 'Could not save'}</p> : null}
            </div>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 16 }}>Body metrics</h2>
            <div className="grid grid-2">
              <TextField label="Date" type="date" value={metric.measured_on} onChange={(v) => setMetric({ ...metric, measured_on: v })} />
              <NumberField label="Weight" value={metric.weight_kg} onChange={(v) => setMetric({ ...metric, weight_kg: v })} min={20} max={400} placeholder="77.5" hint="Kilograms" />
              <NumberField label="Body fat" value={metric.body_fat_pct} onChange={(v) => setMetric({ ...metric, body_fat_pct: v })} min={2} max={70} placeholder="14.5" hint="Percent, optional" />
              <NumberField label="Waist" value={metric.waist_cm} onChange={(v) => setMetric({ ...metric, waist_cm: v })} min={40} max={200} placeholder="82" hint="Centimetres, optional" />
              <NumberField label="Neck" value={metric.neck_cm} onChange={(v) => setMetric({ ...metric, neck_cm: v })} min={15} max={80} placeholder="38" hint="cm, optional" />
              <NumberField label="Shoulders" value={metric.shoulder_cm} onChange={(v) => setMetric({ ...metric, shoulder_cm: v })} min={50} max={220} placeholder="120" hint="cm, optional" />
              <NumberField label="Chest" value={metric.chest_cm} onChange={(v) => setMetric({ ...metric, chest_cm: v })} min={40} max={220} placeholder="102" hint="cm, optional" />
              <NumberField label="Arm" value={metric.arm_cm} onChange={(v) => setMetric({ ...metric, arm_cm: v })} min={15} max={90} placeholder="38" hint="cm, optional" />
              <NumberField label="Forearm" value={metric.forearm_cm} onChange={(v) => setMetric({ ...metric, forearm_cm: v })} min={12} max={60} placeholder="30" hint="cm, optional" />
              <NumberField label="Thigh" value={metric.thigh_cm} onChange={(v) => setMetric({ ...metric, thigh_cm: v })} min={25} max={120} placeholder="60" hint="cm, optional" />
              <NumberField label="Hip" value={metric.hip_cm} onChange={(v) => setMetric({ ...metric, hip_cm: v })} min={50} max={220} placeholder="96" hint="cm, optional" />
              <NumberField label="Calf" value={metric.calf_cm} onChange={(v) => setMetric({ ...metric, calf_cm: v })} min={15} max={80} placeholder="39" hint="cm, optional" />
            </div>
            <div className="row" style={{ marginTop: 16 }}>
              <Button onClick={() => saveMetric.mutate()} disabled={saveMetric.isPending || metric.weight_kg === ''}>
                {saveMetric.isPending ? 'Saving...' : 'Save measurement'}
              </Button>
              {saveMetric.isSuccess ? <p className="form-ok">Measurement saved.</p> : null}
            </div>

            <div style={{ marginTop: 24 }}>
              {weightSeries.length >= 2 ? (
                <LineChart points={weightSeries} label="Weight trend" unit=" kg" formatValue={(v) => v.toFixed(1)} />
              ) : metrics.data && metrics.data.length > 0 ? (
                <p className="list-meta">One measurement recorded. A trend line needs at least two.</p>
              ) : (
                <EmptyState title="No measurements yet" body="Record your weight to start tracking the trend over time." />
              )}
            </div>

            {metrics.data && metrics.data.length > 0 ? (
              <ul className="list" style={{ marginTop: 24 }}>
                {metrics.data.slice(0, 8).map((m) => (
                  <li className="list-row" key={m.id}>
                    <div className="list-main">
                      <span className="list-title">{shortDate(m.measured_on)}</span>
                      <span className="list-meta">
                        {m.body_fat_pct !== null ? `Body fat ${num(m.body_fat_pct, 1)}%` : ''}
                        {m.waist_cm !== null ? ` Waist ${num(m.waist_cm, 1)} cm` : ''}
                      </span>
                    </div>
                    <span className="list-value">{kg(m.weight_kg)}</span>
                  </li>
                ))}
              </ul>
            ) : null}
            <DataSourceNote>
              Body weight moves with water, food and glycogen as well as tissue. A single change does not
              tell you what changed; only the trend over weeks does.
            </DataSourceNote>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 16 }}>Goal</h2>
            <div className="row">
              {GOALS.map((g) => (
                <Button
                  key={g.value}
                  variant={activeGoal?.goal_type === g.value ? 'primary' : 'ghost'}
                  onClick={() => saveGoal.mutate(g.value)}
                  disabled={saveGoal.isPending}
                >
                  {g.label}
                </Button>
              ))}
            </div>
            {activeGoal ? (
              <p className="list-meta" style={{ marginTop: 12 }}>
                Active since {shortDate(activeGoal.started_on)}. Your goal shapes the calorie and macro targets.
              </p>
            ) : null}
            {goals.data && goals.data.length > 1 ? (
              <div style={{ marginTop: 16 }}>
                <p className="list-meta">Previous goals</p>
                <ul className="list">
                  {goals.data.filter((g) => !g.is_active).slice(0, 5).map((g) => (
                    <li className="list-row" key={g.id}>
                      <span className="list-title">{g.goal_type.replace('_', ' ')}</span>
                      <span className="list-meta">{shortDate(g.started_on)} to {g.ended_on ? shortDate(g.ended_on) : 'now'}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </Card>

          <ProgressPhotos />

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 16 }}>Appearance</h2>
            <p className="state-body" style={{ marginBottom: 12 }}>
              Automatic follows your device's local time: light from 06:00 to 17:59, dark from 18:00 to 05:59.
            </p>
            <Segmented
              label="Theme" value={themePref} onChange={setTheme}
              options={[
                { value: 'auto', label: 'Automatic' },
                { value: 'day', label: 'Day' },
                { value: 'night', label: 'Night' }
              ]}
            />
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 12 }}>Connected health data</h2>
            <p className="state-body" style={{ marginBottom: 12 }}>
              Apple Health and Health Connect sync is not implemented yet. Nothing is read from your device
              without your explicit permission, and manual entry covers every metric in the meantime.
            </p>
            <Chip tone="neutral">Not available yet</Chip>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 12 }}>Account and privacy</h2>
            <p className="list-meta" style={{ marginBottom: 12 }}>Signed in as {me?.email}</p>
            <p className="state-body" style={{ marginBottom: 16 }}>
              Your data is private to your account. Requests for your data are scoped to your user id on the
              server, and passwords are stored only as Argon2 hashes.
            </p>
            <Button variant="danger" onClick={logout}>Sign out</Button>
          </Card>
        </>
      ) : null}
    </>
  )
}


/**
 * Progress photos. The camera is the one record of shape change a scale and a
 * tape cannot give; files are stored privately and only the owner's own token
 * can fetch them.
 */
function ProgressPhotos() {
  const qc = useQueryClient()
  const photos = useQuery({
    queryKey: ['photos'],
    queryFn: () => api.get<ProgressPhoto[]>('/profile/photos')
  })
  const [pose, setPose] = useState('front')
  const [takenOn, setTakenOn] = useState(isoDate())
  const [weight, setWeight] = useState('')
  const [notes, setNotes] = useState('')
  const [file, setFile] = useState<File | null>(null)

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Choose a photo first')
      const form = new FormData()
      form.append('file', file)
      form.append('taken_on', takenOn)
      form.append('pose', pose)
      if (weight) form.append('weight_kg', weight)
      if (notes.trim()) form.append('notes', notes.trim())
      return api.upload<ProgressPhoto>('/profile/photos', form)
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['photos'] })
      setFile(null); setWeight(''); setNotes('')
    }
  })

  const remove = useMutation({
    mutationFn: (id: number) => api.del(`/profile/photos/${id}`),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['photos'] }) }
  })

  return (
    <Card style={{ marginTop: 24 }}>
      <h2 style={{ marginBottom: 12 }}>Progress photos</h2>
      <p className="state-body" style={{ marginBottom: 16 }}>
        Photos are stored privately and only ever returned to your own account. They show shape
        change that the scale cannot.
      </p>

      <div className="grid grid-2">
        <TextField label="Date" type="date" value={takenOn} onChange={setTakenOn} />
        <SelectField
          label="Pose" value={pose} onChange={setPose}
          options={[
            { value: 'front', label: 'Front' },
            { value: 'side', label: 'Side' },
            { value: 'back', label: 'Back' },
            { value: 'other', label: 'Other' }
          ]}
        />
        <NumberField label="Weight" value={weight} onChange={setWeight} min={20} max={400} placeholder="77.5" hint="Kilograms, optional" />
        <TextField label="Notes" value={notes} onChange={setNotes} placeholder="Morning, fasted" />
      </div>

      <label className="field" style={{ marginTop: 12 }}>
        <span className="field-label">Photo</span>
        <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>

      <div className="row" style={{ marginTop: 16 }}>
        <Button onClick={() => upload.mutate()} disabled={upload.isPending || !file}>
          {upload.isPending ? 'Uploading...' : 'Upload photo'}
        </Button>
        {upload.isError ? (
          <p className="form-error">{upload.error instanceof Error ? upload.error.message : 'Could not upload'}</p>
        ) : null}
      </div>

      {photos.data && photos.data.length > 0 ? (
        <ul className="list" style={{ marginTop: 24 }}>
          {photos.data.map((p) => (
            <li className="list-row" key={p.id}>
              <div className="list-main">
                <span className="list-title">{shortDate(p.taken_on)} - {p.pose}</span>
                <span className="list-meta">
                  {p.weight_kg !== null ? `${num(p.weight_kg, 1)} kg` : 'weight not recorded'}
                  {p.notes ? ` - ${p.notes}` : ''}
                </span>
              </div>
              <Button variant="ghost" onClick={() => remove.mutate(p.id)} disabled={remove.isPending}>
                Delete
              </Button>
            </li>
          ))}
        </ul>
      ) : (
        <div style={{ marginTop: 24 }}>
          <EmptyState title="No photos yet" body="Add a first photo to start a visual record of your progress." />
        </div>
      )}
    </Card>
  )
}
