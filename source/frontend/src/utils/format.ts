export const WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

/** Local date as YYYY-MM-DD (what <input type="date"> and the API use). */
export function isoDate(d: Date): string {
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

function parse(value: string): Date {
  // A plain date (no time) is read as local midnight so it never shifts a day.
  return new Date(value.length === 10 ? `${value}T00:00:00` : value);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  return parse(value).toLocaleDateString("en-PH", { year: "numeric", month: "short", day: "numeric" });
}

export function formatTime(value: string | null | undefined): string {
  if (!value) return "-";
  return parse(value).toLocaleTimeString("en-PH", { hour: "numeric", minute: "2-digit" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  return `${formatDate(value)}, ${formatTime(value)}`;
}

export function formatMoney(value: number | string | null | undefined): string {
  return new Intl.NumberFormat("en-PH", { style: "currency", currency: "PHP" }).format(Number(value ?? 0));
}

export function ageFrom(birthdate: string | null | undefined): string {
  if (!birthdate) return "";
  const born = parse(birthdate);
  const now = new Date();
  let age = now.getFullYear() - born.getFullYear();
  if (now.getMonth() < born.getMonth() || (now.getMonth() === born.getMonth() && now.getDate() < born.getDate())) age -= 1;
  return age >= 0 ? `${age} yrs` : "";
}

export function weekdayList(days: number[]): string {
  return days.map((d) => WEEKDAY_NAMES[d - 1]?.slice(0, 3)).join(", ");
}