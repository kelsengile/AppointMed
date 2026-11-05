/*
 * Landing page, rebuilt from the Figma design "Desktop - 6" (node 19:86):
 * floating pill navbar, light hero over a hospital photo, About us band,
 * services bento grid, "Meet Our Staff" cards (every active account, from /api/public/staff),
 * clinical departments grid (from /api/public/departments) with a "View all" popup,
 * and a light-blue footer (address and clinic name from Clinic Settings).
 *
 * Image assets were exported from the Figma file into frontend/public/.
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { departmentApi } from "../api/departmentApi";
import { publicApi } from "../api/endpoints";
import { staffDirectoryApi } from "../api/staffDirectoryApi";
import DepartmentsModal from "../components/DepartmentsModal";
import { useAuth } from "../context/AuthContext";
import type { Role } from "../types";
import type { Catalog } from "../types";
import type { DepartmentItem } from "../types/department";
import type { StaffMember } from "../types/staff";

// Figma font for the whole landing page (already loaded in index.html).
const pageFont = { fontFamily: "Poppins, system-ui, -apple-system, sans-serif" };

// ---------------- sample content from the design ----------------

const ABOUT_LEAD =
  "At AppointMed, we believe that accessing quality healthcare should be seamless, transparent, and centered around you. Our modern clinic brings together a dedicated team of experienced medical professionals, cutting-edge diagnostics, and patient-first values to deliver comprehensive care for individuals and families.";
const ABOUT_SECOND =
  "From routine checkups and chronic condition management to effortless online booking, we are committed to making your healthcare journey as smooth as possible—ensuring you receive the right attention, right when you need it.";

const SERVICES: { title: string; text: string; image: string }[] = [
  {
    title: "General Medicine",
    text: "Checkups, illness, and long-term condition care for adults.",
    image: "/service-general.png",
  },
  {
    title: "Prescriptions",
    text: "Receive a written prescription at the end of your visit.",
    image: "/service-prescriptions.png",
  },
  {
    title: "Preventive Care",
    text: "Routine health screenings, blood pressure monitoring, and general physical assessments.",
    image: "/service-preventive.png",
  },
  {
    title: "Smart Scheduling",
    text: "Seamless online booking, instant appointment confirmations, and schedule management.",
    image: "/service-smart.png",
  },
];

// Shown only if the departments request fails (for example the database has not been updated yet).
const FALLBACK_DEPARTMENTS: DepartmentItem[] = [
  { id: -1, name: "Cardiology", description: "Heart disease diagnosis, treatment and cardiac surgery. ECG, Echo, and stress testing available.", icon: "/dept-cardiology.png", is_featured: true, doctor_count: 0 },
  { id: -2, name: "Neurology", description: "Expert care for neurological disorders including stroke, epilepsy, and movement disorders.", icon: "/dept-neurology.png", is_featured: true, doctor_count: 0 },
  { id: -3, name: "Orthopedics", description: "Bone, joint and muscle care including sports injuries, fractures, and joint replacement surgery.", icon: "/dept-orthopedics.png", is_featured: true, doctor_count: 0 },
  { id: -4, name: "Pediatrics", description: "Comprehensive child health care from newborns to adolescents with specialized pediatric specialists.", icon: "/dept-pediatrics.png", is_featured: true, doctor_count: 0 },
  { id: -5, name: "Ophthalmology", description: "Complete eye care services including LASIK, cataract surgery, and vision treatments.", icon: "/dept-ophthalmology.png", is_featured: true, doctor_count: 0 },
  { id: -6, name: "General Medicine", description: "Primary care, routine checkups, preventive health screenings and chronic disease management.", icon: "/dept-general.png", is_featured: true, doctor_count: 0 },
];

const DEFAULT_ADDRESS = "123 Medical Center Drive, Healthcare City, HC 45678";

const ROLE_LABEL: Record<Role, string> = { doctor: "Doctor", nurse: "Nurse", admin: "Administrator" };
const ROLE_BADGE: Record<Role, string> = {
  doctor: "bg-brand-50 text-landing-body",
  nurse: "bg-green-100 text-landing-leaf",
  admin: "bg-slate-100 text-slate-700",
};

// Small line icons for the footer contact list.
function ContactIcon({ kind }: { kind: "pin" | "phone" | "mail" | "clock" }) {
  const paths: Record<typeof kind, string> = {
    pin: "M12 21s-6.5-5.2-6.5-10a6.5 6.5 0 1 1 13 0c0 4.8-6.5 10-6.5 10Zm0-7.8a2.3 2.3 0 1 0 0-4.6 2.3 2.3 0 0 0 0 4.6Z",
    phone:
      "M6.6 3h2.9l1.4 4.1-2 1.4a12.4 12.4 0 0 0 5.6 5.6l1.4-2 4.1 1.4v2.9c0 1-.8 1.7-1.7 1.6C10 17.4 6.6 14 5.02 6.7 4.9 5.8 5.6 5 6.6 5Z",
    mail: "M4 6h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Zm1.4 2 6.6 4.6L18.6 8H5.4Z",
    clock: "M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18Zm0 2.2v.1a6.8 6.8 0 1 0 6.8 6.7v-.1A6.8 6.8 0 0 0 12 5.2Zm.9 2.8v4.2l3.1 1.9-.9 1.5-4-2.4V8h1.8Z",
  };
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="#355882" aria-hidden className="mt-0.5 shrink-0">
      <path d={paths[kind]} />
    </svg>
  );
}

// ---------------- helpers ----------------

const WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]; // 1 = Monday

// "Mon - Fri" when the runs are contiguous, "Mon, Wed, Fri" otherwise.
function weekdayLabel(weekdays: number[]): string {
  if (!weekdays?.length) return "Schedule TBA";
  const sorted = [...weekdays].sort((a, b) => a - b);
  const contiguous = sorted[sorted.length - 1] - sorted[0] === sorted.length - 1;
  const words = sorted.map((d) => WEEKDAY_NAMES[d - 1] ?? "");
  return contiguous ? `${words[0]} - ${words[words.length - 1]}` : words.join(", ");
}

// The five character cutouts from the design. A person gets the cutout whose keyword is in their name
// (so the same character looks the same in every role); anyone else gets one round-robin.
const ART_KEYS = ["spongebob", "sandy", "krabs", "squidward", "patrick"];

function staffArt(member: StaffMember, index: number): { bg: string; figure: string } {
  const name = member.full_name.toLowerCase();
  const found = ART_KEYS.findIndex((key) => name.includes(key));
  const slot = (found >= 0 ? found : index % ART_KEYS.length) + 1;
  return { bg: `/doctor-${slot}.png`, figure: `/docchar-${slot}.png` };
}

// The detail shown under the role: specialization, the doctor a nurse supports, or the admin duty.
function staffDetail(member: StaffMember): string {
  if (member.role === "doctor") return member.specialization ?? "Clinic Staff";
  if (member.role === "nurse") return member.assigned_doctor_name ? `Supports ${member.assigned_doctor_name}` : "Nursing staff";
  return "Clinic administration";
}

// ---------------- small building blocks ----------------

function SectionHeading({ title, subtitle, eyebrow }: { title: string; subtitle?: string; eyebrow?: string }) {
  return (
    <div className="text-center">
      {eyebrow && (
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-landing-body/80 sm:text-sm">{eyebrow}</p>
      )}
      <h2 className="mt-2 text-3xl font-extrabold text-landing-heading sm:text-4xl lg:text-5xl">{title}</h2>
      {subtitle && <p className="mx-auto mt-3 max-w-2xl text-sm font-medium text-landing-soft sm:text-base">{subtitle}</p>}
    </div>
  );
}

function BentoCard({ title, text, image, tall = false }: { title: string; text: string; image: string; tall?: boolean }) {
  return (
    <article
      className={`group relative flex overflow-hidden rounded-3xl bg-white shadow-[0_18px_40px_rgba(53,88,130,0.12)] ${
        tall ? "min-h-[24rem] lg:min-h-[30rem]" : "min-h-[11rem]"
      }`}
    >
      <img
        src={image}
        alt={title}
        className="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
      />
      {/* Caption band in the style of the Figma card footers. */}
      <div className="relative mt-auto w-full bg-gradient-to-t from-white/95 via-white/85 to-white/0 px-5 pb-4 pt-10">
        <h3 className={`font-bold text-landing-body ${tall ? "text-xl sm:text-2xl" : "text-lg"}`}>{title}</h3>
        <p className="mt-1 text-xs font-medium text-landing-body/90 sm:text-sm">{text}</p>
      </div>
    </article>
  );
}

