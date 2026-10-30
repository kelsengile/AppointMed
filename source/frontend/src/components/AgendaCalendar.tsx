// Date picker for the agenda. Red = doctor does not work that day. Yellow = bookings or pending requests.
// Doctors (only) get a "Manage days off" mode to mark a date unavailable or available again.
// The reason for a day off is shown under the calendar when you hover, focus, or select that day.
import { useEffect, useRef, useState, type FormEvent } from "react";
import { staffApi } from "../api/endpoints";
import { useAuth } from "../context/AuthContext";
import { usePolling } from "../hooks/usePolling";
import { formatDate, isoDate } from "../utils/format";
import { cleanText } from "../utils/input";
import Alert from "./Alert";
import Modal from "./Modal";
import { inputClass, primaryButton, secondaryButton } from "./ui";

const HEADERS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const firstOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1);

// Replaces window.prompt / window.confirm. Marks a day unavailable (with an optional reason)
// or, when the day is already off, asks to make it available again.
function DayOffModal({
  day,
  reason,
  isOff,
  onClose,
  onDone,
}: {
  day: string;
  reason: string | null | undefined;
  isOff: boolean;
  onClose: () => void;
  onDone: () => void;
}) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (isOff) await staffApi.clearDayOff(day);
      else await staffApi.setDayOff(day, text.trim() || null);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change that day.");
      setBusy(false);
    }
  }

  return (
    <Modal title={isOff ? "Make this day available?" : "Mark this day as unavailable"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <p className="text-sm text-slate-700">
          <span className="font-medium">{formatDate(day)}</span>
        </p>
        {isOff ? (
          <>
            <p className="text-sm text-slate-600">Reason given: {reason || "none"}</p>
            <p className="text-sm text-slate-600">Patients will be able to book this day again.</p>
          </>
        ) : (
          <>
            <label className="block text-sm font-medium">
              Reason (optional)
              <input
                className={`${inputClass} mt-1`}
                maxLength={255}
                autoFocus
                autoComplete="off"
                placeholder="e.g. Attending a medical conference"
                value={text}
                onChange={(e) => setText(cleanText(e.target.value, 255))}
              />
            </label>
            <p className="text-xs text-slate-500">
              Staff can see this reason. Do not enter medical details. Patients on the booking page only see that the day is unavailable.
            </p>
          </>
        )}
        {error && <Alert kind="error">{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className={secondaryButton}>
            Cancel
          </button>
          <button type="submit" disabled={busy} className={primaryButton}>
            {busy ? "Saving..." : isOff ? "Make available" : "Mark unavailable"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function AgendaCalendar({
  value,
  onChange,
  onChanged,
}: {
  value: string;
  onChange: (day: string) => void;
  /** Called after a day off is added or removed, so the page can refresh its own banner. */
  onChanged?: () => void;
}) {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  const [open, setOpen] = useState(false);
  const [manage, setManage] = useState(false);
  const [hover, setHover] = useState<string | null>(null);
  const [target, setTarget] = useState<string | null>(null); // the day shown in the day-off dialog
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
  const daysOff = new Map((info.data?.off_days ?? []).map((d) => [d.day, d.reason]));

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setOpen(false);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && !target && setOpen(false);
    document.addEventListener("mousedown", onClick);
    window.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      window.removeEventListener("keydown", onKey);
    };
  }, [open, target]);

  const shift = (n: number) => setMonth((m) => new Date(m.getFullYear(), m.getMonth() + n, 1));
  const today = isoDate(new Date());

  // The line under the grid describes the hovered day, or else the selected day.
  const shownDay = hover ?? value;
  const shownIsOff = daysOff.has(shownDay);
  const shownReason = daysOff.get(shownDay);

  async function dayOffChanged() {
    setTarget(null);
    await info.reload();
    onChanged?.();
  }

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
          <div className="mt-1 grid grid-cols-7 gap-1" onMouseLeave={() => setHover(null)}>
            {cells.map((d) => {
              const key = isoDate(d);
              const isDayOff = daysOff.has(key);
              const isBusy = busy.has(key);
              const isOff = !!info.data && !working.has(d.getDay() || 7);
              const tone = isDayOff
                ? "bg-red-200 text-red-900 font-medium"
                : isBusy
                  ? "bg-amber-200 text-amber-900"
                  : isOff
                    ? "bg-red-100 text-red-700"
                    : "hover:bg-slate-100";
              const pastInManage = manage && key < today; // days off can only be set from today on
              return (
                <button
                  key={key}
                  type="button"
                  disabled={pastInManage}
                  onMouseEnter={() => setHover(key)}
                  onFocus={() => setHover(key)}
                  onBlur={() => setHover(null)}
                  onClick={() => {
                    if (manage) {
                      setTarget(key);
                      return;
                    }
                    onChange(key);
                    setOpen(false);
                  }}
                  className={`h-9 rounded-lg text-sm disabled:cursor-not-allowed disabled:opacity-30 ${tone} ${d.getMonth() !== month.getMonth() ? "opacity-40" : ""} ${
                    key === value ? "ring-2 ring-brand-600 font-semibold" : key === today ? "border border-brand-500" : ""
                  }`}
                >
                  {d.getDate()}
                </button>
              );
            })}
          </div>

          {/* Visible on touch screens too, unlike a hover tooltip. */}
          {shownIsOff && (
            <p className="mt-2 rounded-lg bg-red-50 p-2 text-xs text-red-900" role="status">
              <span className="font-medium">{formatDate(shownDay)}: unavailable.</span> {shownReason ? `Reason: ${shownReason}` : "No reason given."}
            </p>
          )}

          {manage && (
            <p className="mt-2 rounded-lg bg-sky-50 p-2 text-xs text-sky-900">
              Click a day to mark it unavailable. Click a dark red day to make it available again.
            </p>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-600">
            <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-red-100" /> Not a working day</span>
            <span className="flex items-center gap-1"><i className="h-3 w-3 rounded bg-red-200" /> Day off</span>
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

          {isDoctor && (
            <button
              type="button"
              onClick={() => setManage((m) => !m)}
              className={`mt-3 w-full rounded-lg px-3 py-1.5 text-sm font-medium ${
                manage ? "bg-brand-600 text-white hover:bg-brand-700" : "border border-slate-300 hover:bg-slate-50"
              }`}
            >
              {manage ? "Done" : "Manage days off"}
            </button>
          )}
        </div>
      )}

      {/* Rendered outside the popup so the dialog stays open if the popup closes. */}
      {target && (
        <DayOffModal
          day={target}
          isOff={daysOff.has(target)}
          reason={daysOff.get(target)}
          onClose={() => setTarget(null)}
          onDone={() => void dayOffChanged()}
        />
      )}
    </div>
  );
}