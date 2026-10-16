import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import ConnectServerModal from "../components/ConnectServerModal";
import FormField from "../components/FormField";
import { useAuth } from "../hooks/useAuth";
import { useServerConnection } from "../hooks/useServerConnection";
import { getErrorMessage } from "../utils/errors";
import { ROLE_HOME } from "../utils/roles";

export default function LoginPage() {
  const { user, loading, signIn } = useAuth();
  const { status, checking, error: serverError, connect, disconnect } = useServerConnection();
  const navigate = useNavigate();

  const [modalOpen, setModalOpen] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-gray-500">Loading...</div>;
  }
  if (user) return <Navigate to={ROLE_HOME[user.role]} replace />;

  const connected = status?.connected === true;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!username.trim() || !password) {
      setError("Enter your username and password.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const signedIn = await signIn(username.trim(), password);
      navigate(ROLE_HOME[signedIn.role], { replace: true });
    } catch (e: unknown) {
      setError(getErrorMessage(e));
      setPassword("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md space-y-6 rounded-lg bg-white p-8 shadow">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AppointMed</h1>
          <p className="text-sm text-gray-500">Staff sign in</p>
        </div>

        {/* Step 1: server connection */}
        <section className="space-y-3 rounded border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-sm">
            <span
              className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-green-500" : "bg-gray-400"}`}
              aria-hidden="true"
            />
            <span className="text-gray-700">
              {checking
                ? "Checking server..."
                : connected
                  ? `Connected to ${status?.host}:${status?.port} as ${status?.user}`
                  : "Not connected to a server"}
            </span>
          </div>
          {serverError && <p className="text-sm text-red-600">{serverError}</p>}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              disabled={checking}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {connected ? "Change server" : "Connect to Server"}
            </button>
            {connected && (
              <button
                type="button"
                onClick={() => void disconnect()}
                className="rounded border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                Disconnect
              </button>
            )}
          </div>
        </section>

        {/* Step 2: staff credentials (locked until connected) */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField
            id="username"
            label="Username"
            value={username}
            onChange={setUsername}
            autoComplete="username"
            disabled={!connected || submitting}
          />
          <FormField
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            autoComplete="current-password"
            disabled={!connected || submitting}
          />
          {!connected && !checking && (
            <p className="text-xs text-gray-500">Connect to the server first to sign in.</p>
          )}
          {error && (
            <p role="alert" className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={!connected || submitting}
            className="w-full rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>

      <ConnectServerModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConnect={connect}
      />
    </main>
  );
}