import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { staffApi } from "../../api/endpoints";
import Badge from "../../components/Badge";
import ExamPanel from "../../components/ExamPanel";
import { useAuth } from "../../context/AuthContext";
import { usePolling } from "../../hooks/usePolling";
import type { AppointmentItem } from "../../types";
import { ageFrom, formatMoney, formatTime, isoDate } from "../../utils/format";

function Section({ title, count, children }: { title: string; count: number; children: ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="flex items-center gap-2 text-lg font-semibold">
        {title} <span className="rounded-full bg-slate-200 px-2 text-sm font-medium text-slate-700">{count}</span>
      </h2>
      <div className="mt-3 space-y-3">{children}</div>
    </section>
  );
}

function Who({ a }: { a: AppointmentItem }) {
  return (
    <div>
      <p className="font-semibold">{a.full_name}</p>
      <p className="text-sm text-slate-500">
        {[a.sex, ageFrom(a.birthdate), a.contact_number].filter(Boolean).join(" - ")}
      </p>
      <p className="mt-1 text-sm text-slate-600">{a.reason ?? "No reason given"}</p>
    </div>
  );
}

const card = "rounded-xl border border-slate-200 bg-white p-4";
const primary = "rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60";

// Doctor: starts and finishes examinations (one at a time). Nurse: checks patients in (the doctor cannot).
export default function AppointmentsPage() {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  const [day, setDay] = useState(isoDate(new Date()));
  const { data, error, loading, reload } = usePolling(() => staffApi.appointments(day), 8000, [day]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const seen = useRef<Set<number> | null>(null);

  const all = data ?? [];
  const consulting = all.filter((a) => a.status === "Consulting");
  const queue = all
    .filter((a) => a.status === "Checked-in")
    .sort((x, y) => (x.checked_in_at ?? "").localeCompare(y.checked_in_at ?? ""));
  const agenda = all.filter((a) => a.status === "Scheduled");
  const unpaid = all.filter((a) => a.status === "Examined");

  // The doctor is told when the nurse checks someone in.
  useEffect(() => {
    if (!data) return;
    const waiting = data.filter((a) => a.status === "Checked-in");
    const previous = seen.current;
    if (previous && isDoctor) {
      const fresh = waiting.filter((a) => !previous.has(a.id));
      if (fresh.length > 0) setNotice(`${fresh.map((a) => a.full_name).join(", ")} checked in and is waiting.`);
    }
    seen.current = new Set(waiting.map((a) => a.id));
  }, [data, isDoctor]);

  async function run(id: number, action: () => Promise<unknown>) {
    setBusyId(id);
    setActionError("");
    try {
      await action();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      await reload();
      setBusyId(null);
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Appointments</h1>
          <p className="mt-1 text-slate-600">
            {isDoctor ? "Examine checked-in patients one at a time." : "Check patients in when they arrive. Your doctor is notified."}
          </p>
        </div>
        <label className="text-sm font-medium">
          Agenda for
          <input type="date" value={day} onChange={(e) => e.target.value && setDay(e.target.value)} className="ml-2 rounded-lg border border-slate-300 px-3 py-1.5" />
        </label>
      </div>

      {notice && (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-lg bg-sky-50 p-3 text-sm text-sky-900" role="status">
          <span>{notice}</span>
          <button onClick={() => setNotice("")} className="rounded px-2 py-1 hover:bg-sky-100">Dismiss</button>
        </div>
      )}
      {(actionError || error) && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800" role="alert">{actionError || error}</p>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}

      <Section title="Under examination" count={consulting.length}>
        {consulting.length === 0 && <p className="text-sm text-slate-500">Nobody is being examined.</p>}
        {consulting.map((a) => (
          <div key={a.id} className={`${card} border-brand-500`}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <Who a={a} />
              <Badge tone="blue">Under examination</Badge>
            </div>
            {isDoctor ? (
              <ExamPanel appointment={a} onDone={() => void reload()} />
            ) : (
              <p className="mt-3 text-sm text-slate-500">The doctor is examining this patient.</p>
            )}
          </div>
        ))}
      </Section>

      <Section title="Queue (checked in)" count={queue.length}>
        {queue.length === 0 && <p className="text-sm text-slate-500">No patients are waiting.</p>}
        {queue.map((a, index) => (
          <div key={a.id} className={`${card} flex flex-wrap items-center justify-between gap-3`}>
            <div className="flex items-start gap-3">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-100 font-semibold text-brand-700">{index + 1}</span>
              <Who a={a} />
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-500">In at {formatTime(a.checked_in_at)}</span>
              {isDoctor ? (
                <button
                  className={primary}
                  disabled={busyId === a.id || consulting.length > 0}
                  title={consulting.length > 0 ? "Finish the current examination first" : undefined}
                  onClick={() => run(a.id, () => staffApi.start(a.id))}
                >
                  Start examination
                </button>
              ) : (
                <button
                  className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-60"
                  disabled={busyId === a.id}
                  onClick={() => window.confirm(`Cancel ${a.full_name}'s appointment?`) && run(a.id, () => staffApi.cancel(a.id))}
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        ))}
      </Section>

      <Section title="Booked / Agenda" count={agenda.length}>
        {agenda.length === 0 && <p className="text-sm text-slate-500">No booked appointments on this day.</p>}
        {agenda.map((a) => (
          <div key={a.id} className={`${card} flex flex-wrap items-center justify-between gap-3`}>
            <div className="flex items-start gap-4">
              <p className="w-20 shrink-0 font-semibold text-brand-700">{formatTime(a.scheduled_time)}</p>
              <Who a={a} />
            </div>
            <div className="flex items-center gap-2">
              <Badge tone="slate">{a.source}</Badge>
              {!isDoctor && (
                <>
                  <button className={primary} disabled={busyId === a.id} onClick={() => run(a.id, () => staffApi.checkIn(a.id))}>
                    Check in
                  </button>
                  <button
                    className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-60"
                    disabled={busyId === a.id}
                    onClick={() => window.confirm(`Cancel ${a.full_name}'s appointment?`) && run(a.id, () => staffApi.cancel(a.id))}
                  >
                    Cancel
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </Section>

      {unpaid.length > 0 && (
        <Section title="Awaiting payment" count={unpaid.length}>
          {unpaid.map((a) => (
            <div key={a.id} className={`${card} flex flex-wrap items-center justify-between gap-3`}>
              <Who a={a} />
              <div className="flex items-center gap-3">
                <span className="font-semibold">{formatMoney(a.invoice_amount)}</span>
                <Link to="../invoice" className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50">
                  Open invoice
                </Link>
              </div>
            </div>
          ))}
        </Section>
      )}
    </section>
  );
}