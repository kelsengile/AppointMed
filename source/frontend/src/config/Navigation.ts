import type { NavItem, Role } from "../types";

// One list per role. Add a page here and it appears in the side panel and the router.
const settingsAndHelp: NavItem[] = [
  { path: "settings", label: "Settings", description: "Change your password and preferences.", bottom: true },
  { path: "help", label: "Help", description: "Guides and answers for using AppointMed.", bottom: true },
];

const doctor: NavItem[] = [
  { path: "dashboard", label: "Dashboard", description: "Today's queue and a summary of your day." },
  { path: "profile", label: "Profile", description: "Your name, specialization, and photo." },
  { path: "appointments", label: "Appointments", description: "Your scheduled, checked-in, and consulting appointments." },
  { path: "examination", label: "Examination", description: "Examine the current patient, then schedule a follow-up or send to history." },
  { path: "patients", label: "Patients", description: "Search and open patient records." },
  { path: "prescriptions", label: "Prescriptions", description: "Write and review prescriptions." },
  { path: "schedule", label: "My Schedule", description: "Your weekly working hours." },
  { path: "doctors", label: "Doctors", description: "Directory of clinic doctors." },
  { path: "rooms", label: "Rooms", description: "Room availability board." },
  { path: "invoice", label: "Invoice", description: "Invoices for your sessions (view only)." },
  { path: "history", label: "History", description: "Completed encounters." },
  { path: "notifications", label: "Notifications", description: "Appointment requests routed to you." },
  ...settingsAndHelp,
];

const nurse: NavItem[] = [
  { path: "dashboard", label: "Dashboard", description: "Pending requests, today's queue, and unbilled sessions." },
  { path: "profile", label: "Profile", description: "Your name, assigned doctor, and photo." },
  { path: "notifications", label: "Notifications", description: "Convert appointment requests to appointments, or dismiss them." },
  { path: "appointments", label: "Appointments", description: "All appointments for your doctor." },
  { path: "new-appointment", label: "New Appointment", description: "Create a walk-in appointment." },
  { path: "check-in", label: "Check-in Queue", description: "Check patients in and assign rooms." },
  { path: "patients", label: "Patients", description: "Search and open patient records." },
  { path: "doctors", label: "Doctors", description: "Directory of clinic doctors." },
  { path: "rooms", label: "Rooms", description: "Update room status." },
  { path: "invoice", label: "Invoice", description: "Bill finished sessions and mark invoices paid." },
  { path: "history", label: "History", description: "Completed encounters." },
  ...settingsAndHelp,
];

const admin: NavItem[] = [
  { path: "dashboard", label: "Dashboard", description: "Clinic-wide totals and recent activity." },
  { path: "users", label: "Users", description: "Create, edit, and deactivate doctors, nurses, and admins." },
  { path: "doctor-schedules", label: "Doctor Schedules", description: "Set weekly working hours and slot length." },
  { path: "rooms", label: "Rooms", description: "Add, rename, and change room status." },
  { path: "clinic-settings", label: "Clinic Settings", description: "Clinic name, fee, and online booking switch." },
  { path: "reports", label: "Reports", description: "Appointments and billing summaries." },
  { path: "audit-logs", label: "Audit Logs", description: "Who did what, and when." },
  { path: "profile", label: "Profile", description: "Your admin account." },
  ...settingsAndHelp,
];

export const NAV: Record<Role, NavItem[]> = { doctor, nurse, admin };