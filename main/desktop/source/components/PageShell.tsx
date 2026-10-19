import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ROLE_LABEL } from "../utils/roles";

export default function PageShell({ title, children }: { title: string; children: ReactNode }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = () => {
    signOut();
    navigate("/", { replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
        <div>
          <span className="text-lg font-bold text-blue-600">AppointMed</span>
          <span className="ml-3 text-sm text-gray-500">{title}</span>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <div className="text-right text-sm">
              <div className="font-medium text-gray-900">{user.full_name}</div>
              <div className="text-gray-500">{ROLE_LABEL[user.role]}</div>
            </div>
          )}
          <button
            onClick={handleSignOut}
            className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}