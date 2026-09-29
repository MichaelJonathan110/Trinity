/**
 * TRINITY icon set: original, hand-drawn on a 24px grid, 1.6px stroke.
 * Written here rather than imported from a default icon library so the set is a
 * deliberate brand decision (antislop R-04, R-06). Every glyph maps to a real concept.
 */
import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement> & { size?: number }

function Svg({ size = 20, children, ...rest }: IconProps) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true" focusable="false" {...rest}
    >
      {children}
    </svg>
  )
}

/** Nutrition: a fork and a leaf (food). */
export const IconNutrition = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 3v7a3 3 0 0 0 6 0V3" />
    <path d="M10 10v11" />
    <path d="M17 3c-1.6 1.4-2.4 3-2.4 5 0 1.6.8 2.6 2.4 3.2V21" />
  </Svg>
)

/** Rest: a crescent moon. */
export const IconRest = (p: IconProps) => (
  <Svg {...p}>
    <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
  </Svg>
)

/** Exercise: a dumbbell. */
export const IconExercise = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 9v6M7 7v10M17 7v10M20 9v6" />
    <path d="M7 12h10" />
  </Svg>
)

/** Steps: two footprints, one leading the other. */
export const IconSteps = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8.5 4.5c1.2 0 2 1.1 2 2.6 0 1.6-.4 3.4-.4 4.6 0 .9-.7 1.6-1.6 1.6H6.9c-.9 0-1.6-.7-1.6-1.6 0-1.2-.4-3-.4-4.6 0-1.5.8-2.6 2-2.6Z" />
    <path d="M7.7 16.8v2.6" />
    <path d="M16.5 9.5c1.2 0 2 1.1 2 2.6 0 1.6-.4 3.4-.4 4.6 0 .9-.7 1.6-1.6 1.6h-1.6c-.9 0-1.6-.7-1.6-1.6 0-1.2-.4-3-.4-4.6 0-1.5.8-2.6 2-2.6Z" />
    <path d="M15.7 5.2v2.6" />
  </Svg>
)

/** Account: a person. */
export const IconAccount = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="8.5" r="3.5" />
    <path d="M5 20a7 7 0 0 1 14 0" />
  </Svg>
)

/** Today / performance overview: three stacked bars of unequal height. */
export const IconToday = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 19h16" />
    <path d="M7 19V11M12 19V5M17 19v-5" />
  </Svg>
)

export const IconSun = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4" />
  </Svg>
)

export const IconPlus = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 5v14M5 12h14" />
  </Svg>
)

export const IconSearch = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="6" />
    <path d="M15.5 15.5 20 20" />
  </Svg>
)

export const IconClose = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 6l12 12M18 6 6 18" />
  </Svg>
)

export const IconStar = (p: IconProps) => (
  <Svg {...p}>
    <path d="m12 4 2.4 4.9 5.4.8-3.9 3.8.9 5.4-4.8-2.6-4.8 2.6.9-5.4L4.2 9.7l5.4-.8Z" />
  </Svg>
)

export const IconChevron = (p: IconProps) => (
  <Svg {...p}>
    <path d="m9 6 6 6-6 6" />
  </Svg>
)

/** Preparation: a target, because a phase aims at a bodyweight and a rate. */
export const IconPrep = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <circle cx="12" cy="12" r="4.5" />
    <circle cx="12" cy="12" r="1" />
  </Svg>
)

/** Progress photos: a camera body with a lens. */
export const IconCamera = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 8.5A1.5 1.5 0 0 1 4.5 7h2l1.2-1.6a1 1 0 0 1 .8-.4h7a1 1 0 0 1 .8.4L17.5 7h2A1.5 1.5 0 0 1 21 8.5v9A1.5 1.5 0 0 1 19.5 19h-15A1.5 1.5 0 0 1 3 17.5Z" />
    <circle cx="12" cy="13" r="3.2" />
  </Svg>
)

/** Tape measure: the circumference log. */
export const IconRuler = (p: IconProps) => (
  <Svg {...p}>
    <rect x="2.5" y="8.5" width="19" height="7" rx="1.5" />
    <path d="M7 8.5v2.5M11 8.5v3.5M15 8.5v2.5M19 8.5v3.5" />
  </Svg>
)
