import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { publicApi } from "../api/endpoints";
import Logo from "../components/Logo";
import type { BookingReceipt, Catalog, Sex } from "../types";
import { formatDate, formatTime, isoDate, weekdayList } from "../utils/format";

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE = /^[0-9+()\-\s]{7,20}$/;
const input =
  "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30";

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-medium">
      {label}
      {children}
      {error && <span className="mt-1 block text-sm font-normal text-red-700">{error}</span>}
    </label>
  );
}

// Public booking page. Creates a request that the doctor's nurse (or the doctor) approves or disapproves.
export default function BookingPage() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [loadError, setLoadError] = useState("");
  const [person, setPerson] = useState({ full_name: "", birthdate: "", sex: "" as Sex | "", contact_number: "", email: "", address: "", reason: "" });
  const [specialization, setSpecialization] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [day, setDay] = useState("");
  const [slots, setSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [slot, setSlot] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState("");
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState<BookingReceipt | null>(null);

  useEffect(() => {
    publicApi
      .catalog()
      .then(setCatalog)
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Could not load the doctors."));
  }, []);

  // Load open times whenever the doctor or the date changes.
  useEffect(() => {
    setSlot("");
    setSlots([]);
    if (!doctorId || !day) return;
    let cancelled = false;
    setSlotsLoading(true);
    publicApi
      .slots(Number(doctorId), day)
      .then((r) => !cancelled && setSlots(r.slots))
      .catch((e) => !cancelled && setSubmitError(e instanceof Error ? e.message : "Could not load times."))
      .finally(() => !cancelled && setSlotsLoading(false));
    return () => {
      cancelled = true;
    };
  }, [doctorId, day]);

  const specializations = useMemo(
    () => Array.from(new Set((catalog?.doctors ?? []).map((d) => d.specialization).filter((s): s is string => !!s))).sort(),
    [catalog],
  );
  const doctors = (catalog?.doctors ?? []).filter((d) => !specialization || d.specialization === specialization);
  const chosen = catalog?.doctors.find((d) => String(d.id) === doctorId);

  const today = new Date();
  const maxDay = new Date();
  maxDay.setDate(maxDay.getDate() + (catalog?.window_days ?? 30));

  function setField(key: keyof typeof person, value: string) {
    setPerson((prev) => ({ ...prev, [key]: value }));
  }

  function validate(): Record<string, string> {
    const e: Record<string, string> = {};
    if (person.full_name.trim().length < 2) e.full_name = "Enter your full name.";
    if (!person.birthdate) e.birthdate = "Enter your birthdate.";
    else if (person.birthdate > isoDate(today)) e.birthdate = "Birthdate cannot be in the future.";
    if (!person.sex) e.sex = "Choose one.";
    if (!PHONE.test(person.contact_number.trim())) e.contact_number = "Enter a valid contact number.";
    if (!EMAIL.test(person.email.trim())) e.email = "Enter a valid email. Your confirmation is sent here.";
    if (person.address.trim().length < 3) e.address = "Enter your address.";
    if (person.reason.trim().length < 3) e.reason = "Tell us the reason for your visit.";
    if (!doctorId) e.doctor = "Choose a doctor.";
    if (!day) e.day = "Choose a date.";
    else if (doctorId && !slot) e.slot = "Choose an available time.";
    return e;
  }

  async function submit(ev: FormEvent) {
    ev.preventDefault();
    setSubmitError("");
    const found = validate();
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    setBusy(true);
    try {
      const result = await publicApi.book({
        full_name: person.full_name.trim(),
        birthdate: person.birthdate,
        sex: person.sex as Sex,
        contact_number: person.contact_number.trim(),
        email: person.email.trim(),
        address: person.address.trim(),
        doctor_id: Number(doctorId),
        preferred_datetime: slot,
        reason: person.reason.trim(),
      });
      setReceipt(result);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Could not send your request.");
      // The slot may have just been taken: refresh the list.
      if (doctorId && day) publicApi.slots(Number(doctorId), day).then((r) => setSlots(r.slots)).catch(() => undefined);
      setSlot("");
    } finally {
      setBusy(false);
    }
  }

  const header = (
    <>
      <Link to="/" aria-label="Back to AppointMed home">
        <Logo size={36} />
      </Link>
      <h1 className="mt-6 text-2xl font-semibold">Book an appointment</h1>
    </>
  );

  if (receipt) {
    return (
      <main className="mx-auto max-w-xl p-6 md:p-10">
        {header}
        <div className="mt-6 rounded-xl border border-brand-100 bg-white p-6" role="status">
          <h2 className="text-lg font-semibold text-brand-700">Request received</h2>
          <p className="mt-2 text-slate-700">
            You asked to see <strong>{receipt.doctor_name}</strong> on <strong>{formatDate(receipt.preferred_datetime)}</strong> at{" "}
            <strong>{formatTime(receipt.preferred_datetime)}</strong>.
          </p>
          <p className="mt-2 text-slate-600">
            Our staff will review it. We will email <strong>{receipt.email}</strong> as soon as it is confirmed, or if the time cannot be
            accommodated. It is not a confirmed appointment yet.
          </p>
          <Link to="/" className="mt-5 inline-block rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700">
            Back to home
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl p-6 md:p-10">
      {header}
      <p className="mt-1 text-slate-600">Choose a doctor and a time. A nurse will confirm your request by email.</p>

      {loadError && <p className="mt-6 rounded-lg bg-red-50 p-4 text-red-800" role="alert">{loadError}</p>}
      {!catalog && !loadError && <p className="mt-6 text-slate-500">Loading...</p>}
      {catalog && !catalog.booking_open && (
        <p className="mt-6 rounded-lg bg-amber-50 p-4 text-amber-900">Online booking is currently closed. Please call the clinic to book.</p>
      )}

      {catalog && catalog.booking_open && (
        <form onSubmit={submit} noValidate className="mt-6 space-y-8">
          <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="font-semibold">1. Your details</h2>
            <Field label="Full name" error={errors.full_name}>
              <input className={input} value={person.full_name} onChange={(e) => setField("full_name", e.target.value)} autoComplete="name" />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Birthdate" error={errors.birthdate}>
                <input type="date" className={input} max={isoDate(today)} value={person.birthdate} onChange={(e) => setField("birthdate", e.target.value)} autoComplete="bday" />
              </Field>
              <Field label="Sex" error={errors.sex}>
                <select className={input} value={person.sex} onChange={(e) => setField("sex", e.target.value)}>
                  <option value="">Select...</option>
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </select>
              </Field>
              <Field label="Contact number" error={errors.contact_number}>
                <input type="tel" className={input} value={person.contact_number} onChange={(e) => setField("contact_number", e.target.value)} autoComplete="tel" />
              </Field>
              <Field label="Email" error={errors.email}>
                <input type="email" className={input} value={person.email} onChange={(e) => setField("email", e.target.value)} autoComplete="email" />
              </Field>
            </div>
            <Field label="Address" error={errors.address}>
              <input className={input} value={person.address} onChange={(e) => setField("address", e.target.value)} autoComplete="street-address" />
            </Field>
            <Field label="Reason for visit" error={errors.reason}>
              <textarea className={input} rows={2} maxLength={255} value={person.reason} onChange={(e) => setField("reason", e.target.value)} />
            </Field>
          </section>

          <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="font-semibold">2. Doctor and time</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Specialization">
                <select
                  className={input}
                  value={specialization}
                  onChange={(e) => {
                    setSpecialization(e.target.value);
                    setDoctorId("");
                  }}
                >
                  <option value="">Any</option>
                  {specializations.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </Field>
              <Field label="Doctor" error={errors.doctor}>
                <select className={input} value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
                  <option value="">Select a doctor...</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.full_name}
                      {d.specialization ? ` (${d.specialization})` : ""}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            {chosen && <p className="text-sm text-slate-500">{chosen.full_name} sees patients on {weekdayList(chosen.weekdays)}.</p>}

            <Field label="Date" error={errors.day}>
              <input type="date" className={input} min={isoDate(today)} max={isoDate(maxDay)} value={day} onChange={(e) => setDay(e.target.value)} />
            </Field>

            {doctorId && day && (
              <div>
                <p className="text-sm font-medium">Available times</p>
                {slotsLoading && <p className="mt-1 text-sm text-slate-500">Loading times...</p>}
                {!slotsLoading && slots.length === 0 && (
                  <p className="mt-1 text-sm text-slate-500">No open times on this day. Try another date.</p>
                )}
                <div className="mt-2 grid grid-cols-3 gap-2 sm:grid-cols-4" role="radiogroup" aria-label="Available times">
                  {slots.map((s) => (
                    <button
                      key={s}
                      type="button"
                      role="radio"
                      aria-checked={slot === s}
                      onClick={() => setSlot(s)}
                      className={`rounded-lg border px-2 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                        slot === s ? "border-brand-600 bg-brand-600 text-white" : "border-slate-300 hover:bg-brand-50"
                      }`}
                    >
                      {formatTime(s)}
                    </button>
                  ))}
                </div>
                {errors.slot && <p className="mt-1 text-sm text-red-700">{errors.slot}</p>}
              </div>
            )}
          </section>

          {submitError && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-800" role="alert">{submitError}</p>}
          <button type="submit" disabled={busy} className="rounded-lg bg-brand-600 px-5 py-3 font-medium text-white hover:bg-brand-700 disabled:opacity-60">
            {busy ? "Sending..." : "Request appointment"}
          </button>
        </form>
      )}
    </main>
  );
}