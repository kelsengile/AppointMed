import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "../api/endpoints";
import { UNAUTHORIZED_EVENT, getToken, setToken } from "../api/client";
import type { Role, SessionUser } from "../types";

interface AuthValue {
  user: SessionUser | null;
  login: (username: string, password: string) => Promise<Role>;
  logout: () => void;
}

const KEY = "appointmed.session";
const AuthContext = createContext<AuthValue | null>(null);

// The session is only trusted if a login token is also stored.
function load(): SessionUser | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw || !getToken()) return null;
    const saved = JSON.parse(raw) as SessionUser;
    return { username: saved.username, role: saved.role, fullName: saved.fullName ?? saved.username };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(load);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    try {
      sessionStorage.removeItem(KEY);
    } catch {
      /* ignore */
    }
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const response = await authApi.login(username.trim(), password);
    setToken(response.access_token);
    const next: SessionUser = {
      username: response.user.username,
      fullName: response.user.full_name,
      role: response.user.role,
    };
    setUser(next);
    try {
      sessionStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* storage unavailable: session lasts until refresh */
    }
    return next.role;
  }, []);

  // The API client fires this when the server rejects the token (expired or deactivated account).
  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}