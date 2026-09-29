import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Legend, NumberField, SelectField, TextField } from '../components/ui'
import { api } from '../lib/api'
import { localTimezone } from '../lib/format'

const SEX = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'unspecified', label: 'Prefer not to say' }
]
const EXPERIENCE = [
  { value: 'beginner', label: 'Beginner (under 1 year)' },
  { value: 'intermediate', label: 'Intermediate (1-3 years)' },
  { value: 'advanced', label: 'Advanced (3+ years)' }
]
const ACTIVITY = [
  { value: 'sedentary', label: 'Sedentary - desk work, little movement' },
  { value: 'light', label: 'Light - some walking or 1-2 sessions a week' },
  { value: 'moderate', label: 'Moderate - 3-4 sessions a week' },
  { value: 'active', label: 'Active - 5-6 sessions a week' },
  { value: 'very_active', label: 'Very active - daily training or physical work' }
]
const GOALS = [
  { value: 'cut', label: 'Cut - lose fat' },
  { value: 'maintain', label: 'Maintain' },
  { value: 'lean_bulk', label: 'Lean bulk - slow gain' },
  { value: 'bulk', label: 'Bulk - faster gain' },
  { value: 'strength', label: 'Strength focus' },
  { value: 'custom', label: 'Custom' }
]

/* What each activity level means, in plain words. This is the multiplier applied
   to your BMR, so the choice visibly changes your calorie target. */
const ACTIVITY_LEGEND = [
  { key: 'Sedentary', label: 'Desk job, little walking. BMR x 1.2.' },
  { key: 'Light', label: 'Some walking, or 1-2 training sessions a week. BMR x 1.375.' },
  { key: 'Moderate', label: '3-4 training sessions a week. BMR x 1.55.' },
  { key: 'Active', label: '5-6 training sessions a week. BMR x 1.725.' },
  { key: 'Very active', label: 'Daily training or physical work. BMR x 1.9.' }
]

export default function OnboardingPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [form, setForm] = useState({
    display_name: '', birth_date: '', sex: 'male', height_cm: '',
    activity_level: 'moderate', training_experience: 'intermediate',
    training_frequency: '4', session_minutes: '75', goal_type: 'maintain'
  })
  const set = (k: keyof typeof form) => (v: string) => setForm((f) => ({ ...f, [k]: v }))

  const save = useMutation({
    mutationFn: async () => {
      await api.patch('/profile', {
        display_name: form.display_name || undefined,
        birth_date: form.birth_date || undefined,
        sex: form.sex,
        height_cm: form.height_cm ? Number(form.height_cm) : undefined,
        activity_level: form.activity_level,
        training_experience: form.training_experience,
        training_frequency: form.training_frequency ? Number(form.training_frequency) : undefined,
        session_minutes: form.session_minutes ? Number(form.session_minutes) : undefined,
        timezone: localTimezone()
      })
      await api.post('/profile/goals', { goal_type: form.goal_type })
    },
    onSuccess: async () => {
      await qc.invalidateQueries()
      navigate('/')
    }
  })

  return (
    <>
      <header className="page-head">
        <h1>Set up your athlete profile</h1>
        <p className="page-sub">
          These values feed your calorie and recovery estimates. You can change any of them later.
        </p>
      </header>

      <div className="grid grid-2">
        <Card>
          <h2 style={{ marginBottom: 16 }}>About you</h2>
          <div className="stack">
            <TextField label="Name" value={form.display_name} onChange={set('display_name')} placeholder="Your Name" />
            <TextField label="Date of birth" type="date" value={form.birth_date} onChange={set('birth_date')}
              hint="Used only to estimate your resting energy expenditure." />
            <SelectField label="Biological sex" value={form.sex} onChange={set('sex')} options={SEX}
              hint="The energy equation differs by sex. Choose what fits your physiology." />
            <NumberField label="Height" value={form.height_cm} onChange={set('height_cm')} min={100} max={250}
              placeholder="178" hint="Centimetres." />
          </div>
        </Card>

        <Card>
          <h2 style={{ marginBottom: 16 }}>Training and goal</h2>
          <div className="stack">
            <SelectField label="Training experience" value={form.training_experience}
              onChange={set('training_experience')} options={EXPERIENCE} />
            <NumberField label="Sessions per week" value={form.training_frequency}
              onChange={set('training_frequency')} min={0} max={14} placeholder="4" />
            <NumberField label="Typical session length" value={form.session_minutes}
              onChange={set('session_minutes')} min={15} max={240} placeholder="75" hint="Minutes." />
            <SelectField label="Daily activity outside training" value={form.activity_level}
              onChange={set('activity_level')} options={ACTIVITY}
              hint={ACTIVITY.find((a) => a.value === form.activity_level)?.label} />
            <Legend title="What the activity levels mean" items={ACTIVITY_LEGEND}
              note="Training frequency is set above; this is what you do outside your sessions." />
            <SelectField label="Current goal" value={form.goal_type} onChange={set('goal_type')} options={GOALS} />
          </div>
        </Card>
      </div>

      <div className="row" style={{ marginTop: 24 }}>
        <Button onClick={() => save.mutate()} disabled={save.isPending}>
          {save.isPending ? 'Saving...' : 'Save and continue'}
        </Button>
        {save.isError ? (
          <p className="form-error" role="alert">
            {save.error instanceof Error ? save.error.message : 'Could not save your profile'}
          </p>
        ) : null}
      </div>
      <p className="source-note" style={{ marginTop: 16 }}>
        Add your weight under Account, then TRINITY can estimate your daily energy needs.
      </p>
    </>
  )
}
