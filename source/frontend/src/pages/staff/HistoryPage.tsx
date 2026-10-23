import { useState } from "react";
import { staffApi } from "../../api/endpoints";
import EncounterCard from "../../components/EncounterCard";
import { usePolling } from "../../hooks/usePolling";

// Completed encounters (examined and paid).
export default function HistoryPage() {
  const [search, setSearch] = useState("");
  const { data, error, loading } = usePolling(() => staffApi.history(search.trim()), 0, [search]);

  return (
    <section>
      <h1 className="text-2xl font-semibold">History</h1>
      <p className="mt-1 text-slate-600">Visits that were examined and paid.</p>
      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by patient name"
        aria-label="Search history by patient name"
        className="mt-4 w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
      />
      {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800" role="alert">{error}</p>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}
      {data && data.length === 0 && <p className="mt-6 text-slate-500">No completed visits yet.</p>}
      <div className="mt-4 space-y-4">
        {data?.map((e) => (
          <EncounterCard key={e.appointment_id} encounter={e} />
        ))}
      </div>
    </section>
  );
}