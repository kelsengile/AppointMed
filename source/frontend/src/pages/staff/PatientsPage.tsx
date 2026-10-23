// Patient records: search, add, edit, delete, and open one to see every paid visit with prescriptions and bills.
import { useState, type FormEvent } from "react";
import { staffApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import EncounterCard from "../../components/EncounterCard";
import Modal from "../../components/Modal";
import { dangerButton, inputClass, primaryButton, secondaryButton } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import type { Encounter, PatientItem, PatientPayload, Sex } from "../../types";
import { ageFrom, formatDate, isoDate } from "../../utils/format";

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE = /^[0-9+()\-\s]{7,20}$/;

// Add / edit form. `patient` is null when adding.
function PatientForm({ patient, onClose, onSaved }: { patient: PatientItem | null; onClose: () => void; onSaved: (id: number, message: string) => void }) {
  const [fullName, setFullName] = useState(patient?.full_name ?? "");
  const [birthdate, setBirthdate] = useState(patient?.birthdate ?? "");
  const [sex, setSex] = useState<Sex | "">(patient?.sex ?? "");
  const [contact, setContact] = useState(patient?.contact_number ?? "");
  const [email, setEmail] = useState(patient?.email ?? "");
  const [address, setAddress] = useState(patient?.address ?? "");
  const [condition, setCondition] = useState(patient?.condition_summary ?? "");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (fullName.trim().length < 2) return setError("Enter the patient's full name.");
    if (birthdate && birthdate > isoDate(new Date())) return setError("Birthdate cannot be in the future.");
    if (contact.trim() && !PHONE.test(contact.trim())) return setError("Enter a valid contact number.");
    if (email.trim() && !EMAIL.test(email.trim())) return setError("Enter a valid email address.");
    const payload: PatientPayload = {
      full_name: fullName.trim(),
      birthdate: birthdate || null,
      sex: sex || null,
      contact_number: contact.trim() || null,
      email: email.trim() || null,
      address: address.trim() || null,
      condition_summary: condition.trim() || null,
    };
    setBusy(true);
    setError("");
    try {
      const saved = patient ? await staffApi.updatePatient(patient.id, payload) : await staffApi.createPatient(payload);
      onSaved(saved.id, patient ? "Patient record updated." : "Patient added.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the patient.");
      setBusy(false);
    }
  }

  return (
    <Modal title={patient ? "Edit patient" : "Add patient"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm font-medium">
          Full name
          <input className={`${inputClass} mt-1`} maxLength={100} value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-medium">
            Birthdate
            <input type="date" className={`${inputClass} mt-1`} max={isoDate(new Date())} value={birthdate} onChange={(e) => setBirthdate(e.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Sex
            <select className={`${inputClass} mt-1`} value={sex} onChange={(e) => setSex(e.target.value as Sex | "")}>
              <option value="">Select...</option>
              <option>Male</option>
              <option>Female</option>
              <option>Other</option>
            </select>
          </label>
          <label className="block text-sm font-medium">
            Contact number
            <input type="tel" className={`${inputClass} mt-1`} maxLength={20} value={contact} onChange={(e) => setContact(e.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Email
            <input type="email" className={`${inputClass} mt-1`} maxLength={100} value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
        </div>
        <label className="block text-sm font-medium">
          Address
          <input className={`${inputClass} mt-1`} maxLength={255} value={address} onChange={(e) => setAddress(e.target.value)} />
        </label>
        <label className="block text-sm font-medium">
          Condition summary
          <input className={`${inputClass} mt-1`} maxLength={255} value={condition} onChange={(e) => setCondition(e.target.value)} />
        </label>
        {error && <Alert kind="error">{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className={secondaryButton}>
            Cancel
          </button>
          <button type="submit" disabled={busy} className={primaryButton}>
            {busy ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function PatientsPage() {
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [form, setForm] = useState<"add" | "edit" | null>(null);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const patients = usePolling(() => staffApi.patients(search.trim()), 0, [search]);
  const visits = usePolling(() => (selectedId ? staffApi.patientHistory(selectedId) : Promise.resolve([] as Encounter[])), 0, [selectedId]);
  const selected: PatientItem | null = patients.data?.find((p) => p.id === selectedId) ?? null;

  async function remove(p: PatientItem) {
    if (!window.confirm(`Delete ${p.full_name}'s record? This cannot be undone.`)) return;
    setActionError("");
    setMessage("");
    try {
      await staffApi.deletePatient(p.id);
      setSelectedId(null);
      setMessage("Patient deleted.");
      await patients.reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not delete the patient.");
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Patients</h1>
          <p className="mt-1 text-slate-600">Patients are added automatically when a request is approved. You can also add them here.</p>
        </div>
        <button type="button" className={primaryButton} onClick={() => setForm("add")}>
          Add patient
        </button>
      </div>
      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by name, contact or email"
        aria-label="Search patients"
        className="mt-4 w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
      />
      {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
      {(actionError || patients.error) && <Alert kind="error">{actionError || patients.error}</Alert>}

      <div className="mt-4 grid gap-6 lg:grid-cols-[22rem_1fr]">
        <div>
          {patients.loading && !patients.data && <p className="text-slate-500">Loading...</p>}
          {patients.data && patients.data.length === 0 && <p className="text-slate-500">No patients found.</p>}
          <ul className="space-y-2">
            {patients.data?.map((p) => (
              <li key={p.id}>
                <button
                  onClick={() => setSelectedId(p.id)}
                  className={`w-full rounded-xl border p-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                    selectedId === p.id ? "border-brand-600 bg-brand-50" : "border-slate-200 bg-white hover:bg-slate-50"
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
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <h2 className="text-lg font-semibold">{selected.full_name}</h2>
                  <div className="flex gap-2">
                    <button className={secondaryButton} onClick={() => setForm("edit")}>
                      Edit
                    </button>
                    <button className={dangerButton} onClick={() => void remove(selected)}>
                      Delete
                    </button>
                  </div>
                </div>
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

      {form && (
        <PatientForm
          patient={form === "edit" ? selected : null}
          onClose={() => setForm(null)}
          onSaved={(id, text) => {
            setForm(null);
            setSelectedId(id);
            setMessage(text);
            void patients.reload();
          }}
        />
      )}
    </section>
  );
}