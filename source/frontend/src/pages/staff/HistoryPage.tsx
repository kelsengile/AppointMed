// Completed encounters (examined and paid), searchable by name, diagnosis or reason, and by date range.
import { useState } from "react";
import { staffApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import EncounterCard from "../../components/EncounterCard";
import { inputClass } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";

export default function HistoryPage() {
  const [search, setSearch] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const { data, error, loading } = usePolling(() => staffApi.history(search.trim(), from, to), 0, [search, from, to]);

  return (
    <section>
      <h1 className="text-2xl font-semibold">History</h1>
      <p className="mt-1 text-slate-600">Visits that were examined and paid.</p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by patient, diagnosis or reason"
          aria-label="Search history"
          className={`${inputClass} max-w-md flex-1`}
        />
        <label className="text-sm font-medium">
          From
          <input type="date" className={`${inputClass} mt-1`} value={from} max={to || undefined} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label className="text-sm font-medium">
          To
          <input type="date" className={`${inputClass} mt-1`} value={to} min={from || undefined} onChange={(e) => setTo(e.target.value)} />
        </label>
        {(from || to) && (
          <button
            type="button"
            className="rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
            onClick={() => {
              setFrom("");
              setTo("");
            }}
          >
            Clear dates
          </button>
        )}
      </div>
      {error && <Alert kind="error">{error}</Alert>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}
      {data && data.length === 0 && <p className="mt-6 text-slate-500">No completed visits found.</p>}
      {data && data.length > 0 && <p className="mt-4 text-sm text-slate-500">{data.length} visit{data.length === 1 ? "" : "s"}</p>}
      <div className="mt-2 space-y-4">
        {data?.map((e) => (
          <EncounterCard key={e.appointment_id} encounter={e} />
        ))}
      </div>
    </section>
  );
}