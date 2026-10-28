// Books a walk-in or phone appointment for the user's doctor, for a new or an existing patient.
import { useState, type FormEvent } from "react";
import { staffApi } from "../api/endpoints";
import { usePolling } from "../hooks/usePolling";
import type { AppointmentCreatePayload, Sex } from "../types";
import { isoDate } from "../utils/format";
import { MIN_BIRTHDATE, cleanName, cleanPhone, cleanText, isName, isPhone } from "../utils/input";
import Alert from "./Alert";
import Modal from "./Modal";
import { inputClass, primaryButton, secondaryButton } from "./ui";

export default function WalkInModal({ onClose, onCreated }: { onClose: () => void; onCreated: (patientName: string) => void }) {
  const patients = usePolling(() => staffApi.patients(""), 0);
  const [mode, setMode] = useState<"existing" | "new">("new");
  const [patientId, setPatientId] = useState("");
  const [fullName, setFullName] = useState("");
  const [birthdate, setBirthdate] = useState("");
  const [sex, setSex] = useState<Sex | "">("");
  const [contact, setContact] = useState("");
  const [reason, setReason] = useState("");
  const [when, setWhen] = useState("");
  const [checkIn, setCheckIn] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const today = isoDate(new Date());

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (when && when.slice(0, 10) < today) return setError("Choose today or a later date.");
    if (checkIn && when && when.slice(0, 10) !== today) return setError("Only today's appointments can be checked in. Untick the box or choose today.");
    const payload: AppointmentCreatePayload = {
      reason: reason.trim() || null,
      scheduled_time: when || null, // empty means "now"
      check_in_now: checkIn,
    };
    if (mode === "existing") {
      if (!patientId) return setError("Choose a patient.");
      payload.patient_id = Number(patientId);
    } else {
      if (!isName(fullName.trim())) return setError("Enter the patient's full name (letters only, at least 2).");
      if (birthdate && (birthdate > today || birthdate < MIN_BIRTHDATE)) return setError("Enter a valid birthdate.");
      if (contact.trim() && !isPhone(contact.trim())) return setError("Enter a valid contact number (7 to 15 digits).");
      payload.full_name = fullName.trim();
      payload.birthdate = birthdate || null;
      payload.sex = sex || null;
      payload.contact_number = contact.trim() || null;
    }
    setBusy(true);
    try {
      const created = await staffApi.createAppointment(payload);
      onCreated(created.full_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the appointment.");
      setBusy(false);
    }
  }

  return (
    <Modal title="New appointment" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <div className="flex gap-2" role="radiogroup" aria-label="Patient type">
          {(["new", "existing"] as const).map((m) => (
            <button
              key={m}
              type="button"
              role="radio"
              aria-checked={mode === m}
              onClick={() => setMode(m)}
              className={`rounded-lg px-3 py-1.5 text-sm ${mode === m ? "bg-brand-600 text-white" : "border border-slate-300 hover:bg-slate-50"}`}
            >
              {m === "new" ? "New patient" : "Existing patient"}
            </button>
          ))}
        </div>

        {mode === "existing" ? (
          <label className="block text-sm font-medium">
            Patient
            <select className={`${inputClass} mt-1`} value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="">{patients.loading && !patients.data ? "Loading..." : "Select a patient..."}</option>
              {patients.data?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <>
            <label className="block text-sm font-medium">
              Full name
              <input className={`${inputClass} mt-1`} maxLength={100} value={fullName} onChange={(e) => setFullName(cleanName(e.target.value))} autoComplete="off" />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm font-medium">
                Birthdate (optional)
                <input type="date" className={`${inputClass} mt-1`} min={MIN_BIRTHDATE} max={today} value={birthdate} onChange={(e) => setBirthdate(e.target.value)} />
              </label>
              <label className="block text-sm font-medium">
                Sex (optional)
                <select className={`${inputClass} mt-1`} value={sex} onChange={(e) => setSex(e.target.value as Sex | "")}>
                  <option value="">Select...</option>
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </select>
              </label>
            </div>
            <label className="block text-sm font-medium">
              Contact number (optional)
              <input type="tel" inputMode="tel" className={`${inputClass} mt-1`} maxLength={20} value={contact} onChange={(e) => setContact(cleanPhone(e.target.value))} />
            </label>
          </>
        )}

        <label className="block text-sm font-medium">
          Reason for visit (optional)
          <input className={`${inputClass} mt-1`} maxLength={255} value={reason} onChange={(e) => setReason(cleanText(e.target.value, 255))} />
        </label>
        <label className="block text-sm font-medium">
          Date and time (leave empty for right now)
          <input type="datetime-local" className={`${inputClass} mt-1`} min={`${today}T00:00`} value={when} onChange={(e) => setWhen(e.target.value)} />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={checkIn} onChange={(e) => setCheckIn(e.target.checked)} />
          Check the patient in now (adds them to the waiting queue; today only)
        </label>

        {error && <Alert kind="error">{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className={secondaryButton}>
            Cancel
          </button>
          <button type="submit" disabled={busy} className={primaryButton}>
            {busy ? "Saving..." : "Create appointment"}
          </button>
        </div>
      </form>
    </Modal>
  );
}