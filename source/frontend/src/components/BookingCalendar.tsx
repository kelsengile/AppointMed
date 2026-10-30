// Date picker for the public booking page. It follows the chosen doctor's schedule.
// Red = the doctor does not work that weekday. Amber = fully booked. Both (and past days) cannot be chosen.
import { useEffect, useRef, useState } from "react";
import { publicApi } from "../api/endpoints";
import { usePolling } from "../hooks/usePolling";
import { formatDate, isoDate } from "../utils/format";

const HEADERS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const firstOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1);

interface Props {
  value: string; // YYYY-MM-DD or ""
  onChange: (day: string) => void;
  doctorId: string; // "" until a doctor is chosen
  minDay: string; // first bookable day (today)
  maxDay: string; // last bookable day (end of the booking window)
  hasError?: boolean;
}

export default function BookingCalendar({ value, onChange, doctorId, minDay, maxDay, hasError }: Props) {
  const [open, setOpen] = useState(false);
  const [month, setMonth] = useState(() => firstOfMonth(new Date(`${value || minDay}T00:00:00`)));
  const box = useRef<HTMLDivElement>(null);

  // 6 weeks starting on the Monday on or before the 1st, so every month fits the same grid.
  const start = new Date(month.getFullYear(), month.getMonth(), 1 - ((month.getDay() + 6) % 7));
  const cells = Array.from({ length: 42 }, (_, i) => new Date(start.getFullYear(), start.getMonth(), start.getDate() + i));

  const info = usePolling(
    () =>
      open && doctorId
        ? publicApi.calendar(Number(doctorId), isoDate(cells[0]), isoDate(cells[41]))
        : Promise.resolve(null),
    0,
    [open, doctorId, month.getTime()],
  );
  const working = new Set(info.data?.working_weekdays ?? []);
  const full = new Set(info.data?.full_days ?? []);
  const offDays = new Set(info.data?.off_days ?? []);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setOpen(false);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    window.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const shift = (n: number) => setMonth((m) => new Date(m.getFullYear(), m.getMonth() + n, 1));

  return (
    <div ref={box} className="relative">
      <button
        type="button"
        disabled={!doctorId}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        className={`mt-1 w-full rounded-lg border bg-white px-3 py-2 text-left font-normal focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400 ${
          hasError ? "border-red-400" : "border-slate-300"
        }`}
      >
        {!doctorId ? "Choose a doctor first" : value ? formatDate(value) : "Select a date..."}
      </button>

      {open && doctorId && (
        <div role="dialog" aria-label="Choose a day" className="absolute left-0 z-30 mt-1 w-72 rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
          <div className="flex items-center justify-between">
            <button type="button" onClick={() => shift(-1)} aria-label="Previous month" className="rounded px-2 py-1 hover:bg-slate-100">‹</button>
            <p className="text-sm font-semibold">{month.toLocaleDateString("en-PH", { month: "long", year: "numeric" })}</p>
            <button type="button" onClick={() => shift(1)} aria-label="Next month" className="rounded px-2 py-1 hover:bg-slate-100">›</button>
          </div>
          <div className="mt-2 grid grid-cols-7 gap-1 text-center text-xs text-slate-500">
            {HEADERS.map((h) => <span key={h}>{h}</span>)}
          </div>
          <div className="mt-1 grid grid-cols-7 gap-1">
            {cells.map((d) => {
              const key = isoDate(d);
              const outside = key < minDay || key > maxDay;
              const isOff = !!info.data && (!working.has(d.getDay() || 7) || offDays.has(key));
              const isFull = !!info.data && full.has(key);
              const disabled = outside || isOff || isFull;
              const tone = isOff
                ? "bg-red-100 text-red-700"
                : isFull
                  ? "bg-amber-200 text-amber-900"
                  : outside
                    ? "text-slate-300"
                    : "hover:bg-slate-100";
              return (
                <button
                  key={key}
                  type="button"
                  disabled={disabled}
                  title={isOff ? "Doctor is not available this day" : isFull ? "Fully booked" : undefined}
                  onClick={() => {
                    onChange(key);
                    setOpen(false);
                  }}
                  className={`h-9 rounded-lg text-sm disabled:cursor-not-allowed ${tone} ${d.getMonth() !== month.getMonth() ? "opacity-40" : ""} ${
                    key === value ? "ring-2 ring-brand-600 font-semibold" : key === isoDate(new Date()) ? "border border-brand-500" : ""
                  }`}
                >
                  {d.getDate()}
                </button>
              );
            })}
          </div>
          {info.error && <p className="mt-2 text-xs text-red-700" role="alert">{info.error}</p>}
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-600">
            <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-red-100" /> Doctor off</span>
            <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-amber-200" /> Fully booked</span>
            <button
              type="button"
              className="ml-auto font-medium text-brand-700 hover:underline"
              onClick={() => setMonth(firstOfMonth(new Date()))}
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  );
}