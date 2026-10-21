import { useCallback, useEffect, useState } from "react";

// Empty in development (Vite proxies /api). Set VITE_API_URL if the API is hosted on another domain.
const API_URL = import.meta.env.VITE_API_URL ?? "";

type Status = "checking" | "online" | "offline";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

function StatusRow({ label, status, detail }: { label: string; status: Status; detail: string }) {
  const color =
    status === "online" ? "text-brand-600" : status === "offline" ? "text-red-700" : "text-slate-500";
  return (
    <li className="flex items-center justify-between border-t border-slate-200 py-3">
      <span>{label}</span>
      <span className={`font-semibold ${color}`}>{detail}</span>
    </li>
  );
}

export default function App() {
  const [api, setApi] = useState<Status>("checking");
  const [db, setDb] = useState<Status>("checking");

  const check = useCallback(async () => {
    setApi("checking");
    setDb("checking");
    try {
      await getJson("/api/health");
      setApi("online");
    } catch {
      setApi("offline");
    }
    try {
      const result = await getJson<{ connected: boolean }>("/api/health/db");
      setDb(result.connected ? "online" : "offline");
    } catch {
      setDb("offline");
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  return (
    <main className="grid min-h-screen place-items-center p-6">
      <section className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8">
        <h1 className="text-2xl font-semibold">AppointMed</h1>
        <p className="mb-5 mt-1 text-slate-600">
          The web app is running. Below is the connection to the backend.
        </p>

        <ul className="mb-5">
          <StatusRow
            label="Backend API"
            status={api}
            detail={api === "checking" ? "Checking..." : api === "online" ? "Online" : "Offline"}
          />
          <StatusRow
            label="Database"
            status={db}
            detail={db === "checking" ? "Checking..." : db === "online" ? "Connected" : "Not connected"}
          />
        </ul>

        {api === "offline" && (
          <p className="mb-4 text-sm text-red-700">
            Cannot reach the backend. Start it with <code>uvicorn main:app --reload</code> in the source folder.
          </p>
        )}
        {api === "online" && db === "offline" && (
          <p className="mb-4 text-sm text-red-700">
            The backend is running but cannot reach MySQL. Check source/.env and that MySQL is started.
          </p>
        )}

        <button
          type="button"
          onClick={() => void check()}
          className="rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          Check again
        </button>
      </section>
    </main>
  );
}
