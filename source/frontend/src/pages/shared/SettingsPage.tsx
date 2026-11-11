// Settings. Everyone: appearance, account summary, change password and email preferences.
import { useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { authApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import EmailPreferencesCard from "../../components/EmailPreferences";
import PasswordRequirements from "../../components/PasswordRequirements";
import { inputClass, primaryButton, secondaryButton } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { usePolling } from "../../hooks/usePolling";
import { formatDateTime } from "../../utils/format";
import { passwordProblem } from "../../utils/password";
import { DEFAULT_PREFS, loadPrefs, updatePrefs, type Prefs, type TextSize, type Theme } from "../../utils/preferences";

function Card({ title, desc, children, className = "" }: { title: string; desc?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white p-5 ${className}`}>
      <h2 className="text-lg font-semibold">{title}</h2>
      {desc && <p className="mt-1 text-sm text-slate-600">{desc}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Choice<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: { value: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <div role="radiogroup" aria-label={label} className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={`rounded-lg px-3 py-1.5 text-sm ${value === o.value ? "bg-brand-600 text-white" : "border border-slate-300 bg-white hover:bg-slate-50"}`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function AppearanceCard() {
  const [prefs, setPrefs] = useState<Prefs>(loadPrefs);
  const change = (patch: Partial<Prefs>) => setPrefs(updatePrefs(patch));
  return (
    <Card title="Appearance" desc="Saved in this browser only.">
      <p className="text-sm font-medium">Theme</p>
      <div className="mt-2">
        <Choice<Theme>
          label="Theme"
          value={prefs.theme}
          onChange={(theme) => change({ theme })}
          options={[
            { value: "light", label: "Light" },
            { value: "dark", label: "Dark" },
            { value: "system", label: "Match my device" },
          ]}
        />
      </div>
      <p className="mt-4 text-sm font-medium">Text size</p>
      <div className="mt-2">
        <Choice<TextSize>
          label="Text size"
          value={prefs.textSize}
          onChange={(textSize) => change({ textSize })}
          options={[
            { value: "small", label: "Small" },
            { value: "normal", label: "Normal" },
            { value: "large", label: "Large" },
          ]}
        />
      </div>
      <button type="button" className={`${secondaryButton} mt-5`} onClick={() => change(DEFAULT_PREFS)}>
        Reset to defaults
      </button>
    </Card>
  );
}

function NotificationsCard() {
  const [prefs, setPrefs] = useState<Prefs>(loadPrefs);
  return (
    <Card title="In-app alerts" desc="Saved in this browser only.">
      <label className="flex items-center gap-3 text-sm font-medium">
        <input type="checkbox" checked={prefs.checkInAlert} onChange={(e) => setPrefs(updatePrefs({ checkInAlert: e.target.checked }))} />
        Show a banner on the Appointments page when a patient checks in
      </label>
    </Card>
  );
}

function AccountCard() {
  const { user } = useAuth();
  const { data } = usePolling(() => authApi.me(), 0);
  return (
    <Card title="Account" desc="Change your name, email, and photo on the profile page.">
      <dl className="space-y-1 text-sm">
        <div><dt className="inline font-medium">Username: </dt><dd className="inline">{data?.username ?? user?.username}</dd></div>
        <div><dt className="inline font-medium">Role: </dt><dd className="inline capitalize">{user?.role}</dd></div>
        <div><dt className="inline font-medium">Last sign-in: </dt><dd className="inline">{formatDateTime(data?.last_login_at)}</dd></div>
      </dl>
      <Link to={`/${user?.role ?? "doctor"}/profile`} className={`${secondaryButton} mt-4 inline-block`}>
        Open profile
      </Link>
    </Card>
  );
}

function PasswordCard() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    if (!current) return setError("Enter your current password.");
    const problem = passwordProblem(next);
    if (problem) return setError(problem);
    if (next !== confirm) return setError("The new passwords do not match.");
    if (next === current) return setError("Choose a password that is different from the current one.");
    setBusy(true);
    try {
      await authApi.changePassword(current, next);
      setMessage("Your password was changed.");
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change the password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Change password">
      <form onSubmit={submit} className="space-y-4">
        <label className="block text-sm font-medium">
          Current password
          <input type="password" autoComplete="current-password" className={`${inputClass} mt-1`} value={current} onChange={(e) => setCurrent(e.target.value)} />
        </label>
        <div>
          <label className="block text-sm font-medium">
            New password
            <input type="password" autoComplete="new-password" className={`${inputClass} mt-1`} value={next} onChange={(e) => setNext(e.target.value)} />
          </label>
          <PasswordRequirements password={next} />
        </div>
        <label className="block text-sm font-medium">
          Confirm new password
          <input type="password" autoComplete="new-password" className={`${inputClass} mt-1`} value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </label>
        {error && <Alert kind="error">{error}</Alert>}
        {message && <Alert kind="success">{message}</Alert>}
        <button type="submit" disabled={busy} className={primaryButton}>
          {busy ? "Saving..." : "Change password"}
        </button>
      </form>
    </Card>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  return (
    <section>
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="mt-1 text-slate-600">Appearance, your account, and your preferences.</p>

      {/* Row 1: doctors have three cards, everyone else two, so there is never an empty column. */}
      <div className={`mt-6 grid gap-6 lg:grid-cols-2 ${isDoctor ? "xl:grid-cols-3" : ""}`}>
        <AppearanceCard />
        <AccountCard />
        {isDoctor && <NotificationsCard />}
      </div>

      {/* Row 2: change password on the left, email settings beside it. */}
      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <PasswordCard />
        <EmailPreferencesCard />
      </div>
    </section>
  );
}