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
    if (!raw) return null;
    const saved = JSON.parse(raw) as Partial<SessionUser> & { username: string; role: Role };
    // Sessions saved before fullName existed fall back to the username.
    return { username: saved.username, role: saved.role, fullName: saved.fullName ?? saved.username };
  } catch {
    return null;
  }
}

// TEMPORARY: the backend has no login endpoint yet, so the role and full name are guessed
// from the seed usernames and the password is NOT checked. Replace the body of login() with
// a call to POST /api/auth/login once it exists, and use users.full_name from the response.
const FULL_NAMES: Record<string, string> = {
  admin: "Eugene H. Krabs",
  "dr.cheeks": "Dr. Sandy Cheeks",
  "dr.tentacles": "Dr. Squidward Tentacles",
  "nurse.spongebob": "SpongeBob SquarePants",
  "nurse.patrick": "Patrick Star",
};

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
    const clean = username.trim();
    const next: SessionUser = { username: clean, role, fullName: FULL_NAMES[clean.toLowerCase()] ?? clean };
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