// The same "Book an appointment" button as the hero (white pill with the calendar icon).
function BookButton({ className = "" }: { className?: string }) {
  return (
    <Link
      to="/book"
      className={`inline-flex items-center gap-3 rounded-2xl bg-white px-5 py-4 shadow-[0_16px_36px_rgba(53,88,130,0.18)] transition-transform hover:-translate-y-0.5 ${className}`}
    >
      {/* calendar icon from the design */}
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden>
        <rect x="3.5" y="5" width="17" height="15" rx="2.5" stroke="#1F3655" strokeWidth="1.8" />
        <path d="M8 3v4M16 3v4M3.5 9.5h17" stroke="#1F3655" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M12 12.5v3.5M10.2 14.2h3.6" stroke="#1F3655" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      <span className="text-sm font-semibold text-landing-heading sm:text-base">Book an appointment</span>
    </Link>
  );
}

function StaffArt({ member, art }: { member: StaffMember; art: { bg: string; figure: string } }) {
  return (
    <div className="relative h-40 w-full overflow-hidden sm:h-44">
      <img src={art.bg} alt="" aria-hidden className="absolute inset-0 h-full w-full object-cover" />
      <img
        src={art.figure}
        alt={member.full_name}
        loading="lazy"
        className="absolute bottom-0 left-1/2 h-[96%] max-w-none -translate-x-1/2 object-contain"
      />
    </div>
  );
}

