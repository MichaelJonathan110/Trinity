/** Shared API types. Kept deliberately close to the backend schemas. */

export interface Tokens { access_token: string; refresh_token: string; token_type: string }

export interface Profile {
  id: number; user_id: number; display_name: string
  birth_date: string | null; sex: string | null
  height_cm: number | null; body_fat_pct: number | null
  training_experience: string | null; training_frequency: number | null
  session_minutes: number | null; activity_level: string | null
  units: string; theme_pref: string; timezone: string | null
}

export interface Goal {
  id: number; goal_type: string; rate_kg_per_week: number | null
  target_weight_kg: number | null; started_on: string; ended_on: string | null; is_active: boolean
}

/** One body measurement. Circumferences are optional: a tape measure is not
    required, but when present they show shape change a scale cannot (spec 64). */
export interface BodyMetric {
  id: number; measured_on: string; weight_kg: number | null
  body_fat_pct: number | null; waist_cm: number | null; notes: string | null
  neck_cm?: number | null; shoulder_cm?: number | null; chest_cm?: number | null
  arm_cm?: number | null; forearm_cm?: number | null; thigh_cm?: number | null
  hip_cm?: number | null; calf_cm?: number | null
}

export interface Food {
  id: number; name: string; brand: string | null; category: string | null
  calories_kcal: number; protein_g: number; carbs_g: number; fat_g: number
  fiber_g: number | null; default_serving_g: number | null; default_serving_label: string | null
  data_quality: string; source_ref: string | null
}

export interface MealItem {
  id: number; food_id: number | null; recipe_id: number | null
  quantity_g: number; serving_label: string | null
  kcal: number; protein_g: number; carbs_g: number; fat_g: number
}

export interface Meal {
  id: number; logged_on: string; category: string; name: string | null; items: MealItem[]
}

export interface DayTotals {
  logged_on: string; kcal: number; protein_g: number; carbs_g: number; fat_g: number
  target_kcal: number | null; target_protein_g: number | null
  target_carbs_g: number | null; target_fat_g: number | null
  meals: Meal[]
}

export interface NutritionHistoryDay {
  date: string; kcal: number; protein_g: number; carbs_g: number; fat_g: number; items: number
}

export interface TdeeResult {
  ready: boolean
  missing?: string[]
  note?: string
  bmr_kcal?: number; tdee_kcal?: number; tdee_method?: string
  activity_level?: string; goal_type?: string; kcal_target?: number
  macros?: { kcal: number; protein_g: number; carbs_g: number; fat_g: number }
  adaptive?: { tdee_kcal: number; method: string; confidence: string; days_of_data: number }
  logged_days?: number
  target_history?: { effective_from: string; kcal: number; source: string }[]
}

export interface Exercise {
  id: number; name: string; primary_muscle: string; secondary_muscles: string | null
  equipment: string | null; movement_pattern: string | null; instructions: string | null
}

/** rir = reps in reserve; set_type = normal | drop | myo_rep | rest_pause | amrap | failure. */
export interface WorkoutSet {
  id?: number; set_index: number; weight_kg: number | null; reps: number | null
  rpe: number | null; rir: number | null; set_type: string | null
  rest_sec: number | null; is_warmup: boolean
}

export interface WorkoutExercise {
  id: number; exercise_id: number; position: number; notes: string | null; sets: WorkoutSet[]
}

export interface Workout {
  id: number; performed_on: string; title: string; status: string
  duration_min: number | null; notes: string | null; exercises: WorkoutExercise[]
}

export interface WorkoutSummary {
  id: number; performed_on: string; title: string; status: string
  duration_min: number | null; notes: string | null; exercises: number; sets: number
}

export interface LastSession {
  exists: boolean
  note?: string
  performed_on?: string; title?: string
  sets?: { weight_kg: number | null; reps: number | null; is_warmup: boolean; rir?: number | null; set_type?: string | null }[]
  volume?: number; best_e1rm?: number | null
}

/** Weekly fractional sets per muscle, against MEV/MAV/MRV landmarks (spec 33). */
export interface MuscleVolume {
  muscle: string; sets_per_week: number
  mev: number; mav: number; mrv: number
  status: 'none' | 'below_mev' | 'maintenance' | 'optimal' | 'above_mrv'
}

