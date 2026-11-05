// A number with a label. Becomes a link when `to` is given.
import { Link } from "react-router-dom";

export default function StatCard({ label, value, hint, to }: { label: string; value: string | number; hint?: string; to?: string }) {
  const body = (
    <>
      <p className="text-sm font-medium text-landing-muted">{label}</p>
      <p className="mt-1 text-3xl font-extrabold text-landing-heading">{value}</p>
      {hint && <p className="mt-1 text-xs text-landing-soft">{hint}</p>}
    </>
  );
  const base = "block rounded-3xl border border-[#DCE9FB] bg-white p-5 shadow-[0_14px_30px_rgba(53,88,130,0.1)]";
  if (!to) return <div className={base}>{body}</div>;
  return (
    <Link
      to={to}
      className={`${base} transition-shadow hover:border-brand-500 hover:shadow-[0_20px_44px_rgba(53,88,130,0.18)] focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500`}
    >
      {body}
    </Link>
  );
}