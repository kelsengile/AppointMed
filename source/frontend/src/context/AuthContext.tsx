// Holds the signed-in user. The token lives in api/client.ts; the name/role live in sessionStorage.
// The profile picture is fetched after sign-in and kept in memory only.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "../api/endpoints";
import { UNAUTHORIZED_EVENT, getToken, setToken } from "../api/client";
import type { Role, SessionUser } from "../types";

interface AuthValue {
  user: SessionUser | null;
  login: (username: string, password: string) => Promise<Role>;
  logout: () => void;
  /** Update the name or picture shown in the side panel after the profile changes. */
  updateSession: (patch: Partial<Pick<SessionUser, "fullName" | "avatar">>) => void;
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

// The picture is not stored (it can be large); only name and role are.
function persist(user: SessionUser): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify({ username: user.username, fullName: user.fullName, role: user.role }));
  } catch {
    /* storage unavailable: session lasts until refresh */
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
    persist(next);
    return next.role;
  }, []);

  const updateSession = useCallback((patch: Partial<Pick<SessionUser, "fullName" | "avatar">>) => {
    setUser((previous) => {
      if (!previous) return previous;
      const next = { ...previous, ...patch };
      persist(next);
      return next;
    });
  }, []);

  // The API client fires this when the server rejects the token (expired or deactivated account).
  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  // After sign-in (or a page refresh) load the picture and the latest name. A rejected token signs the user out.
  const username = user?.username;
  useEffect(() => {
    if (!username) return;
    let cancelled = false;
    authApi
      .me()
      .then((profile) => {
        if (!cancelled) setUser((previous) => (previous ? { ...previous, fullName: profile.full_name, avatar: profile.avatar } : previous));
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [username]);

  const value = useMemo(() => ({ user, login, logout, updateSession }), [user, login, logout, updateSession]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}