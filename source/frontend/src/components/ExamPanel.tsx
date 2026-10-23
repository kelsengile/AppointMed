import { useState, type FormEvent } from "react";
import { staffApi } from "../api/endpoints";
import type { AppointmentItem } from "../types";
import { formatMoney } from "../utils/format";

interface Row {
  medicine_name: string;
  dosage: string;
  quantity: string;
  unit_price: string;
  instructions: string;
}

const blankRow = (): Row => ({ medicine_name: "", dosage: "", quantity: "1", unit_price: "0", instructions: "" });
const input =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30";

// The doctor's examination form. The invoice grows as medicines are added, and is saved on "Finish".
export default function ExamPanel({ appointment, onDone }: { appointment: AppointmentItem; onDone: () => void }) {
  const [diagnosis, setDiagnosis] = useState("");
  const [notes, setNotes] = useState("");
  const [rxNotes, setRxNotes] = useState("");
  const [fee, setFee] = useState(String(appointment.consultation_fee ?? 0));
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const medicines = rows.reduce((sum, r) => sum + (Number(r.quantity) || 0) * (Number(r.unit_price) || 0), 0);
  const total = (Number(fee) || 0) + medicines;

  function change(index: number, key: keyof Row, value: string) {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [key]: value } : r)));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!diagnosis.trim()) {
      setError("Enter a diagnosis.");
      return;
    }
    const feeValue = Number(fee);
    if (!Number.isFinite(feeValue) || feeValue < 0) {
      setError("The consultation fee must be zero or more.");
      return;
    }
    const filled = rows.filter((r) => r.medicine_name.trim());
    for (const r of filled) {
      const qty = Number(r.quantity);
      const price = Number(r.unit_price);
      if (!Number.isInteger(qty) || qty < 1 || !Number.isFinite(price) || price < 0) {
        setError(`Check the quantity and price for ${r.medicine_name}.`);
        return;
      }
    }
    setBusy(true);
    try {
      await staffApi.finish(appointment.id, {
        diagnosis: diagnosis.trim(),
        notes: notes.trim() || null,
        prescription_notes: rxNotes.trim() || null,
        consultation_fee: feeValue,
        items: filled.map((r) => ({
          medicine_name: r.medicine_name.trim(),
          dosage: r.dosage.trim() || null,
          quantity: Number(r.quantity),
          unit_price: Number(r.unit_price) || 0,
          instructions: r.instructions.trim() || null,
        })),
      });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the examination.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mt-4 space-y-4 border-t border-slate-200 pt-4">
      <label className="block text-sm font-medium">
        Diagnosis
        <textarea className={`${input} mt-1`} rows={2} value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} />
      </label>
      <label className="block text-sm font-medium">
        Examination notes (optional)
        <textarea className={`${input} mt-1`} rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>

      <fieldset>
        <legend className="text-sm font-medium">Prescription</legend>
        {rows.length === 0 && <p className="mt-1 text-sm text-slate-500">No medicines added.</p>}
        <div className="mt-2 space-y-3">
          {rows.map((r, i) => (
            <div key={i} className="grid gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-12">
              <input className={`${input} md:col-span-4`} placeholder="Medicine" aria-label="Medicine" value={r.medicine_name} onChange={(e) => change(i, "medicine_name", e.target.value)} />
              <input className={`${input} md:col-span-2`} placeholder="Dosage" aria-label="Dosage" value={r.dosage} onChange={(e) => change(i, "dosage", e.target.value)} />
              <input className={`${input} md:col-span-1`} type="number" min={1} placeholder="Qty" aria-label="Quantity" value={r.quantity} onChange={(e) => change(i, "quantity", e.target.value)} />
              <input className={`${input} md:col-span-2`} type="number" min={0} step="0.01" placeholder="Unit price" aria-label="Unit price" value={r.unit_price} onChange={(e) => change(i, "unit_price", e.target.value)} />
              <button type="button" onClick={() => setRows((prev) => prev.filter((_, idx) => idx !== i))} className="rounded-lg px-2 py-2 text-sm text-red-700 hover:bg-red-50 md:col-span-3">
                Remove
              </button>
              <input className={`${input} md:col-span-12`} placeholder="Instructions, e.g. take twice daily after meals" aria-label="Instructions" value={r.instructions} onChange={(e) => change(i, "instructions", e.target.value)} />
            </div>
          ))}
        </div>
        <button type="button" onClick={() => setRows((prev) => [...prev, blankRow()])} className="mt-2 rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">
          Add medicine
        </button>
        {rows.length > 0 && (
          <label className="mt-3 block text-sm font-medium">
            General prescription note (optional)
            <input className={`${input} mt-1`} value={rxNotes} onChange={(e) => setRxNotes(e.target.value)} />
          </label>
        )}
      </fieldset>

      <div className="rounded-lg bg-slate-50 p-4 text-sm">
        <p className="font-medium">Invoice (updates as you type)</p>
        <label className="mt-2 flex items-center justify-between gap-3">
          <span>Consultation fee</span>
          <input className={`${input} w-32 text-right`} type="number" min={0} step="0.01" value={fee} onChange={(e) => setFee(e.target.value)} />
        </label>
        <p className="mt-2 flex justify-between">
          <span>Medicines</span>
          <span>{formatMoney(medicines)}</span>
        </p>
        <p className="mt-1 flex justify-between border-t border-slate-200 pt-2 font-semibold">
          <span>Total to pay</span>
          <span>{formatMoney(total)}</span>
        </p>
      </div>

      {error && <p className="text-sm text-red-700" role="alert">{error}</p>}
      <button type="submit" disabled={busy} className="rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60">
        {busy ? "Saving..." : "Finish examination and send invoice"}
      </button>
    </form>
  );
}