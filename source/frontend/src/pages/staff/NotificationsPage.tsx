// Appointment requests: approve (creates the patient and appointment, emails them) or disapprove (emails the reason).
import { useState } from "react";
import { staffApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import { inputClass, primaryButton, secondaryButton, statusTone } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import type { NotificationItem } from "../../types";
import { ageFrom, formatDate, formatDateTime, toInputDateTime } from "../../utils/format";

const FILTERS = ["Pending", "Converted", "Dismissed", "all"] as const;
type Filter = (typeof FILTERS)[number];
const LABEL = { Pending: "Pending", Converted: "Approved", Dismissed: "Disapproved" } as const;

export default function NotificationsPage() {
  const [filter, setFilter] = useState<Filter>("Pending");
  const { data, error, loading, reload } = usePolling(() => staffApi.notifications(filter), 15000, [filter]);
  const rooms = usePolling(() => staffApi.rooms(), 0);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [approving, setApproving] = useState<number | null>(null);
  const [rejecting, setRejecting] = useState<number | null>(null);
  const [when, setWhen] = useState("");
  const [room, setRoom] = useState("");
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");

  async function act(id: number, run: () => Promise<unknown>, done: string) {
    setBusyId(id);
    setActionError("");
    setMessage("");
    try {
      await run();
      setMessage(done);
      setApproving(null);
      setRejecting(null);
      setNote("");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      await reload();
      setBusyId(null);
    }
  }

  function startApproval(n: NotificationItem) {
    setRejecting(null);
    setApproving(n.id);
    setWhen(toInputDateTime(n.preferred_datetime));
    setRoom("");
  }

  function confirmApproval(n: NotificationItem) {
    if (!when) {
      setActionError("Choose a date and time for the appointment.");
      return;
    }
    const mailed = n.email ? ` A confirmation was emailed to ${n.email}.` : " The patient has no email on file.";
    void act(n.id, () => staffApi.approve(n.id, { scheduled_time: when, room_id: room ? Number(room) : null }), `Request approved and added to appointments.${mailed}`);
  }

  function confirmDisapproval(n: NotificationItem) {
    if (note.trim().length < 3) {
      setActionError("Enter a short reason for the patient (at least 3 characters).");
      return;
    }
    const mailed = n.email ? ` The reason was emailed to ${n.email}.` : " The patient has no email on file.";
    void act(n.id, () => staffApi.dismiss(n.id, note.trim()), `Request disapproved.${mailed}`);
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">Notifications</h1>
      <p className="mt-1 text-slate-600">Appointment requests from the booking page. Approve to add the patient and the appointment.</p>

      <div className="mt-4 flex flex-wrap gap-2" role="tablist" aria-label="Request status">
        {FILTERS.map((f) => (
          <button
            key={f}
            role="tab"
            aria-selected={filter === f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-sm ${filter === f ? "bg-brand-600 text-white" : "border border-slate-300 bg-white hover:bg-slate-50"}`}
          >
            {f === "all" ? "All" : LABEL[f]}
          </button>
        ))}
      </div>

      {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
      {(actionError || error) && <Alert kind="error">{actionError || error}</Alert>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}
      {data && data.length === 0 && <p className="mt-6 text-slate-500">Nothing here.</p>}

      <ul className="mt-4 space-y-4">
        {data?.map((n) => (
          <li key={n.id} className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h2 className="font-semibold">{n.requester_name}</h2>
                <p className="text-sm text-slate-500">
                  {[n.sex, ageFrom(n.birthdate), n.birthdate ? `born ${formatDate(n.birthdate)}` : ""].filter(Boolean).join(" - ")}
                </p>
              </div>
              <Badge tone={statusTone(n.status)}>{LABEL[n.status]}</Badge>
            </div>
            <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
              <div><dt className="inline font-medium">Requested time: </dt><dd className="inline">{formatDateTime(n.preferred_datetime)}</dd></div>
              <div><dt className="inline font-medium">Reason: </dt><dd className="inline">{n.reason ?? "-"}</dd></div>
              <div><dt className="inline font-medium">Contact: </dt><dd className="inline">{n.contact_number ?? "-"}</dd></div>
              <div><dt className="inline font-medium">Email: </dt><dd className="inline">{n.email ?? "-"}</dd></div>
              <div className="sm:col-span-2"><dt className="inline font-medium">Address: </dt><dd className="inline">{n.address ?? "-"}</dd></div>
              <div><dt className="inline font-medium">Received: </dt><dd className="inline">{formatDateTime(n.created_at)} ({n.origin})</dd></div>
              {n.decision_note && <div className="sm:col-span-2"><dt className="inline font-medium">Reason given: </dt><dd className="inline">{n.decision_note}</dd></div>}
            </dl>

            {n.status === "Pending" && n.slot_taken && (
              <Alert kind="warning">That time is already booked for this doctor. Choose another time before approving.</Alert>
            )}

            {n.status === "Pending" && approving !== n.id && rejecting !== n.id && (
              <div className="mt-4 flex gap-2">
                <button disabled={busyId === n.id} onClick={() => startApproval(n)} className={primaryButton}>
                  Approve
                </button>
                <button
                  disabled={busyId === n.id}
                  onClick={() => {
                    setApproving(null);
                    setRejecting(n.id);
                    setNote("");
                  }}
                  className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-60"
                >
                  Disapprove
                </button>
              </div>
            )}

            {n.status === "Pending" && approving === n.id && (
              <div className="mt-4 space-y-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="block text-sm font-medium">
                    Appointment time (change it if needed)
                    <input type="datetime-local" className={`${inputClass} mt-1`} value={when} onChange={(e) => setWhen(e.target.value)} />
                  </label>
                  <label className="block text-sm font-medium">
                    Exam room (optional)
                    <select className={`${inputClass} mt-1`} value={room} onChange={(e) => setRoom(e.target.value)}>
                      <option value="">No room yet</option>
                      {rooms.data
                        ?.filter((r) => r.status !== "Maintenance")
                        .map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.room_name}
                          </option>
                        ))}
                    </select>
                  </label>
                </div>
                <div className="flex gap-2">
                  <button disabled={busyId === n.id} onClick={() => confirmApproval(n)} className={primaryButton}>
                    Confirm approval
                  </button>
                  <button onClick={() => setApproving(null)} className={secondaryButton}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {n.status === "Pending" && rejecting === n.id && (
              <div className="mt-4 space-y-2">
                <label className="block text-sm font-medium">
                  Reason for the patient (included in the email)
                  <input
                    className={`${inputClass} mt-1`}
                    value={note}
                    maxLength={255}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="e.g. The doctor is unavailable at that time."
                  />
                </label>
                <div className="flex gap-2">
                  <button
                    disabled={busyId === n.id}
                    onClick={() => confirmDisapproval(n)}
                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
                  >
                    Confirm disapproval
                  </button>
                  <button onClick={() => setRejecting(null)} className="rounded-lg px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}