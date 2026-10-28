// Admin: add, rename, change status, and delete exam rooms.
import { useState, type FormEvent } from "react";
import { adminApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import Modal from "../../components/Modal";
import { dangerButton, inputClass, primaryButton, secondaryButton, statusTone } from "../../components/ui";
import { usePolling } from "../../hooks/usePolling";
import type { RoomItem, RoomStatus } from "../../types";
import { formatDateTime } from "../../utils/format";
import { cleanRoomName } from "../../utils/input";

const STATUSES: RoomStatus[] = ["Available", "Occupied", "Maintenance"];

// `room` is null when adding.
function RoomForm({ room, onClose, onSaved }: { room: RoomItem | null; onClose: () => void; onSaved: (message: string) => void }) {
  const [name, setName] = useState(room?.room_name ?? "");
  const [status, setStatus] = useState<RoomStatus>(room?.status ?? "Available");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return setError("Enter a room name.");
    setBusy(true);
    setError("");
    try {
      if (room) await adminApi.updateRoom(room.id, name.trim(), status);
      else await adminApi.createRoom(name.trim(), status);
      onSaved(room ? "Room updated." : "Room added.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the room.");
      setBusy(false);
    }
  }

  return (
    <Modal title={room ? "Edit room" : "Add room"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm font-medium">
          Room name
          <input className={`${inputClass} mt-1`} maxLength={50} value={name} onChange={(e) => setName(cleanRoomName(e.target.value))} autoComplete="off" />
        </label>
        <label className="block text-sm font-medium">
          Status
          <select className={`${inputClass} mt-1`} value={status} onChange={(e) => setStatus(e.target.value as RoomStatus)}>
            {STATUSES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
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

export default function RoomsPage() {
  const rooms = usePolling(() => adminApi.rooms(), 10000);
  const [editing, setEditing] = useState<RoomItem | "new" | null>(null);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");

  async function remove(room: RoomItem) {
    if (!window.confirm(`Delete ${room.room_name}?`)) return;
    setActionError("");
    setMessage("");
    try {
      await adminApi.deleteRoom(room.id);
      setMessage(`${room.room_name} was deleted.`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not delete the room.");
    } finally {
      await rooms.reload();
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Rooms</h1>
          <p className="mt-1 text-slate-600">Add, rename, and change room status.</p>
        </div>
        <button type="button" className={primaryButton} onClick={() => setEditing("new")}>
          Add room
        </button>
      </div>

      {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
      {(actionError || rooms.error) && <Alert kind="error">{actionError || rooms.error}</Alert>}
      {rooms.loading && !rooms.data && <p className="mt-6 text-slate-500">Loading...</p>}

      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="px-3 py-2 font-medium">Room</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Patient inside</th>
              <th className="px-3 py-2 font-medium">Last changed</th>
              <th className="px-3 py-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rooms.data && rooms.data.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-slate-500">No rooms yet.</td>
              </tr>
            )}
            {rooms.data?.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-3 py-2 font-medium">{r.room_name}</td>
                <td className="px-3 py-2"><Badge tone={statusTone(r.status)}>{r.status}</Badge></td>
                <td className="px-3 py-2">{r.occupant ?? "-"}</td>
                <td className="px-3 py-2 text-slate-600">
                  {formatDateTime(r.updated_at)}
                  {r.updated_by_name ? ` by ${r.updated_by_name}` : ""}
                </td>
                <td className="px-3 py-2">
                  <div className="flex gap-2">
                    <button className="rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50" onClick={() => setEditing(r)}>
                      Edit
                    </button>
                    <button className={`${dangerButton} !px-2 !py-1`} onClick={() => void remove(r)}>
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
        <RoomForm
          room={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={(text) => {
            setEditing(null);
            setMessage(text);
            void rooms.reload();
          }}
        />
      )}
    </section>
  );
}