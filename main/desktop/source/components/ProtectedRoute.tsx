import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { Role } from "../types/auth";
import { ROLE_HOME } from "../utils/roles";

interface ProtectedRouteProps {
  role: Role;
  children: ReactNode;
}

/** Convenience only. The backend is what really enforces permissions. */
export default function ProtectedRoute({ role, children }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-gray-500">Loading...</div>;
  }
  if (!user) return <Navigate to="/" replace />;
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role]} replace />;
  return <>{children}</>;
}