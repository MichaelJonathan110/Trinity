/**
 * Charts drawn from real data only. When a series has fewer than two points we
 * render nothing and say so, rather than drawing a decorative shape (antislop R-17, R-38).
 */

export function BarChart({
  data, unit = '', goal, label
}: {
  data: { label: string; value: number }[]
  unit?: string; goal?: number | null; label: string
}) {
  if (data.length === 0) return null
  const max = Math.max(...data.map((d) => d.value), goal ?? 0, 1)
  return (
    <figure className="chart" role="img" aria-label={label}>
      <figcaption className="chart-caption">{label}</figcaption>
      <div className="bars">
        {data.map((d) => {
          const h = Math.max((d.value / max) * 100, d.value > 0 ? 3 : 0)
          return (
            <div className="bar-col" key={d.label}>
              <div className="bar-track">
                <div
                  className={`bar-fill${goal && d.value >= goal ? ' bar-met' : ''}`}
                  style={{ height: `${h}%` }}
                  title={`${d.label}: ${Math.round(d.value)}${unit}`}
                />
              </div>
              <span className="bar-label">{d.label}</span>
            </div>
          )
        })}
      </div>
      {goal ? (
        <p className="chart-note">Goal {Math.round(goal)}{unit}. Bars that reach it are marked.</p>
      ) : null}
    </figure>
  )
}

/** Line chart for a single series; needs at least two points to mean anything. */
export function LineChart({
  points, label, unit = '', formatValue
}: {
  points: { x: string; y: number | null }[]
  label: string; unit?: string; formatValue?: (v: number) => string
}) {
  const usable = points.filter((p) => p.y !== null) as { x: string; y: number }[]
  if (usable.length < 2) {
    return (
      <div className="state state-inline">
        <p className="state-body">
          At least two data points are needed for a {label.toLowerCase()} chart. Log more to see a trend.
        </p>
      </div>
    )
  }
  const W = 640
  const H = 180
  const PAD = 8
  const values = usable.map((p) => p.y)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const stepX = (W - PAD * 2) / (usable.length - 1)
  const coords = usable.map((p, i) => {
    const x = PAD + i * stepX
    const y = H - PAD - ((p.y - min) / span) * (H - PAD * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const fmt = formatValue ?? ((v: number) => v.toFixed(1))

  return (
    <figure className="chart" role="img" aria-label={`${label}: ${fmt(values[0])} to ${fmt(values[values.length - 1])} ${unit}`}>
      <figcaption className="chart-caption">{label}</figcaption>
      <svg className="line-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        <polyline className="line-path" points={coords.join(' ')} />
        {coords.map((c, i) => {
          const [cx, cy] = c.split(',')
          return <circle className="line-dot" key={i} cx={cx} cy={cy} r={3} />
        })}
      </svg>
      <div className="chart-axis">
        <span>{usable[0].x}</span>
        <span>{fmt(min)}{unit}</span>
        <span>{fmt(max)}{unit}</span>
        <span>{usable[usable.length - 1].x}</span>
      </div>
    </figure>
  )
}
