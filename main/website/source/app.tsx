import { useEffect, useState } from "react";

const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

type Status = "checking" | "ok" | "error";

export default function App() {
  const [api, setApi] = useState<Status>("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => response.json())
      .then((data) => setApi(data.status === "ok" ? "ok" : "error"))
      .catch(() => setApi("error"));
  }, []);

  const color =
    api === "ok" ? "text-green-600" : api === "error" ? "text-red-600" : "text-gray-500";
  const text = api === "ok" ? "Connected" : api === "error" ? "Not reachable" : "Checking...";

  return (
    <main className="flex min-h-screen items-center justify-center bg-blue-50">
      <div className="w-full max-w-md space-y-4 rounded-lg bg-white p-8 text-center shadow">
        <h1 className="text-3xl font-bold text-blue-700">AppointMed</h1>
        <p className="text-gray-600">Online appointment booking is coming soon.</p>
        <p className="text-sm text-gray-500">
          Backend API: <span className={`font-semibold ${color}`}>{text}</span>
        </p>
      </div>
    </main>
  );
}