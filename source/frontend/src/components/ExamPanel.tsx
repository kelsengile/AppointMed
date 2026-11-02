import { useState, type FormEvent } from "react";
import { staffApi } from "../api/endpoints";
import type { AppointmentItem } from "../types";
import { formatMoney, isoDateTimeLocal, toNumber } from "../utils/format";
import { INT_PROPS, MONEY_PROPS, cleanDosage, cleanInt, cleanMedicine, cleanMoney, cleanMultiline, cleanText, isMoney } from "../utils/input";
import { inputClass, primaryButton } from "./ui";

interface Row {
  medicine_name: string;
  dosage: string;
  quantity: string;
  unit_price: string;
  instructions: string;
}

const blankRow = (): Row => ({ medicine_name: "", dosage: "", quantity: "1", unit_price: "0", instructions: "" });
const MAX_INVOICE = 99_999_999.99;

// The doctor's examination form. The invoice grows as medicines are added, and is saved on "Finish".
// Optionally books a follow-up visit. Only valid characters can be typed into the number fields.
export default function ExamPanel({ appointment, onDone }: { appointment: AppointmentItem; onDone: () => void }) {
  const [diagnosis, setDiagnosis] = useState("");
  const [notes, setNotes] = useState("");
  const [rxNotes, setRxNotes] = useState("");
  const [fee, setFee] = useState(String(toNumber(appointment.consultation_fee)));
  const [rows, setRows] = useState<Row[]>([]);
  const [followUp, setFollowUp] = useState("");
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
    if (diagnosis.trim().length < 2) {
      setError("Enter a diagnosis (at least 2 characters).");
      return;
    }
    if (!isMoney(fee)) {
      setError("Enter the consultation fee as an amount such as 500 or 500.50 (up to 1,000,000).");
      return;
    }
    const filled = rows.filter((r) => r.medicine_name.trim());
    for (const r of filled) {
      const qty = Number(r.quantity);
      if (!/^\d{1,4}$/.test(r.quantity) || qty < 1) {
        setError(`The quantity for ${r.medicine_name} must be a whole number from 1 to 9999.`);
        return;
      }
      if (!isMoney(r.unit_price)) {
        setError(`The price for ${r.medicine_name} must be an amount such as 8 or 8.50 (up to 1,000,000).`);
        return;
      }
    }
    if (total > MAX_INVOICE) {
      setError("The invoice total is too large. Check the quantities and prices.");
      return;
    }
    if (followUp && new Date(followUp).getTime() <= Date.now()) {
      setError("The follow-up must be in the future.");
      return;
    }
    setBusy(true);
    try {
      await staffApi.finish(appointment.id, {
        diagnosis: diagnosis.trim(),
        notes: notes.trim() || null,
        prescription_notes: rxNotes.trim() || null,
        consultation_fee: Number(fee),
        follow_up_time: followUp || null,
        items: filled.map((r) => ({
          medicine_name: r.medicine_name.trim(),
          dosage: r.dosage.trim() || null,
          quantity: Number(r.quantity),
          unit_price: Number(r.unit_price),
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
        <textarea className={`${inputClass} mt-1`} rows={2} maxLength={2000} value={diagnosis} onChange={(e) => setDiagnosis(cleanMultiline(e.target.value, 2000))} />
      </label>
      <label className="block text-sm font-medium">
        Examination notes (optional)
        <textarea className={`${inputClass} mt-1`} rows={2} maxLength={4000} value={notes} onChange={(e) => setNotes(cleanMultiline(e.target.value, 4000))} />
      </label>

      <fieldset>
        <legend className="text-sm font-medium">Prescription</legend>
        {rows.length === 0 && <p className="mt-1 text-sm text-slate-500">No medicines added.</p>}
        <div className="mt-2 space-y-3">
          {rows.map((r, i) => (
            <div key={i} className="grid gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-12">
              <input className={`${inputClass} md:col-span-4`} maxLength={150} placeholder="Medicine" aria-label="Medicine" value={r.medicine_name} onChange={(e) => change(i, "medicine_name", cleanMedicine(e.target.value))} />
              <input className={`${inputClass} md:col-span-2`} maxLength={100} placeholder="Dosage" aria-label="Dosage" value={r.dosage} onChange={(e) => change(i, "dosage", cleanDosage(e.target.value))} />
              <input {...INT_PROPS} className={`${inputClass} md:col-span-1`} maxLength={4} placeholder="Qty" aria-label="Quantity" value={r.quantity} onChange={(e) => change(i, "quantity", cleanInt(e.target.value, 4))} />
              <input {...MONEY_PROPS} className={`${inputClass} md:col-span-2`} placeholder="Unit price" aria-label="Unit price" value={r.unit_price} onChange={(e) => change(i, "unit_price", cleanMoney(e.target.value))} />
              <button type="button" onClick={() => setRows((prev) => prev.filter((_, idx) => idx !== i))} className="rounded-lg px-2 py-2 text-sm text-red-700 hover:bg-red-50 md:col-span-3">
                Remove
              </button>
              <input className={`${inputClass} md:col-span-12`} maxLength={255} placeholder="Instructions, e.g. take twice daily after meals" aria-label="Instructions" value={r.instructions} onChange={(e) => change(i, "instructions", cleanText(e.target.value, 255))} />
            </div>
          ))}
        </div>
        <button type="button" disabled={rows.length >= 30} onClick={() => setRows((prev) => [...prev, blankRow()])} className="mt-2 rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-60">
          Add medicine
        </button>
        {rows.length > 0 && (
          <label className="mt-3 block text-sm font-medium">
            General prescription note (optional)
            <input className={`${inputClass} mt-1`} maxLength={255} value={rxNotes} onChange={(e) => setRxNotes(cleanText(e.target.value, 255))} />
          </label>
        )}
      </fieldset>

      <label className="block text-sm font-medium">
        Book a follow-up visit (optional)
        <input type="datetime-local" className={`${inputClass} mt-1 sm:w-64`} min={isoDateTimeLocal(new Date())} value={followUp} onChange={(e) => setFollowUp(e.target.value)} />
      </label>

      <div className="rounded-lg bg-slate-50 p-4 text-sm">
        <p className="font-medium">Invoice (updates as you type)</p>
        <label className="mt-2 flex items-center justify-between gap-3">
          <span>Consultation fee</span>
          <input {...MONEY_PROPS} className={`${inputClass} w-32 text-right`} aria-label="Consultation fee" value={fee} onChange={(e) => setFee(cleanMoney(e.target.value))} />
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
      <button type="submit" disabled={busy} className={primaryButton}>
        {busy ? "Saving..." : "Finish examination and send invoice"}
      </button>
    </form>
  );
}