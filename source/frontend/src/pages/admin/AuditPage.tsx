// Admin: the append-only activity log, with search, an action filter, paging, and CSV download of the current page.
import { useState } from "react";
import { adminApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import { inputClass, secondaryButton } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import { downloadCsv } from "../../utils/csv";
import { formatDateTime } from "../../utils/format";

const PAGE_SIZE = 25;

export default function AuditPage() {
  const [q, setQ] = useState("");
  const [action, setAction] = useState("");
  const [offset, setOffset] = useState(0);
  const audit = usePolling(() => adminApi.audit(q.trim(), action, PAGE_SIZE, offset), 0, [q, action, offset]);
  const data = audit.data;

  const total = data?.total ?? 0;
  const first = total === 0 ? 0 : offset + 1;
  const last = Math.min(offset + PAGE_SIZE, total);

  function download() {
    if (!data) return;
    downloadCsv(`audit-log_${first}-${last}.csv`, [
      ["When", "User", "Action", "Entity", "Entity id", "Details"],
      ...data.items.map((r) => [r.created_at, r.username ?? "system", r.action, r.entity, r.entity_id, r.details]),
    ]);
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">Audit Logs</h1>
      <p className="mt-1 text-slate-600">Who did what, and when. Entries cannot be edited.</p>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <input
          type="search"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOffset(0);
          }}
          placeholder="Search details, user or record type"
          aria-label="Search the audit log"
          className={`${inputClass} max-w-xs`}
        />
        <select
          aria-label="Filter by action"
          className={`${inputClass} w-56`}
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">All actions</option>
          {data?.actions.map((a) => (
            <option key={a}>{a}</option>
          ))}
        </select>
        <button type="button" className={secondaryButton} disabled={!data || data.items.length === 0} onClick={download}>
          Download this page (CSV)
        </button>
      </div>

      {audit.error && <Alert kind="error">{audit.error}</Alert>}
      {audit.loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}

      {data && (
        <>
          <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="px-3 py-2 font-medium">When</th>
                  <th className="px-3 py-2 font-medium">User</th>
                  <th className="px-3 py-2 font-medium">Action</th>
                  <th className="px-3 py-2 font-medium">Record</th>
                  <th className="px-3 py-2 font-medium">Details</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-slate-500">No entries found.</td>
                  </tr>
                )}
                {data.items.map((r) => (
                  <tr key={r.id} className="border-t border-slate-100 align-top">
                    <td className="whitespace-nowrap px-3 py-2">{formatDateTime(r.created_at)}</td>
                    <td className="px-3 py-2">{r.username ?? "system"}</td>
                    <td className="px-3 py-2 font-medium">{r.action}</td>
                    <td className="px-3 py-2 text-slate-600">{r.entity ? `${r.entity}${r.entity_id ? ` #${r.entity_id}` : ""}` : "-"}</td>
                    <td className="px-3 py-2 text-slate-600">{r.details ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
            <span>
              Showing {first} to {last} of {total}
            </span>
            <div className="flex gap-2">
              <button type="button" className={secondaryButton} disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
                Previous
              </button>
              <button type="button" className={secondaryButton} disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}