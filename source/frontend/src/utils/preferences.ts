// Per-browser display preferences (theme, text size, check-in alert). Stored in localStorage.
export type Theme = "light" | "dark" | "system";
export type TextSize = "small" | "normal" | "large";

export interface Prefs {
  theme: Theme;
  textSize: TextSize;
  checkInAlert: boolean; // doctor: show a banner when a patient checks in
}

export const DEFAULT_PREFS: Prefs = { theme: "light", textSize: "normal", checkInAlert: true };
const KEY = "appointmed.preferences";
const SIZES: Record<TextSize, string> = { small: "14px", normal: "", large: "18px" };

export function loadPrefs(): Prefs {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const p = JSON.parse(raw) as Partial<Prefs>;
      return {
        theme: p.theme === "dark" || p.theme === "system" || p.theme === "light" ? p.theme : DEFAULT_PREFS.theme,
        textSize: p.textSize === "small" || p.textSize === "large" || p.textSize === "normal" ? p.textSize : DEFAULT_PREFS.textSize,
        checkInAlert: typeof p.checkInAlert === "boolean" ? p.checkInAlert : DEFAULT_PREFS.checkInAlert,
      };
    }
  } catch {
    /* storage unavailable or damaged: use the defaults */
  }
  return DEFAULT_PREFS;
}

export function savePrefs(prefs: Prefs): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(prefs));
  } catch {
    /* storage unavailable: the choice lasts until refresh */
  }
}

export function applyPrefs(prefs: Prefs): void {
  const dark = prefs.theme === "dark" || (prefs.theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.style.fontSize = SIZES[prefs.textSize];
}

/** Merge a change into the saved preferences, save, apply, and return the result. */
export function updatePrefs(patch: Partial<Prefs>): Prefs {
  const next = { ...loadPrefs(), ...patch };
  savePrefs(next);
  applyPrefs(next);
  return next;
}