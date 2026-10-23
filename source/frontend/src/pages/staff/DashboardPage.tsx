// Doctor and nurse dashboard: today's numbers, who is being examined, the waiting queue, and what is coming up.
import { Link } from "react-router-dom";
import { staffApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import StatCard from "../../components/StatCard";
import { cardClass } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { usePolling } from "../../hooks/usePolling";
import { formatDate, formatTime } from "../../utils/format";

export default function DashboardPage() {
  const { user } = useAuth();
  const base = `/${user?.role ?? "doctor"}`;
  const { data, error, loading } = usePolling(() => staffApi.dashboard(), 10000);

  return (
    <section>
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="mt-1 text-slate-600">Today at a glance. This page refreshes by itself.</p>

      {error && <Alert kind="error">{error}</Alert>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}

      {data && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Booked today" value={data.today.Scheduled} to={`${base}/appointments`} />
            <StatCard label="Waiting" value={data.queue.length} hint="Checked in" to={`${base}/appointments`} />
            <StatCard label="Under examination" value={data.consulting ? 1 : 0} />
            <StatCard label="Completed today" value={data.today.Completed} />
            <StatCard label="Pending requests" value={data.pending_notifications} hint="Waiting for approval" to={`${base}/notifications`} />
            <StatCard label="Awaiting payment" value={data.awaiting_payment} hint="Examined, unpaid" to={`${base}/invoice`} />
            <StatCard label="Unbilled sessions" value={data.unbilled} hint="Examined, no invoice yet" to={`${base}/invoice`} />
            <StatCard label="Cancelled today" value={data.today.Cancelled} />
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <div>
              <h2 className="text-lg font-semibold">Under examination</h2>
              <div className={`${cardClass} mt-3`}>
                {data.consulting ? (
                  <>
                    <p className="font-semibold">{data.consulting.full_name}</p>
                    <p className="text-sm text-slate-600">{data.consulting.reason ?? "No reason given"}</p>
                    <p className="mt-1 text-sm text-slate-500">Room: {data.consulting.room_name ?? "none chosen"}</p>
                  </>
                ) : (
                  <p className="text-sm text-slate-500">Nobody is being examined.</p>
                )}
              </div>

              <h2 className="mt-6 text-lg font-semibold">Waiting queue</h2>
              <ul className="mt-3 space-y-2">
                {data.queue.length === 0 && <li className="text-sm text-slate-500">No patients are waiting.</li>}
                {data.queue.map((a) => (
                  <li key={a.id} className={`${cardClass} flex items-center justify-between gap-3`}>
                    <span className="flex items-center gap-3">
                      <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-100 font-semibold text-brand-700">{a.queue_position}</span>
                      <span>
                        <span className="block font-medium">{a.full_name}</span>
                        <span className="block text-sm text-slate-500">{a.reason ?? "No reason given"}</span>
                      </span>
                    </span>
                    <span className="text-sm text-slate-500">In at {formatTime(a.checked_in_at)}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h2 className="text-lg font-semibold">Coming up</h2>
              <ul className="mt-3 space-y-2">
                {data.upcoming.length === 0 && <li className="text-sm text-slate-500">No upcoming appointments.</li>}
                {data.upcoming.map((a) => (
                  <li key={a.id} className={`${cardClass} flex items-center justify-between gap-3`}>
                    <span>
                      <span className="block font-medium">{a.full_name}</span>
                      <span className="block text-sm text-slate-500">{a.reason ?? "No reason given"}</span>
                    </span>
                    <span className="text-right text-sm text-slate-600">
                      {formatDate(a.scheduled_time)}
                      <br />
                      {formatTime(a.scheduled_time)}
                    </span>
                  </li>
                ))}
              </ul>
              <Link to={`${base}/appointments`} className="mt-3 inline-block text-sm font-medium text-brand-700 hover:underline">
                Open appointments
              </Link>
            </div>
          </div>
        </>
      )}
    </section>
  );
}