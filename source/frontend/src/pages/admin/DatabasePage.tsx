// Admin: browse and edit table rows, run one SQL statement, and download a full SQL backup.
import { useState, type FormEvent } from "react";
import { databaseApi } from "../../api/databaseApi";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import Modal from "../../components/Modal";
import { dangerButton, inputClass, primaryButton, secondaryButton } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import type { DbCell, DbColumn, DbQueryResult, DbRow, DbTableData } from "../../types/database";

const PAGE_SIZE = 25;

function Cell({ value }: { value: DbCell }) {
  if (value === null) return <span className="italic text-slate-400">NULL</span>;
  return <>{String(value)}</>;
}

/** "enum('a','b')" -> ["a", "b"], or null when the column is not an ENUM. */
function enumOptions(type: string): string[] | null {
  if (!/^enum\(/i.test(type)) return null;
  return Array.from(type.matchAll(/'((?:[^']|'')*)'/g), (m) => m[1].replace(/''/g, "'"));
}

function FieldInput({ column, value, onChange }: { column: DbColumn; value: string; onChange: (v: string) => void }) {
  const options = enumOptions(column.type);
  if (options) {
    return (
      <select className={`${inputClass} mt-1`} value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">{column.nullable ? "NULL / default" : "Default"}</option>
        {options.map((o) => (
          <option key={o}>{o}</option>
        ))}
      </select>
    );
  }
  if (["text", "mediumtext", "longtext"].includes(column.data_type)) {
    return <textarea className={`${inputClass} mt-1`} rows={3} value={value} onChange={(e) => onChange(e.target.value)} />;
  }
  return (
    <input
      className={`${inputClass} mt-1`}
      autoComplete="off"
      placeholder={column.nullable ? "NULL" : ""}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

// Add (row = null) or edit one row. On edit only the changed fields are sent.
function RowForm({ table, row, onClose, onSaved }: { table: DbTableData; row: DbRow | null; onClose: () => void; onSaved: (message: string) => void }) {
  const editing = row !== null;
  const original: DbRow = row ?? {};
  const fields = table.columns.filter((c) => !c.hidden && !c.generated && (!editing || !c.primary));
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(fields.map((c) => [c.name, original[c.name] === null || original[c.name] === undefined ? "" : String(original[c.name])])),
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const payload: Record<string, string> = {};
    for (const c of fields) {
      const now = values[c.name] ?? "";
      const before = original[c.name] === null || original[c.name] === undefined ? "" : String(original[c.name]);
      if (editing ? now !== before : now.trim() !== "") payload[c.name] = now;
    }
    if (editing && Object.keys(payload).length === 0) return setError("Nothing was changed.");
    setBusy(true);
    setError("");
    try {
      if (row && table.primary_key) await databaseApi.updateRow(table.name, String(row[table.primary_key]), payload);
      else await databaseApi.insertRow(table.name, payload);
      onSaved(editing ? "Row updated." : "Row added.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the row.");
      setBusy(false);
    }
  }

  return (
    <Modal title={`${editing ? "Edit row in" : "Add row to"} ${table.name}`} onClose={onClose} wide>
      <form onSubmit={submit} className="space-y-3">
        {editing && table.primary_key && (
          <p className="text-sm text-slate-600">
            {table.primary_key} = <strong>{String(original[table.primary_key])}</strong>
          </p>
        )}
        <div className="grid gap-3 sm:grid-cols-2">
          {fields.map((c) => (
            <label key={c.name} className="block text-sm font-medium">
              {c.name}
              <span className="ml-2 text-xs font-normal text-slate-500">
                {c.type}
                {c.auto ? ", auto" : ""}
                {!c.nullable && !c.auto ? ", required" : ""}
              </span>
              <FieldInput column={c} value={values[c.name] ?? ""} onChange={(v) => setValues((prev) => ({ ...prev, [c.name]: v }))} />
            </label>
          ))}
        </div>
        {!editing && <p className="text-xs text-slate-500">Leave a field blank to use its default value.</p>}
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

// One SQL statement at a time. Reads show a table. INSERT, UPDATE and DELETE report how many rows changed.
function SqlConsole({ onChanged }: { onChanged: () => void }) {
  const [sql, setSql] = useState("SELECT * FROM clinic_settings");
  const [result, setResult] = useState<DbQueryResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run() {
    const writes = /^\s*(insert|update|delete)\b/i.test(sql);
    if (writes && !window.confirm("This statement changes data right away and cannot be undone. Run it?")) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const response = await databaseApi.query(sql);
      setResult(response);
      if (response.affected !== null) onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run the statement.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <p className="text-sm text-slate-600">
        One statement at a time: SELECT, SHOW, DESCRIBE, EXPLAIN, INSERT, UPDATE or DELETE (UPDATE and DELETE need a WHERE). The audit log cannot be
        changed, and table structure changes need the MySQL root account.
      </p>
      <textarea
        aria-label="SQL statement"
        className={`${inputClass} mt-3 font-mono`}
        rows={5}
        maxLength={5000}
        spellCheck={false}
        value={sql}
        onChange={(e) => setSql(e.target.value)}
      />
      <button type="button" className={`${primaryButton} mt-3`} disabled={busy || !sql.trim()} onClick={() => void run()}>
        {busy ? "Running..." : "Run statement"}
      </button>

      {error && <Alert kind="error">{error}</Alert>}
      {result && result.affected !== null && <Alert kind="success">{result.kind.toUpperCase()} done: {result.affected} row(s) changed.</Alert>}
      {result && result.affected === null && (
        <>
          <p className="mt-4 text-sm text-slate-500">
            {result.rows.length} row{result.rows.length === 1 ? "" : "s"}
            {result.truncated ? " (only the first 500 are shown)" : ""}
          </p>
          <div className="mt-2 overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  {result.columns.map((c, i) => (
                    <th key={`${c}-${i}`} className="whitespace-nowrap px-3 py-2 font-medium">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.length === 0 && (
                  <tr>
                    <td colSpan={Math.max(1, result.columns.length)} className="px-3 py-4 text-slate-500">No rows.</td>
                  </tr>
                )}
                {result.rows.map((row, r) => (
                  <tr key={r} className="border-t border-slate-100">
                    {row.map((cell, c) => (
                      <td key={c} className="max-w-xs truncate px-3 py-2" title={cell === null ? "NULL" : String(cell)}>
                        <Cell value={cell} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default function DatabasePage() {
  const tables = usePolling(() => databaseApi.tables(), 0);
  const [tab, setTab] = useState<"tables" | "sql">("tables");
  const [selected, setSelected] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const data = usePolling<DbTableData | null>(
    () => (selected ? databaseApi.table(selected, search.trim(), PAGE_SIZE, offset) : Promise.resolve(null)),
    0,
    [selected, search, offset],
  );
  const [form, setForm] = useState<{ row: DbRow | null } | null>(null);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [backupBusy, setBackupBusy] = useState(false);

  const table = data.data;
  const visibleColumns = table?.columns.filter((c) => !c.hidden) ?? [];
  const total = table?.total ?? 0;
  const first = total === 0 ? 0 : offset + 1;
  const last = Math.min(offset + PAGE_SIZE, total);

  async function refresh() {
    await Promise.all([tables.reload(), data.reload()]);
  }

  function choose(name: string) {
    setSelected(name);
    setSearch("");
    setOffset(0);
    setMessage("");
    setActionError("");
  }

  async function backup() {
    setBackupBusy(true);
    setMessage("");
    setActionError("");
    try {
      const { blob, filename } = await databaseApi.backup();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setMessage(`Backup downloaded as ${filename}.`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not create the backup.");
    } finally {
      setBackupBusy(false);
    }
  }

  async function remove(row: DbRow) {
    if (!table?.primary_key) return;
    const key = String(row[table.primary_key]);
    if (!window.confirm(`Delete the row where ${table.primary_key} = ${key} from ${table.name}? This cannot be undone.`)) return;
    setActionError("");
    setMessage("");
    try {
      await databaseApi.deleteRow(table.name, key);
      setMessage("Row deleted.");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not delete the row.");
    } finally {
      await refresh();
    }
  }

  const tabClass = (active: boolean) =>
    `rounded-lg px-3 py-1.5 text-sm ${active ? "bg-brand-600 text-white" : "border border-slate-300 bg-white hover:bg-slate-50"}`;

  return (
    <section>
      <h1 className="text-2xl font-semibold">Database</h1>
      <p className="mt-1 text-slate-600">Browse and edit table data, run SQL, and download a backup. Changes apply immediately and are recorded in the audit log.</p>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-5">
        <div className="max-w-xl">
          <h2 className="font-semibold">Backup</h2>
          <p className="mt-1 text-sm text-slate-600">
            Downloads one .sql file with the structure and the current data of every table. It includes password hashes, so keep it private.
            Restore it as the MySQL root user: <code className="rounded bg-slate-100 px-1">mysql -u root -p appointmed &lt; file.sql</code>
          </p>
        </div>
        <button type="button" className={primaryButton} disabled={backupBusy} onClick={() => void backup()}>
          {backupBusy ? "Creating backup..." : "Create and download backup"}
        </button>
      </div>

      {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
      {(actionError || tables.error || data.error) && <Alert kind="error">{actionError || tables.error || data.error}</Alert>}

      <div className="mt-6 flex gap-2" role="tablist" aria-label="Database tools">
        <button role="tab" aria-selected={tab === "tables"} className={tabClass(tab === "tables")} onClick={() => setTab("tables")}>
          Tables
        </button>
        <button role="tab" aria-selected={tab === "sql"} className={tabClass(tab === "sql")} onClick={() => setTab("sql")}>
          SQL console
        </button>
      </div>

      {tab === "sql" && (
        <div className="mt-4">
          <SqlConsole onChanged={() => void refresh()} />
        </div>
      )}

      {tab === "tables" && (
        <div className="mt-4 grid gap-6 lg:grid-cols-[16rem_1fr]">
          <div>
            {tables.loading && !tables.data && <p className="text-slate-500">Loading...</p>}
            <ul className="space-y-2">
              {tables.data?.map((t) => (
                <li key={t.name}>
                  <button
                    type="button"
                    onClick={() => choose(t.name)}
                    className={`w-full rounded-xl border p-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                      selected === t.name ? "border-brand-600 bg-brand-50" : "border-slate-200 bg-white hover:bg-slate-50"
                    }`}
                  >
                    <p className="font-semibold">{t.name}</p>
                    <p className="text-sm text-slate-500">
                      {t.rows} row{t.rows === 1 ? "" : "s"} - {t.columns} columns
                    </p>
                    {t.read_only && <Badge tone="slate">Read only</Badge>}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="min-w-0">
            {!selected && <p className="text-slate-500">Choose a table to see its rows.</p>}
            {selected && data.loading && !table && <p className="text-slate-500">Loading...</p>}
            {table && (
              <>
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{table.name}</h2>
                    <p className="text-sm text-slate-500">
                      Primary key: {table.primary_key ?? "none"}
                      {table.read_only ? " - read only" : ""}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <input
                      type="search"
                      value={search}
                      maxLength={100}
                      onChange={(e) => {
                        setSearch(e.target.value);
                        setOffset(0);
                      }}
                      placeholder="Search this table"
                      aria-label="Search this table"
                      className={`${inputClass} w-56`}
                    />
                    {table.can_insert && (
                      <button type="button" className={primaryButton} onClick={() => setForm({ row: null })}>
                        Add row
                      </button>
                    )}
                  </div>
                </div>

                <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-xs text-slate-500">
                      <tr>
                        {visibleColumns.map((c) => (
                          <th key={c.name} className="whitespace-nowrap px-3 py-2 font-medium" title={c.type}>
                            {c.name}
                            {c.primary ? " (PK)" : ""}
                          </th>
                        ))}
                        {!table.read_only && <th className="px-3 py-2 font-medium">Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {table.rows.length === 0 && (
                        <tr>
                          <td colSpan={visibleColumns.length + 1} className="px-3 py-4 text-slate-500">No rows found.</td>
                        </tr>
                      )}
                      {table.rows.map((row, i) => (
                        <tr key={table.primary_key ? String(row[table.primary_key]) : i} className="border-t border-slate-100 align-top">
                          {visibleColumns.map((c) => (
                            <td key={c.name} className="max-w-xs truncate px-3 py-2" title={row[c.name] === null ? "NULL" : String(row[c.name])}>
                              <Cell value={row[c.name] ?? null} />
                            </td>
                          ))}
                          {!table.read_only && (
                            <td className="whitespace-nowrap px-3 py-2">
                              <div className="flex gap-1">
                                <button className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50" onClick={() => setForm({ row })}>
                                  Edit
                                </button>
                                <button className={`${dangerButton} !px-2 !py-1`} onClick={() => void remove(row)}>
                                  Delete
                                </button>
                              </div>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
                  <span>
                    Showing {first} to {last} of {total}
                  </span>
                  <div className="flex gap-2">
                    <button type="button" className={secondaryButton} disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
                      Previous
                    </button>
                    <button type="button" className={secondaryButton} disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>
                      Next
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {form && table && (
        <RowForm
          table={table}
          row={form.row}
          onClose={() => setForm(null)}
          onSaved={(text) => {
            setForm(null);
            setMessage(text);
            void refresh();
          }}
        />
      )}
    </section>
  );
}