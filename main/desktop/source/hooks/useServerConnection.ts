import { useCallback, useEffect, useState } from "react";
import { connectServer, disconnectServer, getServerStatus } from "../api/server";
import type { ServerCredentials, ServerStatus } from "../types/auth";
import { getErrorMessage } from "../utils/errors";

export function useServerConnection() {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // The backend remembers its connection, so ask it on load.
  useEffect(() => {
    getServerStatus()
      .then(setStatus)
      .catch((e: unknown) => setError(getErrorMessage(e)))
      .finally(() => setChecking(false));
  }, []);

  /** Throws an ApiError when the connection fails, so the popup can show it. */
  const connect = useCallback(async (credentials: ServerCredentials) => {
    setStatus(await connectServer(credentials));
    setError(null);
  }, []);

  const disconnect = useCallback(async () => {
    try {
      setStatus(await disconnectServer());
    } catch (e: unknown) {
      setError(getErrorMessage(e));
    }
  }, []);

  return { status, checking, error, connect, disconnect };
}