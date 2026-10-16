import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { ServerCredentials } from "../types/auth";
import { parseAddress } from "../utils/address";
import { getErrorMessage } from "../utils/errors";
import FormField from "./FormField";

interface ConnectServerModalProps {
  open: boolean;
  onClose: () => void;
  onConnect: (credentials: ServerCredentials) => Promise<void>;
}

export default function ConnectServerModal({ open, onClose, onConnect }: ConnectServerModalProps) {
  const [address, setAddress] = useState("localhost:3306");
  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Clear the previous error and password every time the popup opens.
  useEffect(() => {
    if (open) {
      setError(null);
      setPassword("");
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !submitting) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, submitting, onClose]);

  if (!open) return null;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = parseAddress(address);
    if (!parsed) {
      setError("Enter a valid address, like localhost or 192.168.1.5:3306.");
      return;
    }
    if (!user.trim()) {
      setError("Enter the server username.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onConnect({ host: parsed.host, port: parsed.port, user: user.trim(), password });
      onClose();
    } catch (e: unknown) {
      setError(getErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/40 p-4">
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="connect-title"
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow-xl"
      >
        <div>
          <h2 id="connect-title" className="text-lg font-semibold text-gray-900">
            Connect to server
          </h2>
          <p className="text-sm text-gray-500">Enter the MySQL server details.</p>
        </div>

        <FormField
          id="server-address"
          label="Server address"
          value={address}
          onChange={setAddress}
          placeholder="localhost:3306"
          autoFocus
          disabled={submitting}
        />
        <FormField
          id="server-user"
          label="Server username"
          value={user}
          onChange={setUser}
          placeholder="appointmed_user"
          disabled={submitting}
        />
        <FormField
          id="server-password"
          label="Server password"
          type="password"
          value={password}
          onChange={setPassword}
          disabled={submitting}
        />

        {error && (
          <p role="alert" className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="rounded px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "Connecting..." : "Connect"}
          </button>
        </div>
      </form>
    </div>
  );
}