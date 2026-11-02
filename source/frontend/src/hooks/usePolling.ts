import { useCallback, useEffect, useRef, useState } from "react";

// Loads data now, and again every `intervalMs` (0 = load once). Reloads when `deps` change.
// Only the newest request may update the screen, so a slow old answer can never overwrite a newer one.
export function usePolling<T>(loader: () => Promise<T>, intervalMs = 0, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const latest = useRef(0);

  const reload = useCallback(async () => {
    const id = ++latest.current;
    try {
      const result = await loaderRef.current();
      if (id !== latest.current) return;
      setData(result);
      setError("");
    } catch (e) {
      if (id !== latest.current) return;
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      if (id === latest.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    void reload();
    if (!intervalMs) return;
    const id = window.setInterval(() => void reload(), intervalMs);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload, intervalMs, ...deps]);

  return { data, error, loading, reload };
}