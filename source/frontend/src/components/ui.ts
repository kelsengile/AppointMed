// Shared class names and the status-to-colour mapping, so every page looks the same.
// The look follows the landing page: rounded corners, soft blue shadows, navy gradient buttons.
export type Tone = "green" | "amber" | "red" | "blue" | "slate";

export const inputClass =
  "w-full rounded-xl border border-[#BBD4F3] bg-white px-3 py-2 text-sm text-landing-heading placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30";
export const primaryButton =
  "book-btn rounded-xl px-4 py-2 text-sm font-semibold text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:opacity-60";
export const secondaryButton =
  "rounded-xl border border-[#BBD4F3] bg-white px-4 py-2 text-sm font-medium text-landing-body hover:bg-brand-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-60";
export const dangerButton =
  "rounded-xl border border-red-300 bg-white px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:opacity-60";
export const cardClass = "rounded-3xl border border-[#DCE9FB] bg-white p-4 shadow-[0_14px_30px_rgba(53,88,130,0.1)]";

/** Badge colour for any status word used in the app. */
export function statusTone(status: string): Tone {
  switch (status) {
    case "Completed":
    case "Paid":
    case "Available":
    case "Converted":
    case "Active":
      return "green";
    case "Pending":
    case "Unpaid":
    case "Checked-in":
    case "Occupied":
    case "Examined":
      return "amber";
    case "Consulting":
    case "Scheduled":
      return "blue";
    case "Cancelled":
    case "Dismissed":
    case "Maintenance":
    case "Inactive":
      return "red";
    default:
      return "slate";
  }
} 