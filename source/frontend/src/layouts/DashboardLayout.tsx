import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { NAV } from "../config/navigation";
import { useAuth } from "../context/AuthContext";
import type { Role } from "../types";

const TITLE: Record<Role, string> = { doctor: "Doctor", nurse: "Nurse", admin: "Admin" };

export default function DashboardLayout({ role }: { role: Role }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const items = NAV[role];

  const link = ({ isActive }: { isActive: boolean }) =>
    `block rounded-lg px-3 py-2 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
      isActive ? "bg-brand-100 text-brand-900" : "text-slate-700 hover:bg-slate-100"
    }`;

  const renderLinks = (bottom: boolean) =>
    items
      .filter((i) => !!i.bottom === bottom)
      .map((i) => (
        <NavLink key={i.path} to={`/${role}/${i.path}`} className={link} onClick={() => setOpen(false)}>
          {i.label}
        </NavLink>
      ));

  return (
    <div className="min-h-screen md:flex">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="m-3 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm md:hidden"
      >
        Menu
      </button>

      <aside
        className={`${open ? "flex" : "hidden"} fixed inset-y-0 left-0 z-40 w-64 flex-col border-r border-slate-200 bg-white p-4 md:sticky md:top-0 md:flex md:h-screen`}
      >
        <div className="mb-4 px-3">
          <p className="text-lg font-semibold text-brand-700">AppointMed</p>
          <p className="text-xs text-slate-500">{TITLE[role]} portal</p>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto" aria-label="Main">
          {renderLinks(false)}
        </nav>
        <nav className="space-y-1 border-t border-slate-200 pt-3" aria-label="Secondary">
          {renderLinks(true)}
          <button
            type="button"
            onClick={() => {
              logout();
              navigate("/");
            }}
            className="block w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50"
          >
            Log out
          </button>
          <p className="truncate px-3 pt-1 text-xs text-slate-500">Signed in as {user?.username}</p>
        </nav>
      </aside>

      <main className="min-w-0 flex-1 p-6 md:p-10">
        <Outlet />
      </main>
    </div>
  );
}