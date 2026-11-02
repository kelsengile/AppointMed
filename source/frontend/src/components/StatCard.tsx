// A number with a label. Becomes a link when `to` is given.
import { Link } from "react-router-dom";

export default function StatCard({ label, value, hint, to }: { label: string; value: string | number; hint?: string; to?: string }) {
  const body = (
    <>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-brand-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </>
  );
  const base = "block rounded-xl border border-slate-200 bg-white p-4";
  if (!to) return <div className={base}>{body}</div>;
  return (
    <Link to={to} className={`${base} hover:border-brand-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500`}>
      {body}
    </Link>
  );
}