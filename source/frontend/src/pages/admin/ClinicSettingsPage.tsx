// Admin: clinic name and address, default fee, slot length, booking window, and the online-booking switch.
// Only changed values are sent, so the audit log stays clean.
import { useEffect, useState, type FormEvent } from "react";
import { adminApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import { inputClass, primaryButton } from "../../components/ui";
import type { SettingRow } from "../../types";
import { formatDateTime } from "../../utils/format";
import { cleanAddress, cleanClinicName, cleanInt, cleanMoney, isMoney } from "../../utils/input";

interface FieldDef {
  key: string;
  label: string;
  help: string;
  kind: "text" | "number" | "toggle";
  clean?: (v: string) => string; // removes characters the field must never contain
  maxLength?: number;
}

const FIELDS: FieldDef[] = [
  { key: "clinic_name", label: "Clinic name", help: "Shown on the website and printed invoices.", kind: "text", clean: cleanClinicName, maxLength: 100 },
  { key: "clinic_address", label: "Clinic address", help: "Shown on the website.", kind: "text", clean: cleanAddress, maxLength: 255 },
  { key: "consultation_fee", label: "Default consultation fee (PHP)", help: "Used when an examination starts. The doctor can change it per visit.", kind: "number", clean: (v) => cleanMoney(v), maxLength: 10 },
  { key: "default_slot_minutes", label: "Default slot length (minutes)", help: "5 to 120.", kind: "number", clean: (v) => cleanInt(v, 3), maxLength: 3 },
  { key: "booking_window_days", label: "Online booking window (days)", help: "How far ahead patients can book. 1 to 365.", kind: "number", clean: (v) => cleanInt(v, 3), maxLength: 3 },
  { key: "online_booking_enabled", label: "Online booking", help: "Turns the public booking page on or off.", kind: "toggle" },
];

/** Mirrors the backend rules. Returns "" when the value is fine. */
function problem(key: string, raw: string): string {
  const value = raw.trim();
  const n = Number(value);
  switch (key) {
    case "clinic_name":
      return value && value.length <= 100 ? "" : "The clinic name is required (100 characters at most).";
    case "clinic_address":
      return value && value.length <= 255 ? "" : "The clinic address is required (255 characters at most).";
    case "consultation_fee":
      return isMoney(value) ? "" : "The consultation fee must be an amount between 0 and 1,000,000 (two decimals at most).";
    case "default_slot_minutes":
      return /^\d+$/.test(value) && n >= 5 && n <= 120 ? "" : "The slot length must be a whole number from 5 to 120.";
    case "booking_window_days":
      return /^\d+$/.test(value) && n >= 1 && n <= 365 ? "" : "The booking window must be a whole number from 1 to 365.";
    default:
      return "";
  }
}

const toMap = (rows: SettingRow[]): Record<string, string> => Object.fromEntries(rows.map((r) => [r.setting_key, r.setting_value]));

export default function ClinicSettingsPage() {
  const [rows, setRows] = useState<SettingRow[] | null>(null);
  const [original, setOriginal] = useState<Record<string, string>>({});
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  function apply(list: SettingRow[]) {
    setRows(list);
    setOriginal(toMap(list));
    setValues(toMap(list));
  }

  useEffect(() => {
    let cancelled = false;
    adminApi
      .settings()
      .then((list) => {
        if (!cancelled) apply(list);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load the settings.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    const changed = FIELDS.filter((f) => (values[f.key] ?? "") !== (original[f.key] ?? ""));
    if (changed.length === 0) return setMessage("Nothing was changed.");
    for (const f of changed) {
      const text = problem(f.key, values[f.key] ?? "");
      if (text) return setError(text);
    }
    setBusy(true);
    try {
      const saved = await adminApi.saveSettings(Object.fromEntries(changed.map((f) => [f.key, (values[f.key] ?? "").trim()])));
      apply(saved);
      setMessage("Settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the settings.");
    } finally {
      setBusy(false);
    }
  }

  const lastChange = rows?.reduce<string | null>((latest, r) => (!latest || r.updated_at > latest ? r.updated_at : latest), null) ?? null;

  return (
    <section className="max-w-2xl">
      <h1 className="text-2xl font-semibold">Clinic Settings</h1>
      <p className="mt-1 text-slate-600">Clinic name, fee, and online booking switch.</p>
      {!rows && !error && <p className="mt-6 text-slate-500">Loading...</p>}

      {rows && (
        <form onSubmit={submit} className="mt-6 space-y-5 rounded-xl border border-slate-200 bg-white p-5">
          {FIELDS.map((f) => (
            <div key={f.key}>
              {f.kind === "toggle" ? (
                <label className="flex items-center gap-3 text-sm font-medium">
                  <input
                    type="checkbox"
                    checked={(values[f.key] ?? "true") === "true"}
                    onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.checked ? "true" : "false" }))}
                  />
                  {f.label}: {(values[f.key] ?? "true") === "true" ? "open" : "closed"}
                </label>
              ) : (
                <label className="block text-sm font-medium">
                  {f.label}
                  <input
                    className={`${inputClass} mt-1`}
                    type="text"
                    inputMode={f.kind === "number" ? (f.key === "consultation_fee" ? "decimal" : "numeric") : undefined}
                    autoComplete="off"
                    maxLength={f.maxLength}
                    value={values[f.key] ?? ""}
                    onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: f.clean ? f.clean(e.target.value) : e.target.value }))}
                  />
                </label>
              )}
              <p className="mt-1 text-xs text-slate-500">{f.help}</p>
            </div>
          ))}
          {lastChange && <p className="text-xs text-slate-500">Last changed {formatDateTime(lastChange)}.</p>}
          {error && <Alert kind="error">{error}</Alert>}
          {message && <Alert kind="success">{message}</Alert>}
          <button type="submit" disabled={busy} className={primaryButton}>
            {busy ? "Saving..." : "Save settings"}
          </button>
        </form>
      )}
      {!rows && error && <Alert kind="error">{error}</Alert>}
    </section>
  );
}