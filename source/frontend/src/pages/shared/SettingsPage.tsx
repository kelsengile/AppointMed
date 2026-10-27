// Change your own password. The backend checks the current password and enforces the password rules.
import { useState, type FormEvent } from "react";
import { authApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import PasswordRequirements from "../../components/PasswordRequirements";
import { inputClass, primaryButton } from "../../components/ui";
import { passwordProblem } from "../../utils/password";

export default function SettingsPage() {
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
    <section className="max-w-md">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="mt-1 text-slate-600">Change your password.</p>
      <form onSubmit={submit} className="mt-6 space-y-4 rounded-xl border border-slate-200 bg-white p-5">
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
    </section>
  );
}