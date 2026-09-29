/** Local UI preferences (not server data). */
import { create } from 'zustand'
import { apply, getPref, setPref, type ThemePref } from '../lib/theme'

interface PrefsState {
  themePref: ThemePref
  setTheme: (pref: ThemePref) => void
}

export const usePrefs = create<PrefsState>((set) => ({
  themePref: getPref(),
  setTheme(pref) {
    setPref(pref)
    apply(pref)
    set({ themePref: pref })
  }
}))
