// Edits a doctor's weekly working hours. The booking page builds its open time slots from this.
import { useEffect, useRef, useState } from "react";
import { adminApi } from "../api/endpoints";
import type { ScheduleBlock, UserRecord } from "../types";
import { WEEKDAY_NAMES } from "../utils/format";
import Alert from "./Alert";
import Modal from "./Modal";
import { inputClass, primaryButton, secondaryButton } from "./ui";

interface Row extends ScheduleBlock {
  key: number; // client-side id so React can track rows
}

function toMinutes(value: string): number {
  const [hours, minutes] = value.split(":");
  return Number(hours) * 60 + Number(minutes);
}

/** Returns a message for the first problem found, or "" when the schedule is valid. */
function check(blocks: ScheduleBlock[]): string {
  for (const b of blocks) {
    if (!b.start_time || !b.end_time) return "Fill in the start and end time of every block.";
    if (toMinutes(b.end_time) <= toMinutes(b.start_time)) return "Each block must end after it starts.";
    if (toMinutes(b.end_time) - toMinutes(b.start_time) < b.slot_minutes) return "A block must be at least one slot long.";
    if (!Number.isInteger(b.slot_minutes) || b.slot_minutes < 5 || b.slot_minutes > 120) return "A slot must be 5 to 120 minutes.";
  }
  const sorted = [...blocks].sort((a, b) => a.weekday - b.weekday || toMinutes(a.start_time) - toMinutes(b.start_time));
  for (let i = 1; i < sorted.length; i += 1) {
    if (sorted[i].weekday === sorted[i - 1].weekday && toMinutes(sorted[i].start_time) < toMinutes(sorted[i - 1].end_time)) {
      return `Blocks on ${WEEKDAY_NAMES[sorted[i].weekday - 1]} overlap.`;
    }
  }
  return "";
}

export default function ScheduleEditor({ doctor, onClose, onSaved }: { doctor: UserRecord; onClose: () => void; onSaved: () => void }) {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const nextKey = useRef(1);

  useEffect(() => {
    let cancelled = false;
    adminApi
      .schedule(doctor.id)
      .then((blocks) => {
        if (!cancelled) setRows(blocks.map((b) => ({ ...b, key: nextKey.current++ })));
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load the schedule.");
      });
    return () => {
      cancelled = true;
    };
  }, [doctor.id]);

  function update(key: number, patch: Partial<ScheduleBlock>) {
    setRows((prev) => (prev ? prev.map((r) => (r.key === key ? { ...r, ...patch } : r)) : prev));
  }

  function add(weekday: number) {
    setRows((prev) => [...(prev ?? []), { key: nextKey.current++, weekday, start_time: "08:00", end_time: "12:00", slot_minutes: 30 }]);
  }

  async function save() {
    if (!rows) return;
    const blocks: ScheduleBlock[] = rows.map((r) => ({
      weekday: r.weekday,
      start_time: r.start_time,
      end_time: r.end_time,
      slot_minutes: Number(r.slot_minutes),
    }));
    const problem = check(blocks);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    setError("");
    try {
      await adminApi.saveSchedule(doctor.id, blocks);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save the schedule.");
      setBusy(false);
    }
  }

  return (
    <Modal title={`Working hours: ${doctor.full_name}`} onClose={onClose} wide>
      {!rows && !error && <p className="text-slate-500">Loading...</p>}
      {rows && (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Add one block per stretch of work. Use two blocks on a day for a lunch break. Patients can only book inside these blocks.
          </p>
          {WEEKDAY_NAMES.map((name, index) => {
            const weekday = index + 1;
            const dayRows = rows.filter((r) => r.weekday === weekday).sort((a, b) => toMinutes(a.start_time) - toMinutes(b.start_time));
            return (
              <div key={weekday} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{name}</p>
                  <button type="button" onClick={() => add(weekday)} className="rounded-lg border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50">
                    Add block
                  </button>
                </div>
                {dayRows.length === 0 && <p className="mt-1 text-sm text-slate-500">Day off.</p>}
                {dayRows.map((r) => (
                  <div key={r.key} className="mt-2 flex flex-wrap items-center gap-2">
                    <input type="time" aria-label={`${name} start`} className={`${inputClass} w-32`} value={r.start_time} onChange={(e) => update(r.key, { start_time: e.target.value })} />
                    <span className="text-sm text-slate-500">to</span>
                    <input type="time" aria-label={`${name} end`} className={`${inputClass} w-32`} value={r.end_time} onChange={(e) => update(r.key, { end_time: e.target.value })} />
                    <label className="flex items-center gap-1 text-sm">
                      <input type="number" min={5} max={120} aria-label={`${name} slot minutes`} className={`${inputClass} w-20`} value={r.slot_minutes} onChange={(e) => update(r.key, { slot_minutes: Number(e.target.value) })} />
                      min slots
                    </label>
                    <button type="button" onClick={() => setRows((prev) => (prev ? prev.filter((x) => x.key !== r.key) : prev))} className="rounded-lg px-2 py-1 text-sm text-red-700 hover:bg-red-50">
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
      {error && <Alert kind="error">{error}</Alert>}
      <div className="mt-4 flex justify-end gap-2">
        <button type="button" onClick={onClose} className={secondaryButton}>
          Cancel
        </button>
        <button type="button" disabled={busy || !rows} onClick={save} className={primaryButton}>
          {busy ? "Saving..." : "Save schedule"}
        </button>
      </div>
    </Modal>
  );
}