import type { NavItem, Role } from "../types";

// One list per role. Add a page here and it appears in the side panel and the router.
// - Items with a `group` are listed under that header, in the order written here.
// - Items with a `pin` go to a fixed spot (profile = top, settings and help = bottom).
// The first item must be the Dashboard, because /<role> redirects to it.
const pinned: NavItem[] = [
  { path: "profile", label: "Profile", description: "Your name, role, and photo.", pin: "profile" },
  { path: "settings", label: "Settings", description: "Change your password and preferences.", pin: "settings" },
  { path: "help", label: "Help", description: "Guides and answers for using AppointMed.", pin: "help" },
];

const doctor: NavItem[] = [
  { path: "dashboard", label: "Dashboard", description: "Today's queue and a summary of your day.", group: "Overview" },
  { path: "appointments", label: "Appointments", description: "Your exam room, waiting queue, and today's agenda.", group: "Consultations" },
  { path: "notifications", label: "Notifications", description: "Appointment requests routed to you.", group: "Consultations" },
  { path: "patients", label: "Patients", description: "Search and open patient records.", group: "Records" },
  { path: "history", label: "History", description: "Completed encounters.", group: "Records" },
  { path: "invoice", label: "Invoice", description: "Invoices for your sessions. Mark them paid when the patient pays.", group: "Records" },
  { path: "prescriptions", label: "Prescriptions", description: "Prescriptions are written during an examination (Appointments) and listed in History.", group: "Records" },
  ...pinned,
];

const nurse: NavItem[] = [
  { path: "dashboard", label: "Dashboard", description: "Pending requests, today's queue, and unbilled sessions.", group: "Overview" },
  { path: "appointments", label: "Appointments", description: "Check patients in and manage your doctor's agenda.", group: "Consultations" },
  { path: "notifications", label: "Notifications", description: "Approve appointment requests or disapprove them.", group: "Consultations" },
  { path: "patients", label: "Patients", description: "Search and open patient records.", group: "Records" },
  { path: "history", label: "History", description: "Completed encounters.", group: "Records" },
  { path: "invoice", label: "Invoice", description: "Collect payment for finished sessions and mark invoices paid.", group: "Records" },
  ...pinned,
];

const admin: NavItem[] = [
  { path: "dashboard", label: "Dashboard", description: "Clinic-wide totals and recent activity.", group: "Overview" },
  { path: "Users", label: "Users", description: "Create, edit, and deactivate doctors, nurses, and admins.", group: "Management" },
  { path: "Rooms", label: "Rooms", description: "Add, rename, and change room status.", group: "Management" },
  { path: "clinic", label: "Clinic Settings", description: "Clinic name, fee, and online booking switch.", group: "System" },
  { path: "Reports", label: "Reports", description: "Appointments and billing summaries.", group: "System" },
  { path: "Audits", label: "Audit Logs", description: "Who did what, and when.", group: "System" },
  ...pinned,
];

export const NAV: Record<Role, NavItem[]> = { doctor, nurse, admin };