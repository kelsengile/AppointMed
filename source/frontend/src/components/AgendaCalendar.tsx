// Date picker for the agenda. Red = doctor does not work that weekday. Yellow = bookings or pending requests.
import { useEffect, useRef, useState } from "react";
import { staffApi } from "../api/endpoints";
import { usePolling } from "../hooks/usePolling";
import { formatDate, isoDate } from "../utils/format";

const HEADERS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const firstOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1);

export default function AgendaCalendar({ value, onChange }: { value: string; onChange: (day: string) => void }) {
  const [open, setOpen] = useState(false);
  const [month, setMonth] = useState(() => firstOfMonth(new Date(`${value}T00:00:00`)));
  const box = useRef<HTMLDivElement>(null);

  // 6 weeks starting on the Monday on or before the 1st, so every month fits the same grid.
  const start = new Date(month.getFullYear(), month.getMonth(), 1 - ((month.getDay() + 6) % 7));
  const cells = Array.from({ length: 42 }, (_, i) => new Date(start.getFullYear(), start.getMonth(), start.getDate() + i));

  const info = usePolling(
    () => (open ? staffApi.calendar(isoDate(cells[0]), isoDate(cells[41])) : Promise.resolve(null)),
    0,
    [open, month.getTime()],
  );
  const working = new Set(info.data?.working_weekdays ?? []);
  const busy = new Set(info.data?.busy_days ?? []);

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
  const today = isoDate(new Date());

  return (
    <div ref={box} className="relative ml-2 inline-block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-left font-normal"
      >
        {formatDate(value)}
      </button>
      {open && (
        <div role="dialog" aria-label="Choose a day" className="absolute right-0 z-30 mt-1 w-72 rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
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
              const isBusy = busy.has(key);
              const isOff = !!info.data && !working.has(d.getDay() || 7);
              const tone = isBusy ? "bg-amber-200 text-amber-900" : isOff ? "bg-red-100 text-red-700" : "hover:bg-slate-100";
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => {
                    onChange(key);
                    setOpen(false);
                  }}
                  className={`h-9 rounded-lg text-sm ${tone} ${d.getMonth() !== month.getMonth() ? "opacity-40" : ""} ${
                    key === value ? "ring-2 ring-brand-600 font-semibold" : key === today ? "border border-brand-500" : ""
                  }`}
                >
                  {d.getDate()}
                </button>
              );
            })}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-600">
            <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-red-100" /> Doctor off</span>
            <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-amber-200" /> Booked / pending</span>
            <button
              type="button"
              className="ml-auto font-medium text-brand-700 hover:underline"
              onClick={() => {
                onChange(today);
                setMonth(firstOfMonth(new Date())); // the grid math needs the 1st of the month
                setOpen(false);
              }}
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  );
}