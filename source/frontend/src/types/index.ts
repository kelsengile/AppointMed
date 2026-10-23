export type Role = "doctor" | "nurse" | "admin";
export const ROLES: Role[] = ["doctor", "nurse", "admin"];

export interface SessionUser {
  username: string;
  fullName: string;
  role: Role;
}

export interface NavItem {
  path: string; // relative to /<role>/
  label: string;
  description: string; // shown on the placeholder page
  group?: string; // header shown above this item in the side panel
  pin?: "profile" | "settings" | "help"; // items pinned to a fixed spot instead of a group
}

// ---------- API data (field names match the backend JSON) ----------

export interface LoginResponse {
  access_token: string;
  user: { id: number; username: string; full_name: string; role: Role };
}

export interface DoctorOption {
  id: number;
  full_name: string;
  specialization: string | null;
  weekdays: number[]; // 1 = Monday ... 7 = Sunday
}

export interface Catalog {
  clinic_name: string;
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
}

export type AppointmentStatus = "Scheduled" | "Checked-in" | "Consulting" | "Examined" | "Completed" | "Cancelled";

export interface AppointmentItem {
  id: number;
  patient_id: number | null;
  full_name: string;
  doctor_id: number;
  source: string;
  scheduled_time: string;
  reason: string | null;
  status: AppointmentStatus;
  checked_in_at: string | null;
  birthdate: string | null;
  sex: Sex | null;
  contact_number: string | null;
  invoice_id: number | null;
  consultation_fee: number | null;
  invoice_amount: number | null;
  invoice_status: string | null;
}

export interface PrescriptionLine {
  id: number;
  medicine_name: string;
  dosage: string | null;
  quantity: number;
  unit_price: number;
  instructions: string | null;
}

export interface ExamPayload {
  diagnosis: string;
  notes: string | null;
  prescription_notes: string | null;
  consultation_fee: number;
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
  consultation_fee: number;
  medicines_total: number;
  amount: number;
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
  consultation_fee: number | null;
  medicines_total: number | null;
  amount: number | null;
  paid_at: string | null;
  items: PrescriptionLine[];
}

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