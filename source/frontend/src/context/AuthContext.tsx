import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { Role, SessionUser } from "../types";

interface AuthValue {
  user: SessionUser | null;
  login: (username: string, password: string) => Role | null;
  logout: () => void;
}

const KEY = "appointmed.session";
const AuthContext = createContext<AuthValue | null>(null);

function load(): SessionUser | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as SessionUser) : null;
  } catch {
    return null;
  }
}

// TEMPORARY: the backend has no login endpoint yet, so the role is guessed from the
// seed usernames and the password is NOT checked. Replace the body of login() with a
// call to POST /api/auth/login once it exists.
function guessRole(username: string): Role | null {
  const name = username.trim().toLowerCase();
  if (name.startsWith("admin")) return "admin";
  if (name.startsWith("dr.")) return "doctor";
  if (name.startsWith("nurse.")) return "nurse";
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(load);

  const login = useCallback((username: string, password: string) => {
    const role = guessRole(username);
    if (!role || !password) return null;
    const next = { username: username.trim(), role };
    setUser(next);
    try {
      sessionStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* storage unavailable: session lasts until refresh */
    }
    return role;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    try {
      sessionStorage.removeItem(KEY);
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}