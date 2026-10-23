import { Link } from "react-router-dom";
import Logo from "../components/Logo";

// Public booking page. Will write to `notifications` through the backend (origin = Website).
export default function BookingPage() {
  return (
    <main className="mx-auto max-w-xl p-6 md:p-10">
      <Link to="/" aria-label="Back to AppointMed home">
        <Logo size={36} />
      </Link>
      <h1 className="mt-6 text-2xl font-semibold">Book an appointment</h1>
      <p className="mt-1 text-slate-600">Choose a doctor and a time. A nurse will confirm your request.</p>
      <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-white p-8 text-slate-500">
        The booking form is not built yet.
      </div>
    </main>
  );
}