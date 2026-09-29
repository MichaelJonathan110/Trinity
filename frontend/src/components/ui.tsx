/**
 * UI primitives. Kept small and unopinionated so feature code composes them.
 * Colour always comes from tokens; no component hardcodes a hex value.
 */
import type { ChangeEvent, CSSProperties, ReactNode } from 'react'

/* ------------------------------------------------------------------ Card */
export function Card({ children, className = '', style }: { children: ReactNode; className?: string; style?: CSSProperties }) {
  return <section className={`card ${className}`} style={style}>{children}</section>
}

export function SectionTitle({
  children, action, style
}: { children: ReactNode; action?: ReactNode; style?: CSSProperties }) {
  return (
    <header className="section-title" style={style}>
      <h2>{children}</h2>
      {action}
    </header>
  )
}

export function Divider() {
  return <hr className="divider" />
}

/* ---------------------------------------------------------------- Metric */
export function Metric({
  value, unit, label, note, tone = 'default'
}: {
  value: ReactNode; unit?: string; label: string; note?: string
  /** 'accent' marks the one number the screen exists to show (DESIGN.md principle 1). */
  tone?: 'default' | 'accent'
}) {
  return (
    <div className={`metric-block${tone === 'accent' ? ' metric-accent' : ''}`}>
      <p className="metric-label">{label}</p>
      <p className="metric">
        <span className="metric-value">{value}</span>
        {unit ? <span className="metric-unit">{unit}</span> : null}
      </p>
      {note ? <p className="metric-note">{note}</p> : null}
    </div>
  )
}

/* -------------------------------------------------------------- Progress */
export function Progress({
  value, max, label, tone = 'accent', showPct = false
}: { value: number; max: number; label: string; tone?: 'accent' | 'success' | 'warning' | 'danger'; showPct?: boolean }) {
  const pct = max > 0 ? Math.min(Math.max((value / max) * 100, 0), 100) : 0
  return (
    <div className="progress-wrap">
      <div className="progress-head">
        <span>{label}</span>
        {showPct ? <span className="num">{Math.round(pct)}%</span> : null}
      </div>
      <div
        className="progress" role="progressbar" aria-label={label}
        aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}
      >
        <div className={`progress-fill tone-${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

/* ---------------------------------------------------------------- Button */
export function Button({
  children, onClick, type = 'button', variant = 'primary', disabled = false, full = false, style
}: {
  children: ReactNode; onClick?: () => void
  type?: 'button' | 'submit'; variant?: 'primary' | 'ghost' | 'danger'
  disabled?: boolean; full?: boolean; style?: CSSProperties
}) {
  return (
    <button
      type={type} onClick={onClick} disabled={disabled} style={style}
      className={`btn btn-${variant}${full ? ' btn-full' : ''}`}
    >
      {children}
    </button>
  )
}

/* -------------------------------------------------------------- Segmented */
/** A single-choice control for switching views. Renders as real buttons with
    aria-pressed so it works with a keyboard and a screen reader. */
export function Segmented<T extends string>({
  value, onChange, options, label
}: {
  value: T; onChange: (v: T) => void
  options: readonly { value: T; label: string }[]; label: string
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value} type="button" aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

/* ----------------------------------------------------------------- Field */
interface FieldBase { label: string; hint?: string; required?: boolean }

export function TextField({
  label, value, onChange, type = 'text', placeholder, hint, required = false, min, max, step
}: FieldBase & {
  value: string; onChange: (v: string) => void; type?: string
  placeholder?: string; min?: string; max?: string; step?: string
}) {
  return (
    <label className="field">
      <span className="field-label">
        {label}{required ? <span aria-hidden="true"> *</span> : null}
      </span>
      <input
        type={type} value={value} placeholder={placeholder} required={required}
        min={min} max={max} step={step}
        onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
      />
      {hint ? <span className="field-hint">{hint}</span> : null}
    </label>
  )
}

export function NumberField({
  label, value, onChange, hint, required = false, min, max, step = 'any', placeholder
}: FieldBase & {
  value: string; onChange: (v: string) => void
  min?: number; max?: number; step?: string; placeholder?: string
}) {
  return (
    <label className="field">
      <span className="field-label">
        {label}{required ? <span aria-hidden="true"> *</span> : null}
      </span>
      <input
        type="number" inputMode="decimal" value={value} placeholder={placeholder}
        min={min} max={max} step={step} required={required}
        onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
      />
      {hint ? <span className="field-hint">{hint}</span> : null}
    </label>
  )
}

export function SelectField({
  label, value, onChange, options, hint
}: FieldBase & {
  value: string; onChange: (v: string) => void
  options: { value: string; label: string }[]
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {hint ? <span className="field-hint">{hint}</span> : null}
    </label>
  )
}

/* ----------------------------------------------------------- State blocks */
export function LoadingState({ what = 'data' }: { what?: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <p>Loading {what}...</p>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state state-error" role="alert">
      <p className="state-title">That did not load</p>
      <p className="state-body">{message}</p>
      {onRetry ? <Button variant="ghost" onClick={onRetry}>Try again</Button> : null}
    </div>
  )
}

export function EmptyState({
  title, body, action
}: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="state">
      <p className="state-title">{title}</p>
      <p className="state-body">{body}</p>
      {action}
    </div>
  )
}

export function Chip({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'accent' | 'success' | 'warning' | 'danger' }) {
  return <span className={`chip chip-${tone}`}>{children}</span>
}

/* ---------------------------------------------------------------- Legend */
/** Explains what a numeric scale or an option name actually means, e.g. the
    sleep-quality 1-5 scale or the activity levels. Content, not decoration. */
export function Legend({
  title, items, note
}: { title: string; items: { key: string; label: string }[]; note?: string }) {
  return (
    <div className="legend">
      <p className="legend-title">{title}</p>
      {items.map((it) => (
        <div className="legend-row" key={it.key}>
          <span className="legend-key">{it.key}</span>
          <p className="legend-val">{it.label}</p>
        </div>
      ))}
      {note ? <p className="legend-note">{note}</p> : null}
    </div>
  )
}

export function DataSourceNote({ children }: { children: ReactNode }) {
  return <p className="source-note">{children}</p>
}