function StaffCard({ member, art }: { member: StaffMember; art: { bg: string; figure: string } }) {
  // Green "Available" badge only when a doctor works today (1 = Monday).
  const todayIdx = ((new Date().getDay() + 6) % 7) + 1;
  const availableToday = (member.weekdays ?? []).includes(todayIdx);

  return (
    <article className="flex flex-col overflow-hidden rounded-3xl bg-white shadow-[0_18px_40px_rgba(53,88,130,0.14)] transition-shadow hover:shadow-[0_24px_50px_rgba(53,88,130,0.22)]">
      <StaffArt member={member} art={art} />
      <div className="flex flex-1 flex-col px-4 pb-4 pt-3 text-left">
        <h3 className="text-sm font-bold text-landing-ink sm:text-[15px]">{member.full_name}</h3>
        <p className="mt-0.5 text-xs font-medium text-landing-muted">
          {ROLE_LABEL[member.role]} · {staffDetail(member)}
        </p>
        <div className="mt-2.5 flex flex-wrap items-center gap-2">
          <span className={`rounded-md px-2.5 py-1 text-[10px] font-semibold ${ROLE_BADGE[member.role]}`}>
            {ROLE_LABEL[member.role]}
          </span>
          {member.role === "doctor" && (
            <>
              <span className="rounded-md bg-brand-50 px-2.5 py-1 text-[10px] font-semibold text-landing-body">
                {weekdayLabel(member.weekdays)}
              </span>
              <span
                className={`rounded-md px-2.5 py-1 text-[10px] font-semibold ${
                  availableToday ? "bg-green-100 text-landing-leaf" : "bg-amber-100 text-amber-700"
                }`}
              >
                {availableToday ? "Available" : "Off today"}
              </span>
            </>
          )}
        </div>
      </div>
    </article>
  );
}

