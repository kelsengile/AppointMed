// A dialog over the page. Closes with Escape, the Close button, or a click on the dark background.
import { useEffect, type ReactNode } from "react";

export default function Modal({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-[#1F3655]/50 p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
        className={`my-8 w-full ${wide ? "max-w-3xl" : "max-w-md"} rounded-3xl border border-white/70 bg-white p-6 shadow-[0_24px_60px_rgba(31,54,85,0.3)]`}
      >
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-xl font-extrabold text-landing-heading">{title}</h2>
          <button type="button" onClick={onClose} className="rounded-xl px-3 py-1 text-sm font-medium text-landing-body hover:bg-brand-50">
            Close
          </button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}