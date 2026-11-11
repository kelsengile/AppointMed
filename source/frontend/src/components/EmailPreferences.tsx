// Settings card: choose which emails you receive. Security emails are always sent.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { authApi } from "../api/endpoints";
import { useAuth } from "../context/AuthContext";
import { usePolling } from "../hooks/usePolling";
import type { EmailPrefKey, EmailPreferences, Role } from "../types";
import Alert from "./Alert";
import { primaryButton, secondaryButton } from "./ui";

const ALL_ROLES: Role[] = ["doctor", "nurse", "admin"];

const OPTIONS: { key: EmailPrefKey; label: string; desc: string; roles: Role[] }[] = [
  {
    key: "notify_requests",
    label: "New appointment requests",
    desc: "When a patient asks for an appointment, and when a teammate approves or disapproves one.",
    roles: ["doctor", "nurse"],
  },
  {
    key: "notify_appointments",
    label: "Appointment changes",
    desc: "Patient check-ins, cancellations, rescheduled visits, and days off.",
    roles: ["doctor", "nurse"],
  },
  {
    key: "notify_billing",
    label: "Billing",
    desc: "Examinations that are ready to pay, and payments received.",
    roles: ["doctor", "nurse"],
  },
  {
    key: "notify_account",
    label: "My account and schedule",
    desc: "Changes an administrator makes to your details, working hours, or assigned team.",
    roles: ALL_ROLES,
  },
  {
    key: "notify_clinic",
    label: "Clinic and system changes",
    desc: "Clinic settings, rooms, departments, website content, and database backups or restores.",
    roles: ALL_ROLES,
  },
];

const KEYS = OPTIONS.map((o) => o.key);

export default function EmailPreferencesCard({ className = "" }: { className?: string }) {
  const { user } = useAuth();
  const { data, error, loading, reload } = usePolling(() => authApi.emailPreferences(), 0);
  const [draft, setDraft] = useState<EmailPreferences | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    if (data) setDraft(data.preferences);
  }, [data]);

  const options = OPTIONS.filter((o) => !user || o.roles.includes(user.role));
  const dirty = !!(draft && data && KEYS.some((k) => draft[k] !== data.preferences[k]));
  const profileLink = `/${user?.role ?? "doctor"}/profile`;

  async function save() {
    if (!draft) return;
    setBusy(true);
    setMessage("");
    setFormError("");
    try {
      await authApi.saveEmailPreferences(draft);
      await reload();
      setMessage("Email settings saved.");
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Could not save your email settings.");
    } finally {
      setBusy(false);
    }
  }

  async function sendTest() {
    setBusy(true);
    setMessage("");
    setFormError("");
    try {
      const result = await authApi.sendTestEmail();
      setMessage(
        result.smtp_enabled
          ? `A test email is on its way to ${data?.email}.`
          : "Email is not set up on the server yet (no SMTP_HOST), so the test message was written to the backend console instead.",
      );
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Could not send the test email.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={`rounded-xl border border-slate-200 bg-white p-5 ${className}`}>
      <h2 className="text-lg font-semibold">Email notifications</h2>
      <p className="mt-1 text-sm text-slate-600">Choose which emails AppointMed sends you.</p>

      {error && <Alert kind="error">{error}</Alert>}
      {loading && !data && <p className="mt-4 text-slate-500">Loading...</p>}

      {data && draft && (
        <>
          {data.email ? (
            <p className="mt-3 text-sm text-slate-700">
              Emails go to <strong>{data.email}</strong>. Change it on your{" "}
              <Link to={profileLink} className="font-medium text-brand-700 hover:underline">profile</Link>.
            </p>
          ) : (
            <Alert kind="warning">
              You have no email address, so you will not receive any emails.{" "}
              <Link to={profileLink} className="font-medium underline">Add one on your profile</Link>.
            </Alert>
          )}

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {options.map((o) => (
              <label key={o.key} className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:bg-brand-50">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={draft[o.key]}
                  onChange={(e) => setDraft({ ...draft, [o.key]: e.target.checked })}
                />
                <span>
                  <span className="block text-sm font-medium">{o.label}</span>
                  <span className="block text-xs text-slate-500">{o.desc}</span>
                </span>
              </label>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Security emails (a new account, deactivation, and password changes) are always sent. Emails never include medical details.
          </p>

          {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
          {formError && <Alert kind="error">{formError}</Alert>}

          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" className={primaryButton} disabled={busy || !dirty} onClick={() => void save()}>
              {busy ? "Working..." : "Save email settings"}
            </button>
            <button
              type="button"
              className={secondaryButton}
              disabled={busy || dirty || !data.email}
              title={dirty ? "Save your changes first" : !data.email ? "Add an email address first" : undefined}
              onClick={() => void sendTest()}
            >
              Send me a test email
            </button>
          </div>
        </>
      )}
    </section>
  );
}
