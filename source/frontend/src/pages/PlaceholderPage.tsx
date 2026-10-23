import type { NavItem } from "../types";

// Stand-in for every dashboard page. Replace one at a time with a real page in src/pages/<role>/.
export default function PlaceholderPage({ item }: { item: NavItem }) {
  return (
    <section>
      <h1 className="text-2xl font-semibold">{item.label}</h1>
      <p className="mt-1 max-w-prose text-slate-600">{item.description}</p>
      <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-white p-8 text-slate-500">
        This page is not built yet.
      </div>
    </section>
  );
}