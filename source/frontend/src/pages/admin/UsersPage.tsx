// Admin: create, edit, deactivate and reset passwords for staff. Doctors also get a weekly schedule editor.
import { useState, type FormEvent } from "react";
import { adminApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import Modal from "../../components/Modal";
import PasswordRequirements from "../../components/PasswordRequirements";
import ScheduleEditor from "../../components/ScheduleEditor";
import { inputClass, primaryButton, secondaryButton } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { usePolling } from "../../hooks/usePolling";
import type { DoctorRef, Role, UserCreatePayload, UserRecord } from "../../types";
import { formatDateTime } from "../../utils/format";
import { cleanEmail, cleanName, cleanSpecialization, cleanUsername, isEmail, isName, isUsername } from "../../utils/input";
import { PASSWORD_MAX, passwordProblem } from "../../utils/password";

const ROLES: Role[] = ["doctor", "nurse", "admin"];

type ModalState =
  | { kind: "form"; user: UserRecord | null } // null = create
  | { kind: "password"; user: UserRecord }
  | { kind: "schedule"; user: UserRecord }
  | null;

// Create (editing = null) or edit form.
function UserForm({ editing, doctors, onClose, onSaved }: { editing: UserRecord | null; doctors: DoctorRef[]; onClose: () => void; onSaved: (message: string) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>(editing?.role ?? "nurse");
  const [fullName, setFullName] = useState(editing?.full_name ?? "");
  const [email, setEmail] = useState(editing?.email ?? "");
  const [specialization, setSpecialization] = useState(editing?.specialization ?? "");
  const [assigned, setAssigned] = useState(editing?.assigned_doctor_id ? String(editing.assigned_doctor_id) : "");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!editing) {
      if (!isUsername(username.trim())) return setError("Username: 3 to 50 letters, numbers, dots, dashes or underscores.");
      const problem = passwordProblem(password);
      if (problem) return setError(problem);
    }
    if (!isName(fullName.trim())) return setError("Enter the full name (letters only, at least 2).");
    if (email.trim() && !isEmail(email.trim())) return setError("Enter a valid email address.");
    if (role === "nurse" && !assigned) return setError("Choose the doctor this nurse supports.");

    const common = {
      full_name: fullName.trim(),
      email: email.trim() || null,
      specialization: role === "doctor" ? specialization.trim() || null : null,
      assigned_doctor_id: role === "nurse" ? Number(assigned) : null,
    };
    setBusy(true);
    setError("");
    try {
      if (editing) {
        await adminApi.updateUser(editing.id, common);
        onSaved(`${common.full_name} was updated.`);
      } else {
        const payload: UserCreatePayload = { username: username.trim(), password, role, ...common };
        await adminApi.createUser(payload);
        onSaved(`${common.full_name} was created.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the user.");
      setBusy(false);
    }
  }

  return (
    <Modal title={editing ? `Edit ${editing.username}` : "Add user"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        {!editing && (
          <>
            <label className="block text-sm font-medium">
              Username
              <input className={`${inputClass} mt-1`} maxLength={50} autoComplete="off" value={username} onChange={(e) => setUsername(cleanUsername(e.target.value))} />
            </label>
            <div>
              <label className="block text-sm font-medium">
                Password
                <input type="password" maxLength={PASSWORD_MAX} autoComplete="new-password" className={`${inputClass} mt-1`} value={password} onChange={(e) => setPassword(e.target.value)} />
              </label>
              <PasswordRequirements password={password} />
            </div>
            <label className="block text-sm font-medium">
              Role
              <select className={`${inputClass} mt-1`} value={role} onChange={(e) => setRole(e.target.value as Role)}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r[0].toUpperCase() + r.slice(1)}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
        <label className="block text-sm font-medium">
          Full name
          <input className={`${inputClass} mt-1`} maxLength={100} autoComplete="off" value={fullName} onChange={(e) => setFullName(cleanName(e.target.value))} />
        </label>
        <label className="block text-sm font-medium">
          Email (optional)
          <input type="email" className={`${inputClass} mt-1`} maxLength={100} value={email} onChange={(e) => setEmail(cleanEmail(e.target.value))} />
        </label>
        {role === "doctor" && (
          <label className="block text-sm font-medium">
            Specialization
            <input className={`${inputClass} mt-1`} maxLength={100} value={specialization} onChange={(e) => setSpecialization(cleanSpecialization(e.target.value))} />
          </label>
        )}
        {role === "nurse" && (
          <label className="block text-sm font-medium">
            Supports doctor
            <select className={`${inputClass} mt-1`} value={assigned} onChange={(e) => setAssigned(e.target.value)}>
              <option value="">Select a doctor...</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_name}
                </option>
              ))}
            </select>
          </label>
        )}
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

function PasswordForm({ target, onClose, onSaved }: { target: UserRecord; onClose: () => void; onSaved: (message: string) => void }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const problem = passwordProblem(password);
    if (problem) return setError(problem);
    if (password !== confirm) return setError("The passwords do not match.");
    setBusy(true);
    setError("");
    try {
      await adminApi.resetPassword(target.id, password);
      onSaved(`Password reset for ${target.username}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset the password.");
      setBusy(false);
    }
  }

  return (
    <Modal title={`Reset password: ${target.username}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="block text-sm font-medium">
            New password
            <input type="password" maxLength={PASSWORD_MAX} autoComplete="new-password" className={`${inputClass} mt-1`} value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          <PasswordRequirements password={password} />
        </div>
        <label className="block text-sm font-medium">
          Confirm new password
          <input type="password" maxLength={PASSWORD_MAX} autoComplete="new-password" className={`${inputClass} mt-1`} value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </label>
        {error && <Alert kind="error">{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className={secondaryButton}>
            Cancel
          </button>
          <button type="submit" disabled={busy} className={primaryButton}>
            {busy ? "Saving..." : "Reset password"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function UsersPage() {
  const { user: me } = useAuth();
  const [role, setRole] = useState("");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState<ModalState>(null);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const users = usePolling(() => adminApi.users(role, search.trim()), 0, [role, search]);
  const doctors = usePolling(() => adminApi.doctors(), 0);

  function saved(text: string) {
    setModal(null);
    setMessage(text);
    void users.reload();
    void doctors.reload();
  }

  async function toggleActive(u: UserRecord) {
    const verb = u.is_active ? "Deactivate" : "Reactivate";
    if (!window.confirm(`${verb} ${u.full_name}?`)) return;
    setActionError("");
    setMessage("");
    try {
      await adminApi.setActive(u.id, !u.is_active);
      setMessage(`${u.full_name} was ${u.is_active ? "deactivated" : "reactivated"}.`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not change the account.");
    } finally {
      await users.reload();
      await doctors.reload();
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Users</h1>
          <p className="mt-1 text-slate-600">Create, edit, and deactivate doctors, nurses, and admins.</p>
        </div>
        <button type="button" className={primaryButton} onClick={() => setModal({ kind: "form", user: null })}>
          Add user
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <input type="search" maxLength={100} value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or username" aria-label="Search users" className={`${inputClass} max-w-xs`} />
        <select aria-label="Filter by role" className={`${inputClass} w-40`} value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">All roles</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r[0].toUpperCase() + r.slice(1)}s
            </option>
          ))}
        </select>
      </div>

      {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
      {(actionError || users.error) && <Alert kind="error">{actionError || users.error}</Alert>}
      {users.loading && !users.data && <p className="mt-6 text-slate-500">Loading...</p>}

      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="px-3 py-2 font-medium">Name</th>
              <th className="px-3 py-2 font-medium">Role</th>
              <th className="px-3 py-2 font-medium">Details</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Last sign-in</th>
              <th className="px-3 py-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.data && users.data.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-slate-500">No users found.</td>
              </tr>
            )}
            {users.data?.map((u) => (
              <tr key={u.id} className="border-t border-slate-100 align-top">
                <td className="px-3 py-2">
                  <p className="font-medium">{u.full_name}</p>
                  <p className="text-xs text-slate-500">{u.username}{u.email ? ` - ${u.email}` : ""}</p>
                </td>
                <td className="px-3 py-2 capitalize">{u.role}</td>
                <td className="px-3 py-2 text-slate-600">
                  {u.role === "doctor" && (u.specialization ?? "-")}
                  {u.role === "nurse" && (u.assigned_doctor_name ? `Supports ${u.assigned_doctor_name}` : "No doctor assigned")}
                  {u.role === "admin" && "-"}
                </td>
                <td className="px-3 py-2">
                  <Badge tone={u.is_active ? "green" : "red"}>{u.is_active ? "Active" : "Inactive"}</Badge>
                </td>
                <td className="whitespace-nowrap px-3 py-2">{formatDateTime(u.last_login_at)}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    <button className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50" onClick={() => setModal({ kind: "form", user: u })}>
                      Edit
                    </button>
                    <button className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50" onClick={() => setModal({ kind: "password", user: u })}>
                      Password
                    </button>
                    {u.role === "doctor" && (
                      <button className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50" onClick={() => setModal({ kind: "schedule", user: u })}>
                        Schedule
                      </button>
                    )}
                    <button
                      className="rounded-lg border border-red-300 px-2 py-1 text-red-700 hover:bg-red-50 disabled:opacity-50"
                      disabled={u.username === me?.username && u.is_active}
                      title={u.username === me?.username ? "You cannot deactivate your own account" : undefined}
                      onClick={() => void toggleActive(u)}
                    >
                      {u.is_active ? "Deactivate" : "Reactivate"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal?.kind === "form" && <UserForm editing={modal.user} doctors={doctors.data ?? []} onClose={() => setModal(null)} onSaved={saved} />}
      {modal?.kind === "password" && <PasswordForm target={modal.user} onClose={() => setModal(null)} onSaved={saved} />}
      {modal?.kind === "schedule" && <ScheduleEditor doctor={modal.user} onClose={() => setModal(null)} onSaved={() => saved(`Working hours saved for ${modal.user.full_name}.`)} />}
    </section>
  );
}