// A coloured message box for errors, confirmations and hints.
import type { ReactNode } from "react";

const STYLES = {
  error: "border-red-200 bg-red-50 text-red-800",
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  info: "border-[#BBD4F3] bg-brand-50 text-landing-body",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
} as const;

export default function Alert({
  kind = "info",
  children,
  onClose,
}: {
  kind?: keyof typeof STYLES;
  children: ReactNode;
  onClose?: () => void;
}) {
  return (
    <div
      role={kind === "error" ? "alert" : "status"}
      className={`mt-4 flex items-start justify-between gap-3 rounded-2xl border p-3 text-sm shadow-[0_8px_20px_rgba(53,88,130,0.08)] ${STYLES[kind]}`}
    >
      <span>{children}</span>
      {onClose && (
        <button type="button" onClick={onClose} className="shrink-0 rounded-lg px-2 py-0.5 hover:bg-black/5">
          Dismiss
        </button>
      )}
    </div>
  );
}