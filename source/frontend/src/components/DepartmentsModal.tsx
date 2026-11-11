// Popup that lists every clinical department, with a search box. Opening a department shows its doctors.
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { DepartmentItem } from "../types/department";
import type { StaffMember } from "../types/staff";
import { weekdayList } from "../utils/format";
import { staffPhotoUrl } from "../utils/staffArt";
import Modal from "./Modal";
import { inputClass, secondaryButton } from "./ui";

function DeptIcon({ department }: { department: DepartmentItem }) {
  if (department.icon) {
    return <img src={department.icon} alt="" aria-hidden className="h-11 w-11 shrink-0 rounded-xl object-contain shadow-sm" />;
  }
  return (
    <span aria-hidden className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-100 text-lg font-bold text-brand-700">
      {department.name.charAt(0).toUpperCase()}
    </span>
  );
}

const sameName = (a: string | null | undefined, b: string) => (a ?? "").trim().toLowerCase() === b.trim().toLowerCase();

export default function DepartmentsModal({
  departments,
  staff,
  initialQuery = "",
  initialOpen = "",
  onClose,
}: {
  departments: DepartmentItem[];
  staff: StaffMember[];
  initialQuery?: string;
  initialOpen?: string; // department name to open straight away
  onClose: () => void;
}) {
  const [query, setQuery] = useState(initialQuery);
  const [selected, setSelected] = useState<DepartmentItem | null>(() => departments.find((d) => d.name === initialOpen) ?? null);

  const shown = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return departments;
    return departments.filter((d) => d.name.toLowerCase().includes(term) || d.description.toLowerCase().includes(term));
  }, [departments, query]);

  const doctors = useMemo(
    () => (selected ? staff.filter((s) => s.role === "doctor" && sameName(s.specialization, selected.name)) : []),
    [selected, staff],
  );

  return (
    <Modal title={selected ? selected.name : "Clinical departments"} onClose={onClose} wide>
      {selected ? (
        <div>
          <button type="button" className={secondaryButton} onClick={() => setSelected(null)}>
            ← All departments
          </button>
          <div className="mt-4 flex gap-3">
            <DeptIcon department={selected} />
            <p className="text-sm leading-relaxed text-slate-600">{selected.description}</p>
          </div>

          <h3 className="mt-6 text-base font-bold text-brand-900">
            Doctors in {selected.name} ({doctors.length})
          </h3>
          {doctors.length === 0 && <p className="mt-2 text-sm text-slate-500">Doctors coming soon.</p>}
          <ul className="mt-3 max-h-[50vh] space-y-3 overflow-y-auto pr-1">
            {doctors.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3">
                <div className="flex items-center gap-3">
                  {d.has_photo ? (
                    <img src={staffPhotoUrl(d.id, d.photo_version)} alt="" className="h-12 w-12 rounded-full object-cover" />
                  ) : (
                    <span aria-hidden className="grid h-12 w-12 place-items-center rounded-full bg-brand-100 font-bold text-brand-700">
                      {d.full_name.replace(/^Dr\.?\s+/i, "").charAt(0).toUpperCase()}
                    </span>
                  )}
                  <div>
                    <p className="font-semibold text-brand-900">{d.full_name}</p>
                    <p className="text-xs text-slate-500">{d.weekdays.length ? `Sees patients ${weekdayList(d.weekdays)}` : "Schedule to be announced"}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link to={`/staff/${d.id}`} className={`${secondaryButton} !px-3 !py-1.5`}>
                    View profile
                  </Link>
                  <Link to={`/book?doctor=${d.id}`} className="book-btn rounded-xl px-3 py-1.5 text-sm font-semibold text-white">
                    Book
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <>
          <p className="text-sm text-slate-600">
            {departments.length} department{departments.length === 1 ? "" : "s"}. Open one to see its doctors.
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
                      <button type="button" onClick={() => setSelected(d)} className="text-xs font-semibold text-brand-700 hover:underline">
                        View doctors
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </Modal>
  );
}