export interface VolumeAnalysis {
  weeks: number; window_start: string
  muscles: MuscleVolume[]; trained_count: number; note: string
}

export interface ProgressionAdvice {
  exists: boolean
  note?: string
  action?: string
  detail?: string
  current?: { top_weight: number | null; best_e1rm: number | null; total_reps: number; set_count: number; avg_rir: number | null }
  previous?: { top_weight: number | null; best_e1rm: number | null; total_reps: number; set_count: number; avg_rir: number | null } | null
}

export interface Program {
  id: number; name: string; description: string | null; goal: string | null
  weeks: number | null; is_active: boolean
  template_slug: string | null; source_name: string | null
  source_url: string | null; attribution_note: string | null
  days: { day_index: number; title: string; is_rest: boolean }[]
}

export interface CalendarDay {
  day: string; status: 'completed' | 'modified' | 'skipped' | 'rest' | 'none'
  workout_id: number | null; title: string | null
}

export interface TrainingSummary {
  year: number; total_sessions: number; completed: number; skipped: number
  rest_days: number; consistency_pct: number | null; avg_per_week: number
}

export interface PersonalRecord {
  id: number; exercise_id: number; record_type: string; value: number
  weight_kg: number | null; reps: number | null; achieved_on: string
}

export interface ProgressionPoint {
  date: string; volume: number; best_e1rm: number | null; top_weight: number | null
}

/* ------------------------------------------------------------ Preparation */
export interface PrepPhase {
  id: number; phase_type: string; started_on: string; weeks_on_phase: number
  start_weight_kg: number | null; target_weight_kg: number | null
  target_rate_pct_per_week: number | null; kcal_adjustment: number; notes: string | null
}

export interface WeeklyAverage { week_start: string; avg_kg: number; n: number }

export interface PhaseVerdict {
  verdict: 'unknown' | 'on_plan' | 'too_slow' | 'too_fast'
  label: string; detail: string
}

export interface PhaseSuggestion { suggested_kcal: number; reason: string }

export interface RefeedSuggestion { kind: 'refeed' | 'diet_break'; label: string; detail: string }

export interface PreparationStatus {
  active: boolean
  note?: string
  phase?: PrepPhase
  current_weight_kg?: number | null
  total_change_kg?: number | null
  weekly_averages?: WeeklyAverage[]
  actual_kg_per_week?: number | null
  actual_pct_per_week?: number | null
  verdict?: PhaseVerdict
  suggestion?: PhaseSuggestion
  refeed_due?: RefeedSuggestion | null
}

export interface RefeedEntry {
  id: number; occurred_on: string; kind: string; days: number; notes: string | null
}

/* --------------------------------------------------------- Progress photo */
export interface ProgressPhoto {
  id: number; taken_on: string; pose: string; weight_kg: number | null
  notes: string | null; content_type: string; size_bytes: number; url: string
}

export interface SleepEntry {
  id: number; slept_on: string; bedtime: string; wake_at: string
  duration_min: number; quality: number | null; is_nap: boolean; source: string; notes: string | null
}

export interface SleepDay {
  date: string; duration_min: number; quality: number | null; score: number
  bedtime: string; wake_at: string
}

export interface SleepAverage {
  days: number; avg_minutes: number | null; avg_score: number | null; consistency: number | null
}

export interface RecoveryMetric {
  id: number; recorded_on: string; subjective_score: number | null
  soreness_score: number | null; resting_hr: number | null; hrv_ms: number | null
  readiness_score: number | null; readiness_label: string | null; notes: string | null
}

export interface Readiness {
  score: number | null; label: string; inputs: number
  note?: string; sleep_minutes?: number | null; sleep_target_minutes?: number
}

export interface DayActivity {
  recorded_on: string; steps: number; step_goal: number
  distance_m: number | null; active_kcal: number | null; active_minutes: number | null; source: string
}

export interface StepsHistoryDay {
  date: string; steps: number; distance_m: number | null
  active_kcal: number | null; logged: boolean
}

export interface PillarScore {
  key: string; label: string; score: number | null; detail: string
}

export interface Insight {
  id?: number; for_date: string; domain: string; severity: string; title: string; body: string
}

export interface TodayPayload {
  for_date: string; greeting: string; display_name: string
  pillars: PillarScore[]; readiness: Readiness; headline: string
  insights: Insight[]; has_data: boolean
}
