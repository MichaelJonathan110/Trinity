/** Food search, logging, daily totals, targets and TDEE (spec 10-22). */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button, Card, Chip, DataSourceNote, EmptyState, ErrorState, LoadingState,
  Metric, NumberField, Progress, SelectField, TextField
} from '../components/ui'
import { IconPlus, IconStar } from '../components/icons'
import { api } from '../lib/api'
import { isoDate, num } from '../lib/format'
import type { DayTotals, Food, TdeeResult } from '../lib/types'

const CATEGORIES = [
  { value: 'breakfast', label: 'Breakfast' },
  { value: 'lunch', label: 'Lunch' },
  { value: 'dinner', label: 'Dinner' },
  { value: 'snacks', label: 'Snacks' },
  { value: 'pre_workout', label: 'Pre-workout' },
  { value: 'post_workout', label: 'Post-workout' }
]

const SERVING_PRESETS = [50, 100, 150, 200, 250, 300]

export default function NutritionPage() {
  const qc = useQueryClient()
  const [day] = useState(isoDate())
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('breakfast')
  const [selected, setSelected] = useState<Food | null>(null)
  const [grams, setGrams] = useState('100')
  const [showTargets, setShowTargets] = useState(false)

  const totals = useQuery({
    queryKey: ['nutrition', 'day', day],
    queryFn: () => api.get<DayTotals>(`/nutrition/day?day=${day}`)
  })

  const search = useQuery({
    queryKey: ['foods', query],
    queryFn: () => api.get<{ items: Food[]; total: number }>(`/nutrition/foods?q=${encodeURIComponent(query)}&limit=25`),
    enabled: query.trim().length >= 2
  })

  const favorites = useQuery({
    queryKey: ['favorites'],
    queryFn: () => api.get<{ id: number; food_id: number; name: string | null }[]>('/nutrition/favorites')
  })

  const tdee = useQuery({
    queryKey: ['tdee'],
    queryFn: () => api.get<TdeeResult>('/nutrition/tdee')
  })

  const addItem = useMutation({
    mutationFn: (payload: { food_id: number; quantity_g: number }) =>
      api.post(`/nutrition/meals/items?logged_on=${day}&category=${category}`, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['nutrition'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
      setSelected(null)
      setQuery('')
    }
  })

  const removeItem = useMutation({
    mutationFn: (id: number) => api.del(`/nutrition/meals/items/${id}`),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['nutrition'] })
      await qc.invalidateQueries({ queryKey: ['today'] })
    }
  })

  const toggleFavorite = useMutation({
    mutationFn: async (foodId: number) => {
      const isFav = favorites.data?.some((f) => f.food_id === foodId)
      if (isFav) await api.del(`/nutrition/favorites/${foodId}`)
      else await api.post('/nutrition/favorites', { food_id: foodId })
    },
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['favorites'] })
  })

  const applyTargets = useMutation({
    mutationFn: () => api.post('/nutrition/tdee/apply'),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['nutrition'] })
      await qc.invalidateQueries({ queryKey: ['tdee'] })
    }
  })

  const d = totals.data
  const favouriteIds = useMemo(() => new Set(favorites.data?.map((f) => f.food_id)), [favorites.data])
  const mealLabel = CATEGORIES.find((c) => c.value === category)?.label ?? category

  return (
    <>
      <header className="page-head">
        <h1>Nutrition</h1>
        <p className="page-sub">Log what you eat and see how it tracks against your target.</p>
      </header>

      {totals.isLoading ? <LoadingState what="today's nutrition" /> : null}
      {totals.isError ? (
        <ErrorState message={totals.error instanceof Error ? totals.error.message : 'Could not load nutrition'} onRetry={() => void totals.refetch()} />
      ) : null}

      {d ? (
        <>
          <Card className="metric-hero">
            <Metric
              label="Calories remaining"
              value={d.target_kcal ? num(Math.max(d.target_kcal - d.kcal, 0)) : num(d.kcal)}
              unit="kcal"
              note={d.target_kcal ? `${num(d.kcal)} of ${num(d.target_kcal)} kcal` : 'No target set yet'}
              tone="accent"
            />
            <div style={{ marginTop: 24, display: 'grid', gap: 16 }}>
              {(['protein', 'carbs', 'fat'] as const).map((key) => {
                const value = key === 'protein' ? d.protein_g : key === 'carbs' ? d.carbs_g : d.fat_g
                const target = key === 'protein' ? d.target_protein_g : key === 'carbs' ? d.target_carbs_g : d.target_fat_g
                const label = key === 'protein' ? 'Protein' : key === 'carbs' ? 'Carbohydrates' : 'Fat'
                return (
                  <Progress
                    key={key} label={`${label} - ${num(value)}${target ? ` of ${num(target)}` : ''} g`}
                    value={value} max={target ?? Math.max(value, 1)}
                    tone={target && value >= target ? 'success' : 'accent'}
                  />
                )
              })}
            </div>
          </Card>

          {!d.target_kcal ? (
            <Card style={{ marginTop: 24 }}>
              <h2 style={{ marginBottom: 8 }}>Set your daily target</h2>
              <p className="state-body" style={{ marginBottom: 16 }}>
                TRINITY can estimate your energy needs from your profile and logged weight. It is an estimate, not a measurement.
              </p>
              {tdee.data && !tdee.data.ready ? (
                <p className="form-error">Complete your profile first: {tdee.data.missing?.join(', ')}.</p>
              ) : null}
              <Button onClick={() => applyTargets.mutate()} disabled={applyTargets.isPending || !tdee.data?.ready}>
                {applyTargets.isPending ? 'Calculating...' : 'Calculate and apply targets'}
              </Button>
              {applyTargets.isError ? (
                <p className="form-error" style={{ marginTop: 8 }}>
                  {applyTargets.error instanceof Error ? applyTargets.error.message : 'Could not apply targets'}
                </p>
              ) : null}
            </Card>
          ) : null}

          {tdee.data?.ready ? (
            <Card style={{ marginTop: 24 }}>
              <h2 style={{ marginBottom: 4 }}>Energy estimate</h2>
              <p className="state-body" style={{ marginBottom: 16 }}>{tdee.data.note}</p>
              <div className="stat-row">
                <div className="stat">
                  <span className="stat-label">BMR (Mifflin-St Jeor)</span>
                  <span className="stat-value">{num(tdee.data.bmr_kcal)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">TDEE estimate</span>
                  <span className="stat-value">{num(tdee.data.tdee_kcal)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Target</span>
                  <span className="stat-value">{num(tdee.data.kcal_target)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Adaptive confidence</span>
                  <span className="stat-value" style={{ fontSize: 18 }}>
                    {tdee.data.adaptive?.confidence ?? 'low'}
                  </span>
                </div>
              </div>
              <p className="source-note" style={{ marginTop: 16 }}>
                Adaptive estimate uses {tdee.data.adaptive?.days_of_data ?? 0} logged days. It needs 14 or more
                days of food and weight data before it replaces the equation-based figure.
              </p>
              <button className="link-btn" style={{ marginTop: 8 }} onClick={() => setShowTargets((v) => !v)}>
                {showTargets ? 'Hide' : 'Show'} manual override
              </button>
              {showTargets ? <ManualTargets day={day} /> : null}
            </Card>
          ) : null}

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 16 }}>Add food</h2>
            {/* field-row keeps the two labelled fields top-aligned, so the Meal
                select no longer sits lower than the search field beside it. */}
            <div className="field-row">
              <div style={{ flex: '1 1 260px' }}>
                <TextField label="Search foods" value={query} onChange={setQuery} placeholder="Chicken breast, oats, egg..." hint="Type at least two characters." />
              </div>
              <div style={{ flex: '0 0 200px' }}>
                <SelectField label="Meal" value={category} onChange={setCategory} options={CATEGORIES} hint={`Logging to ${mealLabel.toLowerCase()}.`} />
              </div>
            </div>

            {search.isFetching ? <p className="list-meta" style={{ marginTop: 12 }}>Searching...</p> : null}

            {search.data && search.data.items.length === 0 ? (
              <EmptyState
                title="No foods match that search"
                body="Try a shorter word, or add your own food with its nutrition values."
              />
            ) : null}

            {search.data && search.data.items.length > 0 ? (
              <ul className="list" style={{ marginTop: 16 }}>
                {search.data.items.map((food) => (
                  <li className="list-row" key={food.id}>
                    <div className="list-main">
                      <span className="list-title">{food.name}</span>
                      <span className="list-meta">
                        {food.brand ? `${food.brand} - ` : ''}
                        {num(food.calories_kcal)} kcal, {num(food.protein_g)} P / {num(food.carbs_g)} C / {num(food.fat_g)} F per 100 g
                        {food.data_quality === 'user_entered' ? ' - your entry' : ''}
                      </span>
                    </div>
                    <div className="row" style={{ alignItems: 'center' }}>
                      <button
                        className="link-btn" aria-label={favouriteIds.has(food.id) ? 'Remove from favourites' : 'Add to favourites'}
                        onClick={() => toggleFavorite.mutate(food.id)}
                      >
                        <IconStar size={18} style={{ color: favouriteIds.has(food.id) ? 'var(--accent)' : 'var(--text-tertiary)' }} />
                      </button>
                      <Button variant="ghost" onClick={() => { setSelected(food); setGrams('100') }}>Add</Button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : null}

            {selected ? (
              <div className="card" style={{ marginTop: 16, background: 'var(--surface-2)' }}>
                <h3 style={{ marginBottom: 12 }}>{selected.name}</h3>
                <div className="row" style={{ marginBottom: 12 }}>
                  {SERVING_PRESETS.map((g) => (
                    <Button key={g} variant={grams === String(g) ? 'primary' : 'ghost'} onClick={() => setGrams(String(g))}>
                      {g} g
                    </Button>
                  ))}
                </div>
                <div className="field-row">
                  <div style={{ flex: '0 0 160px' }}>
                    <NumberField label="Amount" value={grams} onChange={setGrams} min={1} max={3000} hint="Grams" />
                  </div>
                  <div className="stat" style={{ flex: '1 1 180px' }}>
                    <span className="stat-label">This portion</span>
                    <span className="stat-value">
                      {num((selected.calories_kcal * Number(grams || 0)) / 100)} kcal
                    </span>
                    <span className="list-meta">
                      {num((selected.protein_g * Number(grams || 0)) / 100)} P / {num((selected.carbs_g * Number(grams || 0)) / 100)} C / {num((selected.fat_g * Number(grams || 0)) / 100)} F
                    </span>
                  </div>
                  <div className="row" style={{ alignItems: 'center', flex: '1 1 100%' }}>
                    <Button
                      onClick={() => addItem.mutate({ food_id: selected.id, quantity_g: Number(grams) })}
                      disabled={addItem.isPending || !Number(grams)}
                    >
                      <IconPlus size={16} /> Log to {mealLabel.toLowerCase()}
                    </Button>
                    <Button variant="ghost" onClick={() => setSelected(null)}>Cancel</Button>
                  </div>
                </div>
                {addItem.isError ? (
                  <p className="form-error" style={{ marginTop: 8 }}>
                    {addItem.error instanceof Error ? addItem.error.message : 'Could not log that food'}
                  </p>
                ) : null}
              </div>
            ) : null}

            <DataSourceNote>
              Values are per 100 g and come from the food's recorded source. Nutrition varies by brand, cut and
              cooking method, so treat every figure as an estimate. Reference foods are development seed data;
              imported foods carry their USDA record id.
            </DataSourceNote>
          </Card>

          <Card style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 16 }}>Logged today</h2>
            {d.meals.length === 0 ? (
              <EmptyState title="No meals logged today" body="Search for a food above and log it to your first meal." />
            ) : (
              <div className="stack">
                {d.meals.map((meal) => (
                  <div className="meal-group" key={meal.id}>
                    <div className="meal-head">
                      <span>{CATEGORIES.find((c) => c.value === meal.category)?.label ?? meal.category}</span>
                      <span className="num">
                        {num(meal.items.reduce((s, i) => s + i.kcal, 0))} kcal
                      </span>
                    </div>
                    <ul className="list">
                      {meal.items.map((item) => (
                        <li className="list-row" key={item.id}>
                          <div className="list-main">
                            <span className="list-title">{num(item.quantity_g)} g</span>
                            <span className="list-meta">
                              {num(item.protein_g)} P / {num(item.carbs_g)} C / {num(item.fat_g)} F
                            </span>
                          </div>
                          <div className="row" style={{ alignItems: 'center' }}>
                            <span className="list-value">{num(item.kcal)} kcal</span>
                            <Button variant="ghost" onClick={() => removeItem.mutate(item.id)}>Remove</Button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {favorites.data && favorites.data.length > 0 ? (
            <Card style={{ marginTop: 24 }}>
              <h2 style={{ marginBottom: 12 }}>Favourites</h2>
              <div className="row">
                {favorites.data.map((f) => (
                  <Chip key={f.id} tone="accent">{f.name ?? `Food ${f.food_id}`}</Chip>
                ))}
              </div>
            </Card>
          ) : null}
        </>
      ) : null}
    </>
  )
}

function ManualTargets({ day }: { day: string }) {
  const qc = useQueryClient()
  const [kcal, setKcal] = useState('')
  const [protein, setProtein] = useState('')
  const [carbs, setCarbs] = useState('')
  const [fat, setFat] = useState('')
  const save = useMutation({
    mutationFn: () => api.post('/nutrition/targets/manual', {
      kcal: Number(kcal), protein_g: Number(protein), carbs_g: Number(carbs), fat_g: Number(fat)
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['nutrition'] })
      await qc.invalidateQueries({ queryKey: ['tdee'] })
    }
  })
  return (
    <div className="stack" style={{ marginTop: 16 }}>
      <p className="state-body">Set your own numbers if you prefer to control them directly.</p>
      <div className="grid grid-2">
        <NumberField label="Calories" value={kcal} onChange={setKcal} min={800} max={8000} placeholder="2650" />
        <NumberField label="Protein g" value={protein} onChange={setProtein} min={20} max={500} placeholder="165" />
        <NumberField label="Carbs g" value={carbs} onChange={setCarbs} min={0} max={900} placeholder="285" />
        <NumberField label="Fat g" value={fat} onChange={setFat} min={10} max={300} placeholder="74" />
      </div>
      <div className="row">
        <Button onClick={() => save.mutate()} disabled={save.isPending || !kcal || !protein || !carbs || !fat}>
          {save.isPending ? 'Saving...' : `Save targets for ${day}`}
        </Button>
        {save.isSuccess ? <p className="form-ok">Targets saved.</p> : null}
        {save.isError ? <p className="form-error">{save.error instanceof Error ? save.error.message : 'Could not save'}</p> : null}
      </div>
    </div>
  )
}
