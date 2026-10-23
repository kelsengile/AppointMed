// Doctor: examines checked-in patients one at a time (room, prescription, invoice).
// Nurse: checks patients in. Both can book walk-ins, reschedule, cancel, pick rooms and set room status.
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { staffApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import ExamPanel from "../../components/ExamPanel";
import Modal from "../../components/Modal";
import WalkInModal from "../../components/WalkInModal";
import { cardClass, dangerButton, inputClass, primaryButton, secondaryButton, statusTone } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { usePolling } from "../../hooks/usePolling";
import type { AppointmentItem, RoomStatus } from "../../types";
import { ageFrom, formatTime, isoDate, toInputDateTime } from "../../utils/format";

const ROOM_STATUSES: RoomStatus[] = ["Available", "Occupied", "Maintenance"];

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
      <p className="text-sm text-slate-500">{[a.sex, ageFrom(a.birthdate), a.contact_number].filter(Boolean).join(" - ")}</p>
      <p className="mt-1 text-sm text-slate-600">{a.reason ?? "No reason given"}</p>
      {a.room_name && <p className="text-sm text-slate-500">Room: {a.room_name}</p>}
    </div>
  );
}

function RescheduleModal({ appointment, onClose, onDone }: { appointment: AppointmentItem; onClose: () => void; onDone: () => void }) {
  const [value, setValue] = useState(toInputDateTime(appointment.scheduled_time));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!value) {
      setError("Choose a new date and time.");
      return;
    }
    if (new Date(value).getTime() <= Date.now()) {
      setError("Choose a time in the future.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await staffApi.reschedule(appointment.id, value);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reschedule.");
      setBusy(false);
    }
  }

  return (
    <Modal title={`Reschedule ${appointment.full_name}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <label className="block text-sm font-medium">
          New date and time
          <input type="datetime-local" className={`${inputClass} mt-1`} value={value} onChange={(e) => setValue(e.target.value)} />
        </label>
        {error && <Alert kind="error">{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className={secondaryButton}>
            Cancel
          </button>
          <button type="submit" disabled={busy} className={primaryButton}>
            {busy ? "Saving..." : "Reschedule"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function AppointmentsPage() {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  const today = isoDate(new Date());
  const [day, setDay] = useState(today);
  const board = usePolling(() => staffApi.dashboard(), 8000); // queue + exam room, whatever their date
  const agenda = usePolling(() => staffApi.appointments(day), 8000, [day]);
  const rooms = usePolling(() => staffApi.rooms(), 15000);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [roomBusy, setRoomBusy] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  const [success, setSuccess] = useState("");
  const [notice, setNotice] = useState("");
  const [walkIn, setWalkIn] = useState(false);
  const [moving, setMoving] = useState<AppointmentItem | null>(null);
  const [roomChoice, setRoomChoice] = useState<Record<number, string>>({});
  const seen = useRef<Set<number> | null>(null);

  const consulting = board.data?.consulting ?? null;
  const queue = board.data?.queue ?? [];
  const dayItems = agenda.data ?? [];
  const booked = dayItems.filter((a) => a.status === "Scheduled");
  const finished = dayItems.filter((a) => a.status === "Examined" || a.status === "Completed" || a.status === "Cancelled");
  const allRooms = rooms.data ?? [];
  const freeRooms = allRooms.filter((r) => r.status === "Available");

  // The doctor is told when somebody new is checked in.
  useEffect(() => {
    if (!board.data) return;
    const waiting = board.data.queue;
    const previous = seen.current;
    if (previous && isDoctor) {
      const fresh = waiting.filter((a) => !previous.has(a.id));
      if (fresh.length > 0) setNotice(`${fresh.map((a) => a.full_name).join(", ")} checked in and is waiting.`);
    }
    seen.current = new Set(waiting.map((a) => a.id));
  }, [board.data, isDoctor]);

  async function refresh() {
    await Promise.all([board.reload(), agenda.reload(), rooms.reload()]);
  }

  async function run(id: number, action: () => Promise<unknown>, done?: string) {
    setBusyId(id);
    setActionError("");
    setSuccess("");
    try {
      await action();
      if (done) setSuccess(done);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      await refresh();
      setBusyId(null);
    }
  }

  async function changeRoom(id: number, status: RoomStatus) {
    setRoomBusy(id);
    setActionError("");
    try {
      await staffApi.setRoomStatus(id, status);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not change the room.");
    } finally {
      await rooms.reload();
      setRoomBusy(null);
    }
  }

  const cancelAppointment = (a: AppointmentItem) => {
    if (!window.confirm(`Cancel ${a.full_name}'s appointment?`)) return;
    void run(a.id, () => staffApi.cancel(a.id, null), `${a.full_name}'s appointment was cancelled.`);
  };

  const errorText = actionError || board.error || agenda.error;

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Appointments</h1>
          <p className="mt-1 text-slate-600">
            {isDoctor ? "Examine checked-in patients one at a time." : "Check patients in when they arrive. Your doctor is notified."}
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm font-medium">
            Agenda for
            <input type="date" value={day} onChange={(e) => e.target.value && setDay(e.target.value)} className="ml-2 rounded-lg border border-slate-300 px-3 py-1.5" />
          </label>
          <button type="button" className={primaryButton} onClick={() => setWalkIn(true)}>
            New appointment
          </button>
        </div>
      </div>

      {notice && <Alert onClose={() => setNotice("")}>{notice}</Alert>}
      {success && <Alert kind="success" onClose={() => setSuccess("")}>{success}</Alert>}
      {errorText && <Alert kind="error">{errorText}</Alert>}
      {board.loading && !board.data && <p className="mt-6 text-slate-500">Loading...</p>}

      <Section title="Under examination" count={consulting ? 1 : 0}>
        {!consulting && <p className="text-sm text-slate-500">Nobody is being examined.</p>}
        {consulting && (
          <div className={`${cardClass} border-brand-500`}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <Who a={consulting} />
              <Badge tone="blue">Under examination</Badge>
            </div>
            {isDoctor ? (
              <>
                <ExamPanel key={consulting.id} appointment={consulting} onDone={() => void refresh()} />
                <button
                  type="button"
                  className={`${secondaryButton} mt-3`}
                  disabled={busyId === consulting.id}
                  onClick={() => run(consulting.id, () => staffApi.release(consulting.id), "The patient is back in the queue.")}
                >
                  Started by mistake? Return to queue
                </button>
              </>
            ) : (
              <p className="mt-3 text-sm text-slate-500">The doctor is examining this patient.</p>
            )}
          </div>
        )}
      </Section>

      <Section title="Queue (checked in)" count={queue.length}>
        {queue.length === 0 && <p className="text-sm text-slate-500">No patients are waiting.</p>}
        {queue.map((a) => {
          const chosenRoom = roomChoice[a.id] ?? (a.room_id && freeRooms.some((r) => r.id === a.room_id) ? String(a.room_id) : "");
          return (
            <div key={a.id} className={`${cardClass} flex flex-wrap items-center justify-between gap-3`}>
              <div className="flex items-start gap-3">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-100 font-semibold text-brand-700">{a.queue_position}</span>
                <Who a={a} />
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-sm text-slate-500">In at {formatTime(a.checked_in_at)}</span>
                {isDoctor && (
                  <>
                    <select
                      aria-label={`Room for ${a.full_name}`}
                      className={`${inputClass} w-40`}
                      value={chosenRoom}
                      onChange={(e) => setRoomChoice((prev) => ({ ...prev, [a.id]: e.target.value }))}
                    >
                      <option value="">No room</option>
                      {freeRooms.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.room_name}
                        </option>
                      ))}
                    </select>
                    <button
                      className={primaryButton}
                      disabled={busyId === a.id || consulting !== null}
                      title={consulting ? "Finish the current examination first" : undefined}
                      onClick={() => run(a.id, () => staffApi.start(a.id, chosenRoom ? Number(chosenRoom) : null))}
                    >
                      Start examination
                    </button>
                  </>
                )}
                <button className={dangerButton} disabled={busyId === a.id} onClick={() => cancelAppointment(a)}>
                  Cancel
                </button>
              </div>
            </div>
          );
        })}
      </Section>

      <Section title="Booked / Agenda" count={booked.length}>
        {booked.length === 0 && <p className="text-sm text-slate-500">No booked appointments on this day.</p>}
        {booked.map((a) => {
          const later = a.scheduled_time.slice(0, 10) > today;
          return (
            <div key={a.id} className={`${cardClass} flex flex-wrap items-center justify-between gap-3`}>
              <div className="flex items-start gap-4">
                <p className="w-20 shrink-0 font-semibold text-brand-700">{formatTime(a.scheduled_time)}</p>
                <Who a={a} />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="slate">{a.source}</Badge>
                <select
                  aria-label={`Room for ${a.full_name}`}
                  className={`${inputClass} w-36`}
                  value={a.room_id ?? ""}
                  disabled={busyId === a.id}
                  onChange={(e) => run(a.id, () => staffApi.assignRoom(a.id, e.target.value ? Number(e.target.value) : null))}
                >
                  <option value="">No room</option>
                  {allRooms
                    .filter((r) => r.status !== "Maintenance" || r.id === a.room_id)
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.room_name}
                      </option>
                    ))}
                </select>
                <button
                  className={primaryButton}
                  disabled={busyId === a.id || later}
                  title={later ? "Only today's appointments can be checked in" : undefined}
                  onClick={() => run(a.id, () => staffApi.checkIn(a.id), `${a.full_name} was added to the queue.`)}
                >
                  Check in
                </button>
                <button className={secondaryButton} disabled={busyId === a.id} onClick={() => setMoving(a)}>
                  Reschedule
                </button>
                <button className={dangerButton} disabled={busyId === a.id} onClick={() => cancelAppointment(a)}>
                  Cancel
                </button>
              </div>
            </div>
          );
        })}
      </Section>

      {finished.length > 0 && (
        <Section title="Finished or cancelled on this day" count={finished.length}>
          {finished.map((a) => (
            <div key={a.id} className={`${cardClass} flex flex-wrap items-center justify-between gap-3`}>
              <div className="flex items-start gap-4">
                <p className="w-20 shrink-0 font-semibold text-slate-500">{formatTime(a.scheduled_time)}</p>
                <Who a={a} />
              </div>
              <Badge tone={statusTone(a.status)}>{a.status}</Badge>
            </div>
          ))}
        </Section>
      )}

      {(board.data?.awaiting_payment ?? 0) > 0 && (
        <Alert kind="warning">
          {board.data?.awaiting_payment} examined patient(s) are waiting to pay.{" "}
          <Link to={`/${user?.role ?? "doctor"}/invoice`} className="font-medium underline">
            Open invoices
          </Link>
        </Alert>
      )}

      <Section title="Rooms" count={allRooms.length}>
        {allRooms.length === 0 && <p className="text-sm text-slate-500">No rooms yet. An administrator can add them.</p>}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {allRooms.map((r) => (
            <div key={r.id} className={cardClass}>
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold">{r.room_name}</p>
                <Badge tone={statusTone(r.status)}>{r.status}</Badge>
              </div>
              <p className="mt-1 text-sm text-slate-500">{r.occupant ? `In use by ${r.occupant}` : "Nobody inside"}</p>
              <select
                aria-label={`Status of ${r.room_name}`}
                className={`${inputClass} mt-3`}
                value={r.status}
                disabled={roomBusy === r.id}
                onChange={(e) => changeRoom(r.id, e.target.value as RoomStatus)}
              >
                {ROOM_STATUSES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </Section>

      {walkIn && (
        <WalkInModal
          onClose={() => setWalkIn(false)}
          onCreated={(name) => {
            setWalkIn(false);
            setSuccess(`Appointment created for ${name}.`);
            void refresh();
          }}
        />
      )}
      {moving && (
        <RescheduleModal
          appointment={moving}
          onClose={() => setMoving(null)}
          onDone={() => {
            setSuccess(`${moving.full_name}'s appointment was moved.`);
            setMoving(null);
            void refresh();
          }}
        />
      )}
    </section>
  );
}