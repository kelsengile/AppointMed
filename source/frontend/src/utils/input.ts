// Input filters. Each one removes characters a field must never contain, so users can only type valid values.
// The backend (schemas/api.py) enforces the same rules.
const tidy = (v: string) => v.replace(/^\s+/, "").replace(/\s{2,}/g, " ");
const strip = (re: RegExp, max: number) => (v: string) => tidy(v.replace(re, "")).slice(0, max);

export const cleanName = strip(/[^\p{L}\p{M} '’.,()-]/gu, 100);
export const cleanSpecialization = strip(/[^\p{L}\p{M} &,./-]/gu, 100);
export const cleanRoomName = strip(/[^\p{L}\p{N}\p{M} #.()-]/gu, 50);
export const cleanMedicine = strip(/[^\p{L}\p{N}\p{M} .,()/%+'’-]/gu, 150);
export const cleanDosage = strip(/[^\p{L}\p{N}\p{M} .,()/%+'’-]/gu, 100);
export const cleanAddress = strip(/[^\p{L}\p{N}\p{M} #.,'’()/-]/gu, 255);
export const cleanClinicName = strip(/[^\p{L}\p{N}\p{M} &.,'’()-]/gu, 100);

export const cleanEmail = (v: string) => v.replace(/\s/g, "").slice(0, 100);
export const cleanUsername = (v: string) => v.replace(/[^A-Za-z0-9._-]/g, "").slice(0, 50);
export const cleanInt = (v: string, max: number) => v.replace(/\D/g, "").slice(0, max);
export const cleanText = (v: string, max: number) => v.replace(/[\u0000-\u001F\u007F]/g, "").replace(/^\s+/, "").slice(0, max);
export const cleanMultiline = (v: string, max: number) => v.replace(/[\u0000-\u0009\u000B-\u001F\u007F]/g, "").slice(0, max);

/** Digits and one dot, at most 2 decimals and `maxInt` whole digits. */
export function cleanMoney(v: string, maxInt = 7): string {
  let s = v.replace(/[^0-9.]/g, "");
  const dot = s.indexOf(".");
  if (dot >= 0) s = s.slice(0, dot + 1) + s.slice(dot + 1).replace(/\./g, "");
  const [whole, frac] = s.split(".");
  const w = whole.slice(0, maxInt);
  return frac === undefined ? w : `${w}.${frac.slice(0, 2)}`;
}

/** Digits, spaces, ( ) - and a + only as the first character. */
export const cleanPhone = (v: string) =>
  tidy(v.replace(/[^0-9+()\-\s]/g, "").replace(/(?!^)\+/g, "")).slice(0, 20);

export const MIN_BIRTHDATE = "1900-01-01";

export const isName = (v: string) => /^[\p{L}\p{M} '’.,()-]+$/u.test(v) && (v.match(/\p{L}/gu) ?? []).length >= 2;
export const isEmail = (v: string) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v);
export const isUsername = (v: string) => /^[A-Za-z0-9._-]{3,50}$/.test(v);
export const isPhone = (v: string) => {
  const digits = v.replace(/\D/g, "").length;
  return /^\+?[0-9()\-\s]{6,19}$/.test(v) && digits >= 7 && digits <= 15;
};
export const isMoney = (v: string, max = 1_000_000) => /^\d+(\.\d{1,2})?$/.test(v) && Number(v) <= max;

/** Spread onto an <input> for an amount (text + decimal keypad, so letters and "e" can never be typed). */
export const MONEY_PROPS = { type: "text", inputMode: "decimal", autoComplete: "off", maxLength: 10 } as const;
/** Spread onto an <input> for a whole number. */
export const INT_PROPS = { type: "text", inputMode: "numeric", autoComplete: "off" } as const;