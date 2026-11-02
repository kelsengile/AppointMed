// Doctor only: every prescription the doctor has issued, newest first.
import { useState } from "react";
import { staffApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import { inputClass } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import { formatDateTime, formatMoney, toNumber } from "../../utils/format";

export default function PrescriptionsPage() {
  const [search, setSearch] = useState("");
  const { data, error, loading } = usePolling(() => staffApi.prescriptions(search.trim()), 0, [search]);

  return (
    <section>
      <h1 className="text-2xl font-semibold">Prescriptions</h1>
      <p className="mt-1 text-slate-600">Prescriptions are written while examining a patient (Appointments) and listed here.</p>
      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by patient or diagnosis"
        aria-label="Search prescriptions"
        className={`${inputClass} mt-4 max-w-md`}
      />
      {error && <Alert kind="error">{error}</Alert>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}
      {data && data.length === 0 && <p className="mt-6 text-slate-500">No prescriptions found.</p>}

      <div className="mt-4 space-y-4">
        {data?.map((rx) => {
          const total = rx.items.reduce((sum, i) => sum + i.quantity * toNumber(i.unit_price), 0);
          return (
            <article key={rx.id} className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="font-semibold">{rx.patient_name}</h2>
                <p className="text-sm text-slate-500">{formatDateTime(rx.issued_at)}</p>
              </div>
              <p className="mt-2 text-sm">
                <span className="font-medium">Diagnosis: </span>
                {rx.diagnosis ?? "-"}
              </p>
              {rx.notes && <p className="mt-1 text-sm text-slate-600">Note: {rx.notes}</p>}
              {rx.items.length === 0 ? (
                <p className="mt-3 text-sm text-slate-500">No medicines on this prescription.</p>
              ) : (
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-slate-500">
                      <tr>
                        <th className="py-1 pr-3 font-medium">Medicine</th>
                        <th className="py-1 pr-3 font-medium">Dosage</th>
                        <th className="py-1 pr-3 font-medium">Qty</th>
                        <th className="py-1 pr-3 font-medium">Instructions</th>
                        <th className="py-1 text-right font-medium">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rx.items.map((i) => (
                        <tr key={i.id} className="border-t border-slate-100">
                          <td className="py-1 pr-3">{i.medicine_name}</td>
                          <td className="py-1 pr-3">{i.dosage ?? "-"}</td>
                          <td className="py-1 pr-3">{i.quantity}</td>
                          <td className="py-1 pr-3">{i.instructions ?? "-"}</td>
                          <td className="py-1 text-right">{formatMoney(i.quantity * toNumber(i.unit_price))}</td>
                        </tr>
                      ))}
                      <tr className="border-t border-slate-200 font-semibold">
                        <td className="pt-2" colSpan={4}>Medicines total</td>
                        <td className="pt-2 text-right">{formatMoney(total)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}