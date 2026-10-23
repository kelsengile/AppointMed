// A coloured message box for errors, confirmations and hints.
import type { ReactNode } from "react";

const STYLES = {
  error: "bg-red-50 text-red-800",
  success: "bg-emerald-50 text-emerald-800",
  info: "bg-sky-50 text-sky-900",
  warning: "bg-amber-50 text-amber-900",
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
    <div role={kind === "error" ? "alert" : "status"} className={`mt-4 flex items-start justify-between gap-3 rounded-lg p-3 text-sm ${STYLES[kind]}`}>
      <span>{children}</span>
      {onClose && (
        <button type="button" onClick={onClose} className="shrink-0 rounded px-2 py-0.5 hover:bg-black/5">
          Dismiss
        </button>
      )}
    </div>
  );
}