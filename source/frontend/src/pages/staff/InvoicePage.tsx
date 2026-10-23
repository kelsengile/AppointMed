import { useState } from "react";
import { staffApi } from "../../api/endpoints";
import Badge from "../../components/Badge";
import { usePolling } from "../../hooks/usePolling";
import { formatDate, formatDateTime, formatMoney } from "../../utils/format";

const FILTERS = ["Unpaid", "Paid", "all"] as const;
type Filter = (typeof FILTERS)[number];

// Session bills: consultation fee + prescribed medicines. The doctor or the nurse marks them paid.
export default function InvoicePage() {
  const [filter, setFilter] = useState<Filter>("Unpaid");
  const { data, error, loading, reload } = usePolling(() => staffApi.invoices(filter), 10000, [filter]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  const [message, setMessage] = useState("");

  async function pay(id: number, name: string) {
    if (!window.confirm(`Mark ${name}'s invoice as paid? The visit moves to History.`)) return;
    setBusyId(id);
    setActionError("");
    setMessage("");
    try {
      await staffApi.pay(id);
      setMessage(`${name}'s invoice is paid. The visit was added to History and the patient's record.`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not mark the invoice as paid.");
    } finally {
      await reload();
      setBusyId(null);
    }
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">Invoice</h1>
      <p className="mt-1 text-slate-600">Mark an invoice paid once the patient has paid. Payment is only possible after the examination is finished.</p>

      <div className="mt-4 flex flex-wrap gap-2" role="tablist" aria-label="Invoice status">
        {FILTERS.map((f) => (
          <button
            key={f}
            role="tab"
            aria-selected={filter === f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-sm ${filter === f ? "bg-brand-600 text-white" : "border border-slate-300 bg-white hover:bg-slate-50"}`}
          >
            {f === "all" ? "All" : f}
          </button>
        ))}
      </div>

      {message && <p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{message}</p>}
      {(actionError || error) && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800" role="alert">{actionError || error}</p>}
      {loading && !data && <p className="mt-6 text-slate-500">Loading...</p>}
      {data && data.length === 0 && <p className="mt-6 text-slate-500">No invoices.</p>}

      <ul className="mt-4 space-y-4">
        {data?.map((inv) => {
          const examining = inv.appointment_status === "Consulting";
          return (
            <li key={inv.id} className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="font-semibold">{inv.patient_name}</h2>
                  <p className="text-sm text-slate-500">Visit {formatDateTime(inv.scheduled_time)} - Invoice #{inv.id}</p>
                </div>
                <Badge tone={inv.status === "Paid" ? "green" : inv.status === "Unpaid" ? "amber" : "red"}>{inv.status}</Badge>
              </div>

              <table className="mt-3 w-full text-left text-sm">
                <tbody>
                  <tr>
                    <td className="py-1">Doctor's examination</td>
                    <td className="py-1 text-right">{formatMoney(inv.consultation_fee)}</td>
                  </tr>
                  {inv.items.map((i) => (
                    <tr key={i.id}>
                      <td className="py-1 text-slate-700">
                        {i.medicine_name} {i.dosage && `(${i.dosage})`} x {i.quantity}
                      </td>
                      <td className="py-1 text-right">{formatMoney(i.quantity * i.unit_price)}</td>
                    </tr>
                  ))}
                  <tr className="border-t border-slate-200 font-semibold">
                    <td className="pt-2">Total</td>
                    <td className="pt-2 text-right">{formatMoney(inv.amount)}</td>
                  </tr>
                </tbody>
              </table>

              {inv.status === "Unpaid" && (
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <button
                    disabled={busyId === inv.id || inv.appointment_status !== "Examined"}
                    onClick={() => pay(inv.id, inv.patient_name)}
                    className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
                  >
                    Mark as paid
                  </button>
                  {examining && <span className="text-sm text-slate-500">The examination is still in progress. The total updates when the doctor finishes.</span>}
                </div>
              )}
              {inv.status === "Paid" && <p className="mt-3 text-sm text-slate-500">Paid on {formatDate(inv.paid_at)}.</p>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}