import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { getCurrentUser, login } from "../api/auth";
import type { AuthUser } from "../types/auth";

const TOKEN_KEY = "appointmed.token";

export interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  signIn: (username: string, password: string) => Promise<AuthUser>;
  signOut: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore a session (e.g. after a hot reload) if the saved token is still valid.
  useEffect(() => {
    const saved = sessionStorage.getItem(TOKEN_KEY);
    if (!saved) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    getCurrentUser(saved)
      .then((restored) => {
        if (!cancelled) setUser(restored);
      })
      .catch(() => sessionStorage.removeItem(TOKEN_KEY))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (username: string, password: string) => {
    const response = await login(username, password);
    sessionStorage.setItem(TOKEN_KEY, response.access_token);
    setUser(response.user);
    return response.user;
  }, []);

  const signOut = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signOut }),
    [user, loading, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}