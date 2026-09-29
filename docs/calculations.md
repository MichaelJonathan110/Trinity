# Calculations

Every formula lives in `backend/app/calculations/` as a **pure function** with unit
tests. Nothing here performs I/O. All inputs and outputs are explicit.

## Energy

**BMR — Mifflin-St Jeor**

```
male:   BMR = 10*kg + 6.25*cm - 5*age + 5
female: BMR = 10*kg + 6.25*cm - 5*age - 161
```

**TDEE** = `BMR * activity_factor`

| Activity | Factor |
|----------|--------|
| sedentary | 1.2 |
| light | 1.375 |
| moderate | 1.55 |
| very active | 1.725 |
| athlete | 1.9 |

**Goal-adjusted target**

```
cut:      TDEE - 0.20 * TDEE
maintain: TDEE
bulk:     TDEE + 0.10 * TDEE
```

## Macros

Given a target calorie intake and a goal:

| Goal | Protein | Fat | Carbs |
|------|---------|-----|-------|
| cut | 2.2 g/kg | 25% kcal | remainder |
| maintain | 1.8 g/kg | 30% kcal | remainder |
| bulk | 1.6 g/kg | 25% kcal | remainder |

Protein and fat are set first (they are the physiologically constrained
macros); carbohydrate absorbs the remainder. 1 g protein = 4 kcal,
1 g carb = 4 kcal, 1 g fat = 9 kcal.

## Training Readiness (0–100)

A weighted blend of the last night's recovery against recent load:

```
readiness = 100
  - sleep_debt_penalty     (short vs. needed sleep)
  - hrv_penalty            (below personal baseline)
  - resting_hr_penalty     (above personal baseline)
  - load_penalty           (acute:chronic workload ratio)
  - soreness_penalty
```

Each penalty is clamped; the result is clamped to `[0, 100]`. Bands:

| Score | Band |
|-------|------|
| 80–100 | Primed |
| 60–79 | Ready |
| 40–59 | Compromised |
| 0–39 | Rest |

The **breakdown** (per-factor contribution) is returned alongside the score so
the UI can explain *why*, never just show a number.

## Daily Performance (0–100)

Combines nutrition adherence, activity, training, and recovery into one
end-of-day score. Each domain contributes a bounded sub-score; weights are
fixed constants in `calculations/performance.py`.

## Personal records

Estimated 1RM uses the **Epley** formula: `1RM = w * (1 + reps/30)`.
A record is only updated when the estimate exceeds the stored best.

## Conventions

- All functions take plain numbers/dataclasses and return plain numbers.
- Rounding happens once, at the edge, in a documented `round_*` helper.
- Baseline values (HRV, resting HR) are rolling means over a configurable
  window (default 28 days).
