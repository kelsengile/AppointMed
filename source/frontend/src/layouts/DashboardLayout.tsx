import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import Logo from "../components/Logo";
import { NAV } from "../config/navigation";
import { useAuth } from "../context/AuthContext";
import type { NavItem, Role } from "../types";

const TITLE: Record<Role, string> = { doctor: "Doctor", nurse: "Nurse", admin: "Admin" };

interface Group {
  name: string;
  items: NavItem[];
}

export default function DashboardLayout({ role }: { role: Role }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const items = NAV[role];
  const profile = items.find((i) => i.pin === "profile");
  const settings = items.find((i) => i.pin === "settings");
  const help = items.find((i) => i.pin === "help");

  // Group the unpinned items by their `group` header, keeping the order from navigation.ts.
  const groups: Group[] = [];
  for (const item of items) {
    if (item.pin) continue;
    const name = item.group ?? "";
    const existing = groups.find((g) => g.name === name);
    if (existing) existing.items.push(item);
    else groups.push({ name, items: [item] });
  }

  const username = user?.username ?? "";
  const initial = username.charAt(0).toUpperCase();
  const close = () => setOpen(false);

  const link = ({ isActive }: { isActive: boolean }) =>
    `block rounded-lg px-3 py-2 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
      isActive ? "bg-brand-100 text-brand-900" : "text-slate-700 hover:bg-slate-100"
    }`;

  const profileLink = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-lg px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
      isActive ? "bg-brand-100" : "hover:bg-slate-100"
    }`;

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
        {/* Brand: logo and name */}
        <div className="px-3 pb-3">
          <Logo size={32} />
        </div>

        {/* Profile: circle with initial, username, and role underneath */}
        {profile && (
          <NavLink
            to={`/${role}/${profile.path}`}
            className={(s) => `${profileLink(s)} border-t border-slate-200`}
            onClick={close}
            aria-label="Open your profile"
          >
            <span
              className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-brand-600 text-base font-semibold text-white"
              aria-hidden="true"
            >
              {initial}
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-brand-900">{username}</span>
              <span className="block text-xs text-slate-500">{TITLE[role]}</span>
            </span>
          </NavLink>
        )}

        {/* Page groups, each with a header and a separation line */}
        <nav className="mt-3 flex-1 overflow-y-auto" aria-label="Main">
          {groups.map((group) => (
            <div key={group.name} className="border-t border-slate-200 py-3">
              <p className="px-3 pb-1 text-xs font-semibold text-slate-500">{group.name}</p>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavLink key={item.path} to={`/${role}/${item.path}`} className={link} onClick={close}>
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom: Settings and a "?" Help button on one line, then Log out */}
        <div className="space-y-1 border-t border-slate-200 pt-3">
          <div className="flex gap-1">
            {settings && (
              <NavLink to={`/${role}/${settings.path}`} className={(s) => `${link(s)} flex-1`} onClick={close}>
                {settings.label}
              </NavLink>
            )}
            {help && (
              <NavLink
                to={`/${role}/${help.path}`}
                className={(s) => `${link(s)} w-10 text-center`}
                onClick={close}
                aria-label="Help"
                title="Help"
              >
                ?
              </NavLink>
            )}
          </div>
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
        </div>
      </aside>

      <main className="min-w-0 flex-1 p-6 md:p-10">
        <Outlet />
      </main>
    </div>
  );
}