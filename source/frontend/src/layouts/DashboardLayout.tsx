import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import Logo from "../components/Logo";
import { NAV } from "../config/Navigation";
import { useAuth } from "../context/AuthContext";
import type { NavItem, Role } from "../types";

const TITLE: Record<Role, string> = { doctor: "Doctor", nurse: "Nurse", admin: "Admin" };
const DESKTOP_MIN_WIDTH = 768; // matches Tailwind's md breakpoint

interface Group {
  name: string;
  items: NavItem[];
}

// Icon for the open/close button: a window with a left panel.
function PanelIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <line x1="9" y1="4" x2="9" y2="20" />
    </svg>
  );
}

export default function DashboardLayout({ role }: { role: Role }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  // Open by default on desktop, closed on mobile.
  const [open, setOpen] = useState(() => window.innerWidth >= DESKTOP_MIN_WIDTH);

  const items = NAV[role];
  const profile = items.find((i) => i.pin === "profile");
  const settings = items.find((i) => i.pin === "settings");
  const help = items.find((i) => i.pin === "help");

  // Group the unpinned items by their `group` header, keeping the order from Navigation.ts.
  const groups: Group[] = [];
  for (const item of items) {
    if (item.pin) continue;
    const name = item.group ?? "";
    const existing = groups.find((g) => g.name === name);
    if (existing) existing.items.push(item);
    else groups.push({ name, items: [item] });
  }

  const fullName = user?.fullName ?? user?.username ?? "";
  const initial = fullName.replace(/^dr\.\s*/i, "").charAt(0).toUpperCase();

  // On phones the panel covers the page, so close it after choosing a page.
  const closeOnMobile = () => {
    if (window.innerWidth < DESKTOP_MIN_WIDTH) setOpen(false);
  };

  const link = ({ isActive }: { isActive: boolean }) =>
    `block rounded-xl px-3 py-2 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
      isActive ? "bg-gradient-to-r from-[#365983] to-[#527DAA] text-white shadow-md" : "text-landing-body hover:bg-brand-50"
    }`;

  const profileLink = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-xl px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
      isActive ? "bg-brand-100" : "hover:bg-brand-50"
    }`;

  const toggleButton =
    "rounded-xl p-2 text-landing-body hover:bg-brand-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500";

  return (
    <div className="app-theme min-h-screen bg-gradient-to-b from-[#F4F9FE] to-[#EAF4FC] md:flex">
      <aside
        className={`${open ? "flex" : "hidden"} fixed inset-y-3 left-3 z-40 w-64 flex-col rounded-3xl border border-white/70 bg-white/90 p-4 shadow-[0_18px_40px_rgba(53,88,130,0.18)] backdrop-blur md:sticky md:top-3 md:m-3 md:h-[calc(100vh-1.5rem)] md:shrink-0`}
      >
        {/* Brand: logo and name link to the landing page, with the close button on the right */}
        <div className="flex items-center justify-between gap-2 px-3 pb-3">
          <Link
            to="/"
            aria-label="Go to the AppointMed home page"
            title="Go to the home page"
            className="rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            <Logo size={32} />
          </Link>
          <button type="button" onClick={() => setOpen(false)} className={toggleButton} aria-label="Close side panel" title="Close side panel">
            <PanelIcon />
          </button>
        </div>

        {/* Profile: picture (or initial), full name, and role underneath */}
        {profile && (
          <NavLink
            to={`/${role}/${profile.path}`}
            className={(s) => `${profileLink(s)} border-t border-[#DCE9FB]`}
            onClick={closeOnMobile}
            aria-label="Open your profile"
          >
            {user?.avatar ? (
              <img src={user.avatar} alt="" className="h-10 w-10 shrink-0 rounded-full object-cover" />
            ) : (
              <span
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#365983] to-[#527DAA] text-base font-semibold text-white"
                aria-hidden="true"
              >
                {initial}
              </span>
            )}
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-landing-heading">{fullName}</span>
              <span className="block text-xs text-landing-muted">{TITLE[role]}</span>
            </span>
          </NavLink>
        )}

        {/* Page groups, each with a header and a separation line */}
        <nav className="mt-3 flex-1 overflow-y-auto" aria-label="Main">
          {groups.map((group) => (
            <div key={group.name} className="border-t border-[#DCE9FB] py-3">
              <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-landing-soft">{group.name}</p>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavLink key={item.path} to={`/${role}/${item.path}`} className={link} onClick={closeOnMobile}>
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom: Settings and a "?" Help button on one line, then Log out */}
        <div className="space-y-1 border-t border-[#DCE9FB] pt-3">
          <div className="flex gap-1">
            {settings && (
              <NavLink to={`/${role}/${settings.path}`} className={(s) => `${link(s)} flex-1`} onClick={closeOnMobile}>
                {settings.label}
              </NavLink>
            )}
            {help && (
              <NavLink
                to={`/${role}/${help.path}`}
                className={(s) => `${link(s)} w-10 text-center`}
                onClick={closeOnMobile}
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
            className="block w-full rounded-xl px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1 p-6 md:p-10 md:pl-6">
        {/* Shown only while the side panel is closed */}
        {!open && (
          <button type="button" onClick={() => setOpen(true)} className={`${toggleButton} -ml-2 mb-4 border border-[#BBD4F3] bg-white`} aria-label="Open side panel" title="Open side panel">
            <PanelIcon />
          </button>
        )}
        <Outlet />
      </main>
    </div>
  );
}