// Admin: appointment and billing summaries for a date range, with CSV downloads.
import { useState } from "react";
import { adminApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import StatCard from "../../components/StatCard";
import { inputClass, secondaryButton } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import { downloadCsv } from "../../utils/csv";
import { formatDate, formatMoney, isoDate, toNumber } from "../../utils/format";

function Bar({ value, max }: { value: number; max: number }) {
  const percent = value > 0 && max > 0 ? Math.max(2, Math.round((value / max) * 100)) : 0;
  return (
    <div className="h-2 w-full min-w-16 rounded-full bg-slate-100">
      <div className="h-2 rounded-full bg-brand-500" style={{ width: `${percent}%` }} />
    </div>
  );
}

export default function ReportsPage() {
  const [from, setFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 29);
    return isoDate(d);
  });
  const [to, setTo] = useState(() => isoDate(new Date()));
  const report = usePolling(() => adminApi.reports(from, to), 0, [from, to]);
  const data = report.data;

  const maxStatus = Math.max(0, ...(data?.status_counts.map((s) => toNumber(s.count)) ?? []));
  const maxDaily = Math.max(0, ...(data?.daily.map((d) => toNumber(d.revenue)) ?? []));

  function downloadDaily() {
    if (!data) return;
    downloadCsv(`daily-report_${from}_${to}.csv`, [
      ["Date", "Appointments", "Revenue paid"],
      ...data.daily.map((d) => [d.day, toNumber(d.appointments), toNumber(d.revenue)]),
    ]);
  }

  function downloadDoctors() {
    if (!data) return;
    downloadCsv(`doctor-report_${from}_${to}.csv`, [
      ["Doctor", "Appointments", "Completed", "Cancelled", "Revenue paid", "Revenue unpaid"],
      ...data.per_doctor.map((d) => [d.doctor_name, toNumber(d.appointments), toNumber(d.completed), toNumber(d.cancelled), toNumber(d.revenue_paid), toNumber(d.revenue_unpaid)]),
    ]);
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">Reports</h1>
      <p className="mt-1 text-slate-600">Appointments and billing summaries.</p>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="text-sm font-medium">
          From
          <input type="date" className={`${inputClass} mt-1`} value={from} max={to} onChange={(e) => e.target.value && setFrom(e.target.value)} />
        </label>
        <label className="text-sm font-medium">
          To
          <input type="date" className={`${inputClass} mt-1`} value={to} min={from} onChange={(e) => e.target.value && setTo(e.target.value)} />
        </label>
        <button type="button" className={secondaryButton} disabled={!data} onClick={downloadDaily}>
          Download daily CSV
        </button>
        <button type="button" className={secondaryButton} disabled={!data} onClick={downloadDoctors}>
          Download doctors CSV
        </button>
      </div>

      {report.error && <Alert kind="error">{report.error}</Alert>}
      {report.loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}

      {data && (
        <>
          <p className="mt-4 text-sm text-slate-500">
            {formatDate(data.date_from)} to {formatDate(data.date_to)}
          </p>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard label="Appointments" value={data.totals.appointments} />
            <StatCard label="Completed" value={data.totals.completed} />
            <StatCard label="Cancelled" value={data.totals.cancelled} />
            <StatCard label="Revenue paid" value={formatMoney(data.totals.revenue_paid)} />
            <StatCard label="Revenue unpaid" value={formatMoney(data.totals.revenue_unpaid)} />
            <StatCard label="New patients" value={data.totals.new_patients} />
          </div>

          <h2 className="mt-8 text-lg font-semibold">Appointments by status</h2>
          <div className="mt-3 rounded-xl border border-slate-200 bg-white p-4">
            {data.status_counts.length === 0 && <p className="text-sm text-slate-500">No appointments in this range.</p>}
            <ul className="space-y-3">
              {data.status_counts.map((s) => (
                <li key={s.status} className="grid grid-cols-[8rem_1fr_3rem] items-center gap-3 text-sm">
                  <span>{s.status}</span>
                  <Bar value={toNumber(s.count)} max={maxStatus} />
                  <span className="text-right font-medium">{toNumber(s.count)}</span>
                </li>
              ))}
            </ul>
          </div>

          <h2 className="mt-8 text-lg font-semibold">By doctor</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="px-3 py-2 font-medium">Doctor</th>
                  <th className="px-3 py-2 text-right font-medium">Appointments</th>
                  <th className="px-3 py-2 text-right font-medium">Completed</th>
                  <th className="px-3 py-2 text-right font-medium">Cancelled</th>
                  <th className="px-3 py-2 text-right font-medium">Paid</th>
                  <th className="px-3 py-2 text-right font-medium">Unpaid</th>
                </tr>
              </thead>
              <tbody>
                {data.per_doctor.map((d) => (
                  <tr key={d.doctor_id} className="border-t border-slate-100">
                    <td className="px-3 py-2 font-medium">{d.doctor_name}</td>
                    <td className="px-3 py-2 text-right">{toNumber(d.appointments)}</td>
                    <td className="px-3 py-2 text-right">{toNumber(d.completed)}</td>
                    <td className="px-3 py-2 text-right">{toNumber(d.cancelled)}</td>
                    <td className="px-3 py-2 text-right">{formatMoney(d.revenue_paid)}</td>
                    <td className="px-3 py-2 text-right">{formatMoney(d.revenue_unpaid)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 className="mt-8 text-lg font-semibold">Day by day</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="px-3 py-2 font-medium">Date</th>
                  <th className="px-3 py-2 text-right font-medium">Appointments</th>
                  <th className="px-3 py-2 font-medium">Revenue paid</th>
                </tr>
              </thead>
              <tbody>
                {data.daily.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-3 py-4 text-slate-500">No activity in this range.</td>
                  </tr>
                )}
                {data.daily.map((d) => (
                  <tr key={d.day} className="border-t border-slate-100">
                    <td className="whitespace-nowrap px-3 py-2">{formatDate(d.day)}</td>
                    <td className="px-3 py-2 text-right">{toNumber(d.appointments)}</td>
                    <td className="px-3 py-2">
                      <div className="grid grid-cols-[1fr_7rem] items-center gap-3">
                        <Bar value={toNumber(d.revenue)} max={maxDaily} />
                        <span className="text-right">{formatMoney(d.revenue)}</span>
                      </div>
                    </td>
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