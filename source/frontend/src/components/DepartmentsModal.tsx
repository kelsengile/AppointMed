// Popup that lists every clinical department, with a search box. Opened from the landing page.
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { DepartmentItem } from "../types/department";
import Modal from "./Modal";
import { inputClass } from "./ui";

function DeptIcon({ department }: { department: DepartmentItem }) {
  if (department.icon) {
    return <img src={department.icon} alt="" aria-hidden className="h-11 w-11 shrink-0 rounded-xl shadow-sm" />;
  }
  return (
    <span aria-hidden className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-100 text-lg font-bold text-brand-700">
      {department.name.charAt(0).toUpperCase()}
    </span>
  );
}

export default function DepartmentsModal({
  departments,
  initialQuery = "",
  onClose,
}: {
  departments: DepartmentItem[];
  initialQuery?: string;
  onClose: () => void;
}) {
  const [query, setQuery] = useState(initialQuery);

  const shown = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return departments;
    return departments.filter((d) => d.name.toLowerCase().includes(term) || d.description.toLowerCase().includes(term));
  }, [departments, query]);

  return (
    <Modal title="Clinical departments" onClose={onClose} wide>
      <p className="text-sm text-slate-600">
        {departments.length} department{departments.length === 1 ? "" : "s"}. Choose a doctor and a time on the booking page.
      </p>
      <input
        type="search"
        autoFocus
        maxLength={100}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search departments"
        aria-label="Search departments"
        className={`${inputClass} mt-3`}
      />

      <div className="mt-4 max-h-[60vh] overflow-y-auto pr-1">
        {shown.length === 0 && <p className="py-6 text-center text-sm text-slate-500">No departments match your search.</p>}
        <ul className="grid gap-3 sm:grid-cols-2">
          {shown.map((d) => (
            <li key={d.id} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-3">
              <DeptIcon department={d} />
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-semibold text-brand-900">{d.name}</h3>
                <p className="mt-0.5 text-xs leading-relaxed text-slate-600">{d.description}</p>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <span className="text-xs text-slate-500">
                    {d.doctor_count > 0 ? `${d.doctor_count} doctor${d.doctor_count === 1 ? "" : "s"}` : "Doctors coming soon"}
                  </span>
                  {d.doctor_count > 0 && (
                    <Link to="/book" className="text-xs font-semibold text-brand-700 hover:underline">
                      Book now
                    </Link>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Modal>
  );
}