// Shared TypeScript types. Field names match the backend JSON exactly.

export type Role = "doctor" | "nurse" | "admin";
export const ROLES: Role[] = ["doctor", "nurse", "admin"];

/** MySQL DECIMAL values arrive as text ("500.00"). Use toNumber() from utils/format before doing arithmetic. */
export type Money = number | string;

export interface SessionUser {
  username: string;
  fullName: string;
  role: Role;
  avatar?: string | null; // data URL, kept in memory only
}

export interface NavItem {
  path: string; // relative to /<role>/
  label: string;
  description: string; // shown on the placeholder page
  group?: string; // header shown above this item in the side panel
  pin?: "profile" | "settings" | "help"; // items pinned to a fixed spot instead of a group
}

// ---------- auth, profile ----------

export interface LoginResponse {
  access_token: string;
  user: { id: number; username: string; full_name: string; role: Role };
}

export interface UserRecord {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  email: string | null;
  specialization: string | null;
  assigned_doctor_id: number | null;
  assigned_doctor_name: string | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface Profile extends UserRecord {
  avatar: string | null;
}

// ---------- public booking ----------

export interface DoctorOption {
  id: number;
  full_name: string;
  specialization: string | null;
  weekdays: number[]; // 1 = Monday ... 7 = Sunday
}

export interface Catalog {
  clinic_name: string;
  clinic_address: string;
  booking_open: boolean;
  window_days: number;
  doctors: DoctorOption[];
}

export type Sex = "Male" | "Female" | "Other";

export interface BookingPayload {
  full_name: string;
  birthdate: string;
  sex: Sex;
  contact_number: string;
  email: string;
  address: string;
  doctor_id: number;
  preferred_datetime: string;
  reason: string;
}

export interface BookingReceipt {
  id: number;
  doctor_name: string;
  preferred_datetime: string;
  email: string;
}

// ---------- notifications, appointments, rooms ----------

export type RequestStatus = "Pending" | "Converted" | "Dismissed";

export interface NotificationItem {
  id: number;
  doctor_id: number;
  requester_name: string;
  contact_number: string | null;
  email: string | null;
  birthdate: string | null;
  sex: Sex | null;
  address: string | null;
  preferred_datetime: string | null;
  reason: string | null;
  origin: string;
  status: RequestStatus;
  decision_note: string | null;
  created_at: string;
  resolved_at: string | null;
  slot_taken: boolean; // the wanted time is already booked
}

export type AppointmentStatus = "Scheduled" | "Checked-in" | "Consulting" | "Examined" | "Completed" | "Cancelled";

export interface AppointmentItem {
  id: number;
  notification_id: number | null;
  patient_id: number | null;
  full_name: string;
  doctor_id: number;
  doctor_name: string;
  nurse_id: number | null;
  room_id: number | null;
  room_name: string | null;
  source: string;
  scheduled_time: string;
  reason: string | null;
  status: AppointmentStatus;
  checked_in_at: string | null;
  birthdate: string | null;
  sex: Sex | null;
  contact_number: string | null;
  invoice_id: number | null;
  consultation_fee: Money | null;
  invoice_amount: Money | null;
  invoice_status: string | null;
}

export interface AppointmentCreatePayload {
  patient_id?: number | null;
  full_name?: string | null;
  birthdate?: string | null;
  sex?: Sex | null;
  contact_number?: string | null;
  scheduled_time?: string | null;
  reason?: string | null;
  check_in_now: boolean;
}

export interface DayOff {
  day: string; // YYYY-MM-DD
  reason: string | null;
}

export interface CalendarData {
  working_weekdays: number[]; // 1 = Monday ... 7 = Sunday
  busy_days: string[]; // YYYY-MM-DD
  off_days: DayOff[]; // days the doctor marked as unavailable
}

export interface BookingCalendarData {
  working_weekdays: number[]; // 1 = Monday ... 7 = Sunday
  full_days: string[]; // YYYY-MM-DD, working days with no open time left
  off_days: string[]; // YYYY-MM-DD, days the doctor is unavailable
}


export type RoomStatus = "Available" | "Occupied" | "Maintenance";

export interface RoomItem {
  id: number;
  room_name: string;
  status: RoomStatus;
  updated_at: string;
  updated_by_name: string | null;
  occupant: string | null;
}

export interface StaffDashboard {
  today: Record<AppointmentStatus, number>;
  pending_notifications: number;
  unbilled: number;
  awaiting_payment: number;
  queue: Array<AppointmentItem & { queue_position: number }>;
  consulting: AppointmentItem | null;
  upcoming: AppointmentItem[];
}

// ---------- examination, prescriptions, invoices ----------

export interface PrescriptionLine {
  id: number;
  medicine_name: string;
  dosage: string | null;
  quantity: number;
  unit_price: Money;
  instructions: string | null;
}

export interface ExamPayload {
  diagnosis: string;
  notes: string | null;
  prescription_notes: string | null;
  consultation_fee: number;
  follow_up_time: string | null;
  items: {
    medicine_name: string;
    dosage: string | null;
    quantity: number;
    unit_price: number;
    instructions: string | null;
  }[];
}

export interface InvoiceItem {
  id: number;
  appointment_id: number;
  patient_id: number;
  patient_name: string;
  scheduled_time: string;
  appointment_status: AppointmentStatus;
  consultation_fee: Money;
  medicines_total: Money;
  amount: Money;
  status: "Unpaid" | "Paid" | "Cancelled";
  issued_at: string;
  paid_at: string | null;
  items: PrescriptionLine[];
}

export interface Encounter {
  appointment_id: number;
  patient_id: number | null;
  full_name: string;
  scheduled_time: string;
  reason: string | null;
  diagnosis: string | null;
  notes: string | null;
  examined_at: string | null;
  invoice_id: number | null;
  consultation_fee: Money | null;
  medicines_total: Money | null;
  amount: Money | null;
  paid_at: string | null;
  items: PrescriptionLine[];
}

export interface PrescriptionRecord {
  id: number;
  issued_at: string;
  notes: string | null;
  patient_id: number;
  patient_name: string;
  diagnosis: string | null;
  appointment_id: number;
  items: PrescriptionLine[];
}

// ---------- patients ----------

export interface PatientItem {
  id: number;
  full_name: string;
  birthdate: string | null;
  sex: Sex | null;
  contact_number: string | null;
  email: string | null;
  address: string | null;
  condition_summary: string | null;
  visit_count: number;
}

export interface PatientPayload {
  full_name: string;
  birthdate: string | null;
  sex: Sex | null;
  contact_number: string | null;
  email: string | null;
  address: string | null;
  condition_summary: string | null;
}

// ---------- admin ----------

export interface DoctorRef {
  id: number;
  full_name: string;
}

export interface UserCreatePayload {
  username: string;
  password: string;
  full_name: string;
  role: Role;
  email: string | null;
  specialization: string | null;
  assigned_doctor_id: number | null;
}

export interface UserUpdatePayload {
  full_name: string;
  email: string | null;
  specialization: string | null;
  assigned_doctor_id: number | null;
}

export interface ScheduleBlock {
  weekday: number; // 1 = Monday ... 7 = Sunday
  start_time: string; // HH:MM
  end_time: string; // HH:MM
  slot_minutes: number;
}

export interface SettingRow {
  setting_key: string;
  setting_value: string;
  description: string | null;
  updated_at: string;
}

export interface AuditRow {
  id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  entity: string | null;
  entity_id: number | null;
  details: string | null;
  created_at: string;
}

export interface AuditPage {
  total: number;
  items: AuditRow[];
  actions: string[];
}

export interface AdminDashboard {
  users: Record<Role, number>;
  patients: number;
  appointments_today: number;
  pending_requests: number;
  revenue_paid_month: number;
  unpaid_total: number;
  recent_activity: AuditRow[];
}

export interface ReportData {
  date_from: string;
  date_to: string;
  status_counts: { status: string; count: Money }[];
  per_doctor: {
    doctor_id: number;
    doctor_name: string;
    appointments: Money;
    completed: Money;
    cancelled: Money;
    revenue_paid: Money;
    revenue_unpaid: Money;
  }[];
  daily: { day: string; appointments: Money; revenue: Money }[];
  totals: {
    appointments: number;
    completed: number;
    cancelled: number;
    revenue_paid: number;
    revenue_unpaid: number;
    new_patients: number;
  };
}