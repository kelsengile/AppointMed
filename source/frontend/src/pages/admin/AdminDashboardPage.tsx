// Admin dashboard: clinic-wide totals and the latest activity.
import { Link } from "react-router-dom";
import { adminApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import StatCard from "../../components/StatCard";
import { usePolling } from "../../hooks/usePolling";
import { formatDateTime, formatMoney } from "../../utils/format";

export default function AdminDashboardPage() {
  const { data, error, loading } = usePolling(() => adminApi.dashboard(), 15000);

  return (
    <section>
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="mt-1 text-slate-600">Clinic-wide totals and recent activity.</p>
      {error && <Alert kind="error">{error}</Alert>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}

      {data && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Active doctors" value={data.users.doctor} to="/admin/users" />
            <StatCard label="Active nurses" value={data.users.nurse} to="/admin/users" />
            <StatCard label="Active administrators" value={data.users.admin} to="/admin/users" />
            <StatCard label="Patients" value={data.patients} />
            <StatCard label="Appointments today" value={data.appointments_today} hint="Not cancelled" />
            <StatCard label="Pending requests" value={data.pending_requests} hint="Waiting for staff" />
            <StatCard label="Paid this month" value={formatMoney(data.revenue_paid_month)} to="/admin/reports" />
            <StatCard label="Unpaid invoices" value={formatMoney(data.unpaid_total)} to="/admin/reports" />
          </div>

          <div className="mt-8 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent activity</h2>
            <Link to="/admin/audits" className="text-sm font-medium text-brand-700 hover:underline">
              Open audit logs
            </Link>
          </div>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="px-3 py-2 font-medium">When</th>
                  <th className="px-3 py-2 font-medium">User</th>
                  <th className="px-3 py-2 font-medium">Action</th>
                  <th className="px-3 py-2 font-medium">Details</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_activity.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-3 py-4 text-slate-500">No activity yet.</td>
                  </tr>
                )}
                {data.recent_activity.map((row) => (
                  <tr key={row.id} className="border-t border-slate-100">
                    <td className="whitespace-nowrap px-3 py-2">{formatDateTime(row.created_at)}</td>
                    <td className="px-3 py-2">{row.username ?? "system"}</td>
                    <td className="px-3 py-2 font-medium">{row.action}</td>
                    <td className="px-3 py-2 text-slate-600">{row.details ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}