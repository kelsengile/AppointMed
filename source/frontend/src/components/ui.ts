// Shared class names and the status-to-colour mapping, so every page looks the same.
export type Tone = "green" | "amber" | "red" | "blue" | "slate";

export const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30";
export const primaryButton =
  "rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:opacity-60";
export const secondaryButton =
  "rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-60";
export const dangerButton =
  "rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:opacity-60";
export const cardClass = "rounded-xl border border-slate-200 bg-white p-4";

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