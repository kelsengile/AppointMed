import type { Encounter } from "../types";
import { formatDate, formatDateTime, formatMoney } from "../utils/format";

// A finished (paid) visit: diagnosis, prescription list, and the bill.
export default function EncounterCard({ encounter: e, showName = true }: { encounter: Encounter; showName?: boolean }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-semibold">{showName ? e.full_name : formatDate(e.scheduled_time)}</h3>
        <p className="text-sm text-slate-500">{showName ? formatDateTime(e.scheduled_time) : e.reason}</p>
      </div>
      {showName && e.reason && <p className="mt-1 text-sm text-slate-600">Reason: {e.reason}</p>}
      <p className="mt-3 text-sm">
        <span className="font-medium">Diagnosis: </span>
        {e.diagnosis ?? "-"}
      </p>
      {e.notes && <p className="mt-1 text-sm text-slate-600">{e.notes}</p>}

      {e.items.length > 0 && (
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
              {e.items.map((i) => (
                <tr key={i.id} className="border-t border-slate-100">
                  <td className="py-1 pr-3">{i.medicine_name}</td>
                  <td className="py-1 pr-3">{i.dosage ?? "-"}</td>
                  <td className="py-1 pr-3">{i.quantity}</td>
                  <td className="py-1 pr-3">{i.instructions ?? "-"}</td>
                  <td className="py-1 text-right">{formatMoney(i.quantity * i.unit_price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-3 border-t border-slate-100 pt-3 text-sm text-slate-600">
        Consultation {formatMoney(e.consultation_fee)} + medicines {formatMoney(e.medicines_total)} ={" "}
        <span className="font-semibold text-brand-900">{formatMoney(e.amount)}</span>
        {e.paid_at && <span> (paid {formatDate(e.paid_at)})</span>}
      </p>
    </article>
  );
}