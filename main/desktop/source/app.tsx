import { useEffect, useState } from "react";

const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

type Status = "checking" | "ok" | "error";

async function check(path: string): Promise<Status> {
  try {
    const response = await fetch(`${API_URL}${path}`);
    const data = await response.json();
    return data.status === "ok" ? "ok" : "error";
  } catch {
    return "error";
  }
}

function StatusRow({ label, status }: { label: string; status: Status }) {
  const color =
    status === "ok" ? "text-green-600" : status === "error" ? "text-red-600" : "text-gray-500";
  const text = status === "ok" ? "Connected" : status === "error" ? "Not reachable" : "Checking...";
  return (
    <div className="flex items-center justify-between rounded border border-gray-200 px-4 py-3">
      <span className="font-medium text-gray-700">{label}</span>
      <span className={`font-semibold ${color}`}>{text}</span>
    </div>
  );
}

export default function App() {
  const [api, setApi] = useState<Status>("checking");
  const [db, setDb] = useState<Status>("checking");

  useEffect(() => {
    check("/health").then(setApi);
    check("/health/db").then(setDb);
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md space-y-4 rounded-lg bg-white p-8 shadow">
        <h1 className="text-2xl font-bold text-gray-900">AppointMed Desktop</h1>
        <p className="text-sm text-gray-500">Staff application. Setup check page.</p>
        <StatusRow label="Backend API" status={api} />
        <StatusRow label="MySQL database" status={db} />
      </div>
    </main>
  );
}