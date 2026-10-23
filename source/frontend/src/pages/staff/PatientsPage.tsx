import { useState } from "react";
import { staffApi } from "../../api/endpoints";
import EncounterCard from "../../components/EncounterCard";
import { usePolling } from "../../hooks/usePolling";
import type { PatientItem } from "../../types";
import { ageFrom, formatDate } from "../../utils/format";

// Patient records: search, then open one to see every paid visit with prescriptions and bills.
export default function PatientsPage() {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<PatientItem | null>(null);
  const patients = usePolling(() => staffApi.patients(search.trim()), 0, [search]);
  const visits = usePolling(
    () => (selected ? staffApi.history("", selected.id) : Promise.resolve([])),
    0,
    [selected?.id],
  );

  return (
    <section>
      <h1 className="text-2xl font-semibold">Patients</h1>
      <p className="mt-1 text-slate-600">Patients are added automatically when a booking request is approved.</p>
      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by name"
        aria-label="Search patients by name"
        className="mt-4 w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
      />
      {patients.error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800" role="alert">{patients.error}</p>}

      <div className="mt-4 grid gap-6 lg:grid-cols-[22rem_1fr]">
        <div>
          {patients.loading && !patients.data && <p className="text-slate-500">Loading...</p>}
          {patients.data && patients.data.length === 0 && <p className="text-slate-500">No patients found.</p>}
          <ul className="space-y-2">
            {patients.data?.map((p) => (
              <li key={p.id}>
                <button
                  onClick={() => setSelected(p)}
                  className={`w-full rounded-xl border p-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                    selected?.id === p.id ? "border-brand-600 bg-brand-50" : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <p className="font-semibold">{p.full_name}</p>
                  <p className="text-sm text-slate-500">
                    {[p.sex, ageFrom(p.birthdate)].filter(Boolean).join(" - ")} - {p.visit_count} visit{p.visit_count === 1 ? "" : "s"}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          {!selected && <p className="text-slate-500">Select a patient to see their record.</p>}
          {selected && (
            <>
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h2 className="text-lg font-semibold">{selected.full_name}</h2>
                <dl className="mt-2 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
                  <div><dt className="inline font-medium">Birthdate: </dt><dd className="inline">{formatDate(selected.birthdate)} {ageFrom(selected.birthdate) && `(${ageFrom(selected.birthdate)})`}</dd></div>
                  <div><dt className="inline font-medium">Sex: </dt><dd className="inline">{selected.sex ?? "-"}</dd></div>
                  <div><dt className="inline font-medium">Contact: </dt><dd className="inline">{selected.contact_number ?? "-"}</dd></div>
                  <div><dt className="inline font-medium">Email: </dt><dd className="inline">{selected.email ?? "-"}</dd></div>
                  <div className="sm:col-span-2"><dt className="inline font-medium">Address: </dt><dd className="inline">{selected.address ?? "-"}</dd></div>
                  <div className="sm:col-span-2"><dt className="inline font-medium">Latest condition: </dt><dd className="inline">{selected.condition_summary ?? "-"}</dd></div>
                </dl>
              </div>
              <h3 className="mt-6 font-semibold">Visit history</h3>
              {visits.error && <p className="mt-2 text-sm text-red-700" role="alert">{visits.error}</p>}
              {visits.data && visits.data.length === 0 && <p className="mt-2 text-slate-500">No completed visits yet.</p>}
              <div className="mt-3 space-y-4">
                {visits.data?.map((e) => (
                  <EncounterCard key={e.appointment_id} encounter={e} showName={false} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}