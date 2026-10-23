import { useState } from "react";
import { Link } from "react-router-dom";
import LoginModal from "../components/LoginModal";

const SERVICES = [
  { name: "General Medicine", text: "Checkups, illness, and long-term condition care for adults." },
  { name: "Pediatrics", text: "Vaccinations, growth checks, and care for children." },
  { name: "Prescriptions", text: "Receive a written prescription at the end of your visit." },
];

const DOCTORS = [
  { name: "Dr. Sandy Cheeks", field: "General Medicine", days: "Monday to Friday" },
  { name: "Dr. Squidward Tentacles", field: "Pediatrics", days: "Monday, Wednesday, Friday" },
];

export default function LandingPage() {
  const [loginOpen, setLoginOpen] = useState(false);
  const navLink = "rounded px-2 py-1 hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-white";

  return (
    <div>
      <header className="absolute inset-x-0 top-0 z-10 text-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-4">
          <a href="#top" className="text-xl font-semibold">AppointMed</a>
          <nav className="flex flex-wrap items-center gap-1 text-sm" aria-label="Site">
            <a href="#services" className={navLink}>Services</a>
            <a href="#doctors" className={navLink}>Doctors</a>
            <a href="#contact" className={navLink}>Contact</a>
            <Link to="/book" className="ml-2 rounded-lg bg-white px-3 py-1.5 font-medium text-brand-700 hover:bg-brand-50">
              Book appointment
            </Link>
            <button
              type="button"
              onClick={() => setLoginOpen(true)}
              className="rounded-lg border border-white/70 px-3 py-1.5 font-medium hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              Staff login
            </button>
          </nav>
        </div>
      </header>

      {/* Hero background: put your photo at frontend/public/hero.jpg. The gradient shows until then. */}
      <section
        id="top"
        className="relative grid min-h-[34rem] items-end bg-brand-700 bg-cover bg-center px-6 pb-16 pt-32 text-white"
        style={{
          backgroundImage:
            "linear-gradient(to top, rgba(18,48,47,.85), rgba(18,48,47,.35)), url('/hero.jpg'), linear-gradient(135deg, #0d6459, #14917f)",
        }}
      >
        <div className="mx-auto w-full max-w-6xl">
          <h1 className="max-w-2xl text-4xl font-semibold leading-tight md:text-5xl">Book your clinic visit without the phone call.</h1>
          <p className="mt-4 max-w-xl text-lg text-white/90">Pick a doctor and a time. Our nurses confirm it, so you walk in to a ready room.</p>
          <Link to="/book" className="mt-6 inline-block rounded-lg bg-white px-5 py-3 font-medium text-brand-700 hover:bg-brand-50">
            Book an appointment
          </Link>
        </div>
      </section>

      <section id="services" className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-2xl font-semibold">Services</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {SERVICES.map((s) => (
            <article key={s.name} className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold">{s.name}</h3>
              <p className="mt-1 text-sm text-slate-600">{s.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="doctors" className="bg-brand-50 px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-2xl font-semibold">Our doctors</h2>
          <ul className="mt-6 grid gap-4 md:grid-cols-2">
            {DOCTORS.map((d) => (
              <li key={d.name} className="rounded-xl border border-brand-100 bg-white p-5">
                <p className="font-semibold">{d.name}</p>
                <p className="text-sm text-slate-600">{d.field}</p>
                <p className="mt-1 text-sm text-slate-500">{d.days}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <footer id="contact" className="mx-auto max-w-6xl px-6 py-10 text-sm text-slate-600">
        <p className="font-semibold text-brand-900">AppointMed Bikini Bottom Clinic</p>
        <p>124 Conch Street, Bikini Bottom (fictional sample data)</p>
      </footer>

      {loginOpen && <LoginModal onClose={() => setLoginOpen(false)} />}
    </div>
  );
}