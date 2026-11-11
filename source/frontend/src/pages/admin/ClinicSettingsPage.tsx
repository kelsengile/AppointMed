import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { adminApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import Modal from "../../components/Modal";
import { dangerButton, inputClass, primaryButton, secondaryButton } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import type { SettingRow } from "../../types";
import type { DepartmentItem, DepartmentPayload } from "../../types/department";
import { formatDateTime } from "../../utils/format";
import { fitImage } from "../../utils/image";
import { cleanAddress, cleanClinicName, cleanInt, cleanMoney, cleanText, isMoney } from "../../utils/input";
import { useSite } from "../../hooks/useSite";
import BrandingSettings from "../../components/BrandingSettings";
import { DEFAULT_LOGO } from "../../config/branding";

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

// Add or edit one department (specialty). `department` is null when adding.
function DepartmentForm({ department, onClose, onSaved }: { department: DepartmentItem | null; onClose: () => void; onSaved: (message: string) => void }) {
  const [name, setName] = useState(department?.name ?? "");
  const [description, setDescription] = useState(department?.description ?? "");
  const [featured, setFeatured] = useState(department?.is_featured ?? false);
  const [active, setActive] = useState(department?.is_active ?? true);
  const [order, setOrder] = useState(String(department?.sort_order ?? 100));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (name.trim().length < 2) return setError("Enter the department name.");
    if (description.trim().length < 3) return setError("Enter a short description.");
    const body: DepartmentPayload = {
      name: name.trim(),
      description: description.trim(),
      is_featured: featured,
      is_active: active,
      sort_order: Number(order) || 0,
    };
    setBusy(true);
    setError("");
    try {
      if (department) await adminApi.updateDepartment(department.id, body);
      else await adminApi.createDepartment(body);
      onSaved(department ? "Department updated." : "Department added.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the department.");
      setBusy(false);
    }
  }

  return (
    <Modal title={department ? "Edit department" : "Add department"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm font-medium">
          Name
          <input className={`${inputClass} mt-1`} maxLength={100} autoComplete="off" value={name} onChange={(e) => setName(cleanClinicName(e.target.value))} />
        </label>
        <label className="block text-sm font-medium">
          Description
          <textarea className={`${inputClass} mt-1`} rows={3} maxLength={255} value={description} onChange={(e) => setDescription(cleanText(e.target.value, 255))} />
        </label>
        <label className="block text-sm font-medium">
          Order (lower numbers come first)
          <input className={`${inputClass} mt-1 w-28`} inputMode="numeric" maxLength={4} value={order} onChange={(e) => setOrder(cleanInt(e.target.value, 4))} />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={featured} onChange={(e) => setFeatured(e.target.checked)} />
          Featured (shown as a card on the front page)
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
          Visible on the website
        </label>
        <p className="text-xs text-slate-500">
          Doctors pick their specialization from this list on the Users page. Renaming a department updates its doctors automatically,
          and a department that still has doctors cannot be deleted.
        </p>
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

// Departments and specialties shown on the front page: text, icon, order, and visibility.
function DepartmentsSettings() {
  const list = usePolling(() => adminApi.departments(), 0);
  const [editing, setEditing] = useState<DepartmentItem | "new" | null>(null);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const iconTarget = useRef<number | null>(null);

  async function chooseIcon(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    const id = iconTarget.current;
    if (!file || id === null) return;
    setBusyId(id);
    setActionError("");
    setMessage("");
    try {
      await adminApi.setDepartmentIcon(id, await fitImage(file, 128, 128, "image/png", 140_000));
      setMessage("Icon updated.");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not upload the icon.");
    } finally {
      setBusyId(null);
      await list.reload();
    }
  }

  async function removeIcon(d: DepartmentItem) {
    setBusyId(d.id);
    setActionError("");
    setMessage("");
    try {
      await adminApi.removeDepartmentIcon(d.id);
      setMessage("Icon removed.");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not remove the icon.");
    } finally {
      setBusyId(null);
      await list.reload();
    }
  }

  async function remove(d: DepartmentItem) {
    if (!window.confirm(`Delete the ${d.name} department? Doctors are not deleted.`)) return;
    setBusyId(d.id);
    setActionError("");
    setMessage("");
    try {
      await adminApi.deleteDepartment(d.id);
      setMessage(`${d.name} was deleted.`);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not delete the department.");
    } finally {
      setBusyId(null);
      await list.reload();
    }
  }

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Departments and specialties</h2>
          <p className="mt-1 text-sm text-slate-600">
            Managed here, shown on the front page. "Learn More" lists the doctors whose specialization matches the department name.
          </p>
        </div>
        <button type="button" className={primaryButton} onClick={() => setEditing("new")}>
          Add department
        </button>
      </div>

      <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={chooseIcon} aria-label="Choose a department icon" />
      {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
      {(actionError || list.error) && <Alert kind="error">{actionError || list.error}</Alert>}
      {list.loading && !list.data && <p className="mt-4 text-slate-500">Loading...</p>}

      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="px-3 py-2 font-medium">Icon</th>
              <th className="px-3 py-2 font-medium">Department</th>
              <th className="px-3 py-2 font-medium">Doctors</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {list.data && list.data.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-slate-500">No departments yet.</td>
              </tr>
            )}
            {list.data?.map((d) => (
              <tr key={d.id} className="border-t border-slate-100 align-top">
                <td className="px-3 py-2">
                  {d.icon ? (
                    <img src={d.icon} alt="" className="h-10 w-10 rounded-lg object-contain" />
                  ) : (
                    <span aria-hidden className="grid h-10 w-10 place-items-center rounded-lg bg-brand-100 font-bold text-brand-700">
                      {d.name.charAt(0).toUpperCase()}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <p className="font-medium">{d.name}</p>
                  <p className="max-w-md text-xs text-slate-500">{d.description}</p>
                </td>
                <td className="px-3 py-2">{d.doctor_count}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    <Badge tone={d.is_active ? "green" : "red"}>{d.is_active ? "Visible" : "Hidden"}</Badge>
                    {d.is_featured && <Badge tone="blue">Featured</Badge>}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    <button className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50" onClick={() => setEditing(d)}>
                      Edit
                    </button>
                    <button
                      className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50 disabled:opacity-60"
                      disabled={busyId === d.id}
                      onClick={() => {
                        iconTarget.current = d.id;
                        fileInput.current?.click();
                      }}
                    >
                      Upload icon
                    </button>
                    {d.icon && (
                      <button className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50 disabled:opacity-60" disabled={busyId === d.id} onClick={() => void removeIcon(d)}>
                        Remove icon
                      </button>
                    )}
                    <button className={`${dangerButton} !px-2 !py-1`} disabled={busyId === d.id} onClick={() => void remove(d)}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <DepartmentForm
          department={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={(text) => {
            setEditing(null);
            setMessage(text);
            void list.reload();
          }}
        />
      )}
    </section>
  );
}

export default function ClinicSettingsPage() {
  const { logoSrc } = useSite();
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
    <section>
      <h1 className="text-2xl font-semibold">Clinic Settings</h1>
      <p className="mt-1 text-slate-600">Clinic name, fee, and online booking switch.</p>
      {!rows && !error && <p className="mt-6 text-slate-500">Loading...</p>}

      {rows && (
        <div className="mt-6 flex flex-col gap-6 lg:flex-row">
          {/* Left: the white card with only the settings */}
          <form
            onSubmit={submit}
            className="grid content-start gap-x-8 gap-y-8 rounded-xl border border-slate-200 bg-white p-6 md:grid-cols-2 lg:w-2/3 lg:p-10"
          >
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
            <div className="md:col-span-2">
              {lastChange && <p className="text-xs text-slate-500">Last changed {formatDateTime(lastChange)}.</p>}
              {error && <Alert kind="error">{error}</Alert>}
              {message && <Alert kind="success">{message}</Alert>}
              <button type="submit" disabled={busy} className={`${primaryButton} mt-4`}>
                {busy ? "Saving..." : "Save settings"}
              </button>
            </div>
          </form>

          {/* Right: the logo, outside the white card (hidden on small screens) */}
          <div className="hidden items-center justify-center lg:flex lg:flex-1">
            <img src={logoSrc ?? DEFAULT_LOGO} alt="AppointMed logo" className="h-auto w-full max-w-md object-contain" />
          </div>
        </div>
      )}
      {!rows && error && <Alert kind="error">{error}</Alert>}
      <BrandingSettings />
      <DepartmentsSettings />
    </section>
  );
}