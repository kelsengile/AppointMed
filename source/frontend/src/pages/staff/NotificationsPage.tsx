import { useState } from "react";
import { staffApi } from "../../api/endpoints";
import Badge from "../../components/Badge";
import { usePolling } from "../../hooks/usePolling";
import { ageFrom, formatDate, formatDateTime } from "../../utils/format";

const FILTERS = ["Pending", "Converted", "Dismissed", "all"] as const;
type Filter = (typeof FILTERS)[number];
const tone = { Pending: "amber", Converted: "green", Dismissed: "red" } as const;

// Appointment requests: approve (creates the patient + appointment, emails them) or disapprove (emails them).
export default function NotificationsPage() {
  const [filter, setFilter] = useState<Filter>("Pending");
  const { data, error, loading, reload } = usePolling(() => staffApi.notifications(filter), 15000, [filter]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [rejecting, setRejecting] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");

  async function act(id: number, run: () => Promise<{ emailed: boolean }>, done: string) {
    setBusyId(id);
    setActionError("");
    setMessage("");
    try {
      const result = await run();
      setMessage(`${done}${result.emailed ? " The patient was emailed." : " The patient has no email on file."}`);
      setRejecting(null);
      setNote("");
      await reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Something went wrong.");
      await reload();
    } finally {
      setBusyId(null);
    }
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
            {f === "all" ? "All" : f === "Converted" ? "Approved" : f === "Dismissed" ? "Disapproved" : f}
          </button>
        ))}
      </div>

      {message && <p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{message}</p>}
      {(actionError || error) && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800" role="alert">{actionError || error}</p>}
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
              <Badge tone={tone[n.status]}>{n.status === "Converted" ? "Approved" : n.status === "Dismissed" ? "Disapproved" : n.status}</Badge>
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

            {n.status === "Pending" && rejecting !== n.id && (
              <div className="mt-4 flex gap-2">
                <button
                  disabled={busyId === n.id}
                  onClick={() => act(n.id, () => staffApi.approve(n.id), "Request approved and added to appointments.")}
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
                >
                  Approve
                </button>
                <button
                  disabled={busyId === n.id}
                  onClick={() => {
                    setRejecting(n.id);
                    setNote("");
                  }}
                  className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-60"
                >
                  Disapprove
                </button>
              </div>
            )}

            {n.status === "Pending" && rejecting === n.id && (
              <div className="mt-4 space-y-2">
                <label className="block text-sm font-medium">
                  Reason for the patient (included in the email, optional)
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                    value={note}
                    maxLength={255}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="e.g. The doctor is unavailable at that time."
                  />
                </label>
                <div className="flex gap-2">
                  <button
                    disabled={busyId === n.id}
                    onClick={() => act(n.id, () => staffApi.dismiss(n.id, note.trim() || null), "Request disapproved.")}
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