function StaffSkeletons() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <article key={i} className="animate-pulse overflow-hidden rounded-3xl bg-white shadow-[0_18px_40px_rgba(53,88,130,0.1)]">
          <div className="h-40 w-full bg-brand-100 sm:h-44" />
          <div className="px-4 pb-5 pt-3">
            <div className="h-3.5 w-3/4 rounded bg-brand-100" />
            <div className="mt-2 h-3 w-1/2 rounded bg-brand-100" />
            <div className="mt-4 h-6 rounded-lg bg-brand-100" />
          </div>
        </article>
      ))}
    </>
  );
}

function DeptCard({ department, onOpen }: { department: DepartmentItem; onOpen: (name: string) => void }) {
  return (
    <article className="rounded-3xl bg-white p-5 text-left shadow-[0_14px_30px_rgba(53,88,130,0.1)] transition-shadow hover:shadow-[0_20px_44px_rgba(53,88,130,0.18)]">
      {department.icon ? (
        <img src={department.icon} alt="" aria-hidden className="h-12 w-12 rounded-xl shadow-sm" />
      ) : (
        <span aria-hidden className="grid h-12 w-12 place-items-center rounded-xl bg-brand-100 text-xl font-bold text-brand-700">
          {department.name.charAt(0).toUpperCase()}
        </span>
      )}
      <h3 className="mt-4 text-base font-bold text-[#365983]">{department.name}</h3>
      <p className="mt-1.5 text-[13px] leading-relaxed text-[#759ECA]">{department.description}</p>
      <button
        type="button"
        onClick={() => onOpen(department.name)}
        className="mt-4 inline-flex items-center gap-1 text-[13px] font-semibold text-landing-body hover:gap-2"
      >
        Learn More <span aria-hidden>→</span>
      </button>
    </article>
  );
}

const SOCIALS: { label: string; href: string; icon: string }[] = [
  {
    label: "Facebook",
    href: "https://www.facebook.com",
    icon: "M13.5 9H15V6.5h-1.5c-1.93 0-3.5 1.57-3.5 3.5v1.5H8V14h2v7.5h2.5V14h2l.5-2.5h-2.5V10c0-.55.45-1 1-1Z",
  },
  {
    label: "X (Twitter)",
    href: "https://x.com",
    icon: "M6 6l5.12 6.44L6.35 18h2.2l3.55-4.16L15.6 18H18l-5.35-6.72L17.29 6h-2.2l-3.22 3.83L8.4 6H6Z",
  },
  {
    label: "LinkedIn",
    href: "https://www.linkedin.com",
    icon: "M7.5 9H9.5V18H7.5V9ZM8.5 6.25A1.25 1.25 0 1 1 8.5 8.75 1.25 1.25 0 0 1 8.5 6.25ZM11.5 9h1.92v1.23h.03c.27-.5 1.03-1.32 2.35-1.32 2.51 0 2.98 1.65 2.98 3.8V18h-2v-4.62c0-1.1-.02-2.52-1.54-2.52-1.54 0-1.74 1.2-1.74 2.44V18h-2V9Z",
  },
  {
    label: "YouTube",
    href: "https://www.youtube.com",
    icon: "M18.63 7.68c.37 1.38.37 4.27 0 5.65a2.06 2.06 0 0 1-1.45 1.45c-1.38.37-6.43.37-7.81 0a2.06 2.06 0 0 1-1.45-1.45c-.37-1.38-.37-4.27 0-5.65A2.06 2.06 0 0 1 9.37 6.2c1.38-.37 6.43-.37 7.81 0 .7.19 1.26.75 1.45 1.48ZM11 13.2 14.5 11 11 8.8v4.4Z",
  },
];

function FooterColumn({ title, links }: { title: string; links: { label: string; to: string }[] }) {
  return (
    <div>
      <h3 className="text-base font-bold text-[#527BA9]">{title}</h3>
      <ul className="mt-3 space-y-2">
        {links.map((l) => (
          <li key={l.label} className="text-sm text-landing-faint transition-colors hover:text-landing-body">
            {l.to.startsWith("/") ? <Link to={l.to}>{l.label}</Link> : <a href={l.to}>{l.label}</a>}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------- page ----------------

export default function LandingPage() {
  const { user } = useAuth();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [staff, setStaff] = useState<StaffMember[] | null>(null);
  const [staffError, setStaffError] = useState("");
  const [departments, setDepartments] = useState<DepartmentItem[] | null>(null);
  // null = popup closed; a string = open, with that text pre-filled in the search box.
  const [popupQuery, setPopupQuery] = useState<string | null>(null);

  // Clinic name and address for the footer. A failure here is not shown; the page uses defaults.
  useEffect(() => {
    publicApi
      .catalog()
      .then(setCatalog)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    staffDirectoryApi
      .list()
      .then(setStaff)
      .catch((e) => setStaffError(e instanceof Error ? e.message : "Could not load the staff."));
  }, []);

  useEffect(() => {
    departmentApi
      .list()
      .then(setDepartments)
      .catch(() => setDepartments([])); // an empty list makes the page use the built-in featured six
  }, []);

  const allDepartments = departments && departments.length > 0 ? departments : FALLBACK_DEPARTMENTS;
  const featured = useMemo(() => {
    const picked = allDepartments.filter((d) => d.is_featured).slice(0, 6);
    return picked.length > 0 ? picked : allDepartments.slice(0, 6);
  }, [allDepartments]);
  const total = allDepartments.length;
  const viewAllLabel = `View All ${total >= 25 ? "25+" : total} Departments`;

  const address = catalog?.clinic_address?.trim() || DEFAULT_ADDRESS;
  const clinicName = catalog?.clinic_name?.trim() || "AppointMed";

  return (
    <div style={pageFont} className="relative bg-landing-pagebg text-landing-body">
      {/* ---------------- navbar (floating pill) ---------------- */}
      <header className="absolute inset-x-0 top-0 z-30 px-4 pt-4 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 rounded-2xl bg-white/85 px-4 py-2.5 shadow-[0_10px_30px_rgba(53,88,130,0.12)] backdrop-blur">
          <span className="inline-flex items-center gap-2">
            <img src="/logo-mark.png" alt="" aria-hidden style={{ height: 40, width: "auto" }} />
            <span className="text-lg font-semibold text-brand-700">AppointMed</span>
          </span>
          <nav className="flex items-center gap-1 text-sm" aria-label="Site">
            <a href="#services" className="hidden rounded-lg px-3 py-1.5 font-medium text-landing-body hover:bg-brand-50 sm:inline-block">
              Services
            </a>
            <a href="#about" className="hidden rounded-lg px-3 py-1.5 font-medium text-landing-body hover:bg-brand-50 sm:inline-block">
              About
            </a>
            <a href="#staff" className="hidden rounded-lg px-3 py-1.5 font-medium text-landing-body hover:bg-brand-50 sm:inline-block">
              Staff
            </a>
            <a href="#departments" className="hidden rounded-lg px-3 py-1.5 font-medium text-landing-body hover:bg-brand-50 md:inline-block">
              Departments
            </a>
          </nav>
          {user ? (
            <Link
              to={`/${user.role}`}
              className="rounded-xl border border-brand-200 px-4 py-1.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
            >
              Dashboard
            </Link>
          ) : (
            <Link
              to="/staff-login"
              className="rounded-xl border border-brand-200 px-4 py-1.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
            >
              Staff login
            </Link>
          )}
        </div>
      </header>

      {/* ---------------- hero ---------------- */}
      <section id="top" className="relative overflow-hidden bg-landing-pagebg">
        <img
          src="/hero-building.png"
          alt=""
          aria-hidden
          className="absolute right-0 top-0 hidden h-full w-[62%] object-cover sm:block"
          style={{
            maskImage: "linear-gradient(to right, transparent 0%, black 55%)",
            WebkitMaskImage: "linear-gradient(to right, transparent 0%, black 55%)",
          }}
        />
        {/* soft white wash so text stays readable over the photo */}
        <div className="absolute inset-0 bg-gradient-to-r from-landing-pagebg via-landing-pagebg/85 to-transparent" aria-hidden />
        <div className="relative mx-auto w-full max-w-7xl px-6 pb-16 pt-32 sm:pt-36 lg:pt-40">
          <h1 className="max-w-2xl text-4xl font-extrabold leading-tight text-landing-heading sm:text-6xl lg:text-7xl">
            Booked in a click!
          </h1>
          <p className="mt-5 max-w-xl text-base font-medium text-landing-body sm:text-lg">
            Enjoy effortless scheduling on your own timeline. Simply choose your doctor and a convenient time; our clinical
            team will confirm your details so your room is fully prepared upon your arrival.
          </p>
          <BookButton className="mt-8" />
        </div>
      </section>

      {/* ---------------- about us ---------------- */}
      <section id="about" className="bg-gradient-to-b from-[#8FC1EC] to-[#EAF5FD] px-6 py-14 sm:py-16">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-3xl font-extrabold text-landing-heading sm:text-5xl">About us</h2>
          <p className="mt-3 text-xl font-bold text-landing-body sm:text-2xl">Your Partner in Health and Wellness</p>
          <p className="mt-5 text-sm font-normal leading-relaxed text-landing-body sm:text-base">{ABOUT_LEAD}</p>
          <p className="mt-4 text-sm font-normal leading-relaxed text-landing-body sm:text-base">{ABOUT_SECOND}</p>
        </div>
      </section>

      {/* ---------------- services bento ---------------- */}
      <section id="services" className="landing-section-swirl relative px-6 py-14">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-5 lg:grid-cols-2">
            <BentoCard title={SERVICES[0].title} text={SERVICES[0].text} image={SERVICES[0].image} tall />
            <div className="grid gap-5">
              <BentoCard title={SERVICES[1].title} text={SERVICES[1].text} image={SERVICES[1].image} />
              <div className="grid gap-5 sm:grid-cols-2">
                <BentoCard title={SERVICES[2].title} text={SERVICES[2].text} image={SERVICES[2].image} />
                <BentoCard title={SERVICES[3].title} text={SERVICES[3].text} image={SERVICES[3].image} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- meet our staff ---------------- */}
      <section id="staff" className="bg-[#F4F9FE] px-6 pb-16 pt-10">
        <div className="mx-auto max-w-7xl">
          {/* The heading sits in a white tab, as in the design. */}
          <div className="inline-block rounded-br-3xl bg-white px-8 py-4 shadow-[0_14px_30px_rgba(53,88,130,0.1)]">
            <h2 className="text-2xl font-extrabold text-landing-heading sm:text-3xl">Meet Our Staff</h2>
          </div>
          {staffError ? (
            <div className="mt-8 rounded-2xl bg-white p-6 text-center shadow-sm">
              <p className="text-sm font-medium text-landing-body">{staffError}</p>
            </div>
          ) : (
            <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {staff ? (
                staff.length ? (
                  staff.map((m, i) => <StaffCard key={m.id} member={m} art={staffArt(m, i)} />)
                ) : (
                  <p className="col-span-full rounded-2xl bg-white p-6 text-center text-sm text-landing-muted shadow-sm">
                    No staff are currently listed.
                  </p>
                )
              ) : (
                <StaffSkeletons />
              )}
            </div>
          )}

          {/* One booking button for the whole list, below the last card. */}
          <div className="mt-10 flex justify-center">
            <BookButton />
          </div>
        </div>
      </section>

      {/* ---------------- clinical departments ---------------- */}
      <section id="departments" className="bg-gradient-to-b from-[#F4F9FE] to-[#EAF4FC] px-6 pb-20 pt-12">
        <div className="mx-auto max-w-6xl">
          <SectionHeading
            eyebrow="Clinical Departments"
            title="Our Specialties & Departments"
            subtitle="World-class clinical care delivered by specialists across all major medical disciplines."
          />
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {featured.map((d) => (
              <DeptCard key={d.id} department={d} onOpen={(name) => setPopupQuery(name)} />
            ))}
          </div>
          <div className="mt-10 flex justify-center">
            <button
              type="button"
              onClick={() => setPopupQuery("")}
              aria-haspopup="dialog"
              className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-landing-body shadow-[0_10px_24px_rgba(53,88,130,0.12)] transition-transform hover:-translate-y-0.5"
            >
              {viewAllLabel}
            </button>
          </div>
        </div>
      </section>

      {/* ---------------- footer ---------------- */}
      <footer id="contact" className="landing-section-swirl relative">
        <div className="absolute inset-0 bg-white/45" aria-hidden />
        <div className="relative mx-auto max-w-6xl px-6 pb-8 pt-14">
          <div className="grid gap-10 lg:grid-cols-[1.3fr_2fr]">
            <div>
              <img src="/footer-logo.png" alt="AppointMed" className="h-28 w-auto" />
              <p className="mt-3 max-w-xs text-sm leading-relaxed text-landing-faint">
                AppointMed is your trusted partner for clinical appointment booking. Connecting patients with certified
                specialists for world-class healthcare.
              </p>
              <div className="mt-4 flex gap-3">
                {SOCIALS.map((s) => (
                  <a
                    key={s.label}
                    href={s.href}
                    aria-label={s.label}
                    target="_blank"
                    rel="noreferrer"
                    className="flex h-9 w-9 items-center justify-center rounded-lg bg-landing-navy transition-transform hover:-translate-y-0.5"
                  >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="white" aria-hidden>
                      <path d={s.icon} />
                    </svg>
                  </a>
                ))}
              </div>
            </div>

            <div className="grid gap-8 sm:grid-cols-3">
              <FooterColumn
                title="Quick Links"
                links={[
                  { label: "Home", to: "#top" },
                  { label: "About Us", to: "#about" },
                  { label: "Our Staff", to: "#staff" },
                  { label: "Departments", to: "#departments" },
                  { label: "Contact Us", to: "#contact" },
                ]}
              />
              <FooterColumn
                title="Services"
                links={[
                  { label: "Book Appointment", to: "/book" },
                  { label: "Emergency Care", to: "#services" },
                  { label: "Lab & Diagnostics", to: "#services" },
                  { label: "Health Checkups", to: "#services" },
                  { label: "Telemedicine", to: "#services" },
                  { label: "Medical Records", to: "#services" },
                ]}
              />
              <div className="text-left">
                <h3 className="text-base font-bold text-[#527BA9]">Contact Us</h3>
                <ul className="mt-3 space-y-3 text-sm text-[#94A3B8]">
                  <li className="flex items-start gap-2">
                    <ContactIcon kind="pin" />
                    <span>{address}</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ContactIcon kind="phone" />
                    <a href="tel:+12345678900" className="transition-colors hover:text-landing-body">+1 (234) 567-8900</a>
                  </li>
                  <li className="flex items-center gap-2">
                    <ContactIcon kind="mail" />
                    <a href="mailto:info@appointmed.com" className="transition-colors hover:text-landing-body">info@appointmed.com</a>
                  </li>
                  <li className="flex items-center gap-2">
                    <ContactIcon kind="clock" />
                    <span>Mon - Sat: 8:00 AM – 8:00 PM</span>
                  </li>
                </ul>
              </div>
            </div>  
          </div>

          <div className="mt-10 border-t border-[#B9D3EA] pt-4">
            <p className="text-xs font-medium text-landing-faint">
              © 2026 {clinicName}. All rights reserved.&nbsp;|&nbsp;Privacy Policy&nbsp;|&nbsp;Terms of Service
            </p>
          </div>
        </div>
      </footer>

      {/* ---------------- departments popup ---------------- */}
      {popupQuery !== null && (
        <DepartmentsModal departments={allDepartments} initialQuery={popupQuery} onClose={() => setPopupQuery(null)} />
      )}
    </div>
  );
}