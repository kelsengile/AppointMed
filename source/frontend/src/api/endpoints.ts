// Every backend call the app makes. Paths and bodies match backend/routes/*.py.
import type {
  AdminDashboard,
  AppointmentCreatePayload,
  AppointmentItem,
  AuditPage,
  BookingPayload,
  BookingReceipt,
  Catalog,
  DoctorRef,
  Encounter,
  ExamPayload,
  InvoiceItem,
  LoginResponse,
  NotificationItem,
  PatientItem,
  PatientPayload,
  PrescriptionRecord,
  Profile,
  ReportData,
  RoomItem,
  RoomStatus,
  ScheduleBlock,
  SettingRow,
  StaffDashboard,
  UserCreatePayload,
  UserRecord,
  UserUpdatePayload,
} from "../types";
import { request } from "./client";

type Query = Record<string, string | number | null | undefined>;
type Ok = { ok: boolean };
type SavedPatient = Omit<PatientItem, "visit_count">;

/** Builds "?a=1&b=2", skipping empty values. */
function qs(params: Query): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const authApi = {
  login: (username: string, password: string) =>
    request<LoginResponse>("/api/auth/login", { method: "POST", body: { username, password } }),
  me: () => request<Profile>("/api/auth/me"),
  updateMe: (full_name: string, email: string | null) =>
    request<Profile>("/api/auth/me", { method: "PUT", body: { full_name, email } }),
  setAvatar: (image: string) => request<Profile>("/api/auth/me/avatar", { method: "PUT", body: { image } }),
  removeAvatar: () => request<Profile>("/api/auth/me/avatar", { method: "DELETE" }),
  changePassword: (current_password: string, new_password: string) =>
    request<Ok>("/api/auth/change-password", { method: "POST", body: { current_password, new_password } }),
};

export const publicApi = {
  catalog: () => request<Catalog>("/api/public/catalog"),
  slots: (doctorId: number, day: string) =>
    request<{ slots: string[] }>(`/api/public/slots${qs({ doctor_id: doctorId, day })}`),
  book: (payload: BookingPayload) => request<BookingReceipt>("/api/public/bookings", { method: "POST", body: payload }),
};

export const staffApi = {
  dashboard: () => request<StaffDashboard>("/api/staff/dashboard"),

  // booking requests
  notifications: (status: string) =>
    request<NotificationItem[]>(`/api/staff/notifications${qs({ status: status === "all" ? "" : status })}`),
  approve: (id: number, body: { room_id: number | null; scheduled_time: string | null }) =>
    request<AppointmentItem>(`/api/staff/notifications/${id}/approve`, { method: "POST", body }),
  dismiss: (id: number, note: string) =>
    request<Ok>(`/api/staff/notifications/${id}/dismiss`, { method: "POST", body: { note } }),

  // appointments
  appointments: (day: string, q = "") => request<AppointmentItem[]>(`/api/staff/appointments${qs({ day, q })}`),
  createAppointment: (body: AppointmentCreatePayload) =>
    request<AppointmentItem>("/api/staff/appointments", { method: "POST", body }),
  checkIn: (id: number) => request<AppointmentItem>(`/api/staff/appointments/${id}/check-in`, { method: "POST" }),
  start: (id: number, roomId: number | null) =>
    request<AppointmentItem>(`/api/staff/appointments/${id}/start`, { method: "POST", body: { room_id: roomId } }),
  release: (id: number) => request<AppointmentItem>(`/api/staff/appointments/${id}/release`, { method: "POST" }),
  finish: (id: number, payload: ExamPayload) =>
    request<AppointmentItem>(`/api/staff/appointments/${id}/finish`, { method: "POST", body: payload }),
  cancel: (id: number, reason: string | null) =>
    request<AppointmentItem>(`/api/staff/appointments/${id}/cancel`, { method: "POST", body: { reason } }),
  reschedule: (id: number, scheduledTime: string) =>
    request<AppointmentItem>(`/api/staff/appointments/${id}/reschedule`, { method: "POST", body: { scheduled_time: scheduledTime } }),
  assignRoom: (id: number, roomId: number | null) =>
    request<AppointmentItem>(`/api/staff/appointments/${id}/room`, { method: "PUT", body: { room_id: roomId } }),
  bill: (id: number) => request<{ id: number }>(`/api/staff/appointments/${id}/bill`, { method: "POST" }),

  // rooms
  rooms: () => request<RoomItem[]>("/api/staff/rooms"),
  setRoomStatus: (id: number, status: RoomStatus) =>
    request<Ok>(`/api/staff/rooms/${id}/status`, { method: "PUT", body: { status } }),

  // patients
  patients: (q: string) => request<PatientItem[]>(`/api/staff/patients${qs({ q })}`),
  createPatient: (body: PatientPayload) => request<SavedPatient>("/api/staff/patients", { method: "POST", body }),
  updatePatient: (id: number, body: PatientPayload) =>
    request<SavedPatient>(`/api/staff/patients/${id}`, { method: "PUT", body }),
  deletePatient: (id: number) => request<Ok>(`/api/staff/patients/${id}`, { method: "DELETE" }),
  patientHistory: (id: number) => request<Encounter[]>(`/api/staff/patients/${id}/history`),

  // history, invoices, prescriptions
  history: (q: string, dateFrom: string, dateTo: string) =>
    request<Encounter[]>(`/api/staff/history${qs({ q, date_from: dateFrom, date_to: dateTo })}`),
  invoices: (status: string) =>
    request<InvoiceItem[]>(`/api/staff/invoices${qs({ status: status === "all" ? "" : status })}`),
  unbilled: () => request<AppointmentItem[]>("/api/staff/invoices/unbilled"),
  pay: (id: number) => request<Ok>(`/api/staff/invoices/${id}/pay`, { method: "POST" }),
  prescriptions: (q: string) => request<PrescriptionRecord[]>(`/api/staff/prescriptions${qs({ q })}`),
};

export const adminApi = {
  dashboard: () => request<AdminDashboard>("/api/admin/dashboard"),

  users: (role: string, q: string) => request<UserRecord[]>(`/api/admin/users${qs({ role, q })}`),
  doctors: () => request<DoctorRef[]>("/api/admin/doctors"),
  createUser: (body: UserCreatePayload) => request<UserRecord>("/api/admin/users", { method: "POST", body }),
  updateUser: (id: number, body: UserUpdatePayload) => request<UserRecord>(`/api/admin/users/${id}`, { method: "PUT", body }),
  setActive: (id: number, isActive: boolean) =>
    request<UserRecord>(`/api/admin/users/${id}/active`, { method: "POST", body: { is_active: isActive } }),
  resetPassword: (id: number, newPassword: string) =>
    request<Ok>(`/api/admin/users/${id}/password`, { method: "POST", body: { new_password: newPassword } }),
  schedule: (id: number) => request<ScheduleBlock[]>(`/api/admin/users/${id}/schedule`),
  saveSchedule: (id: number, blocks: ScheduleBlock[]) =>
    request<ScheduleBlock[]>(`/api/admin/users/${id}/schedule`, { method: "PUT", body: { blocks } }),

  rooms: () => request<RoomItem[]>("/api/admin/rooms"),
  createRoom: (room_name: string, status: RoomStatus) =>
    request<RoomItem[]>("/api/admin/rooms", { method: "POST", body: { room_name, status } }),
  updateRoom: (id: number, room_name: string, status: RoomStatus) =>
    request<RoomItem[]>(`/api/admin/rooms/${id}`, { method: "PUT", body: { room_name, status } }),
  deleteRoom: (id: number) => request<RoomItem[]>(`/api/admin/rooms/${id}`, { method: "DELETE" }),

  settings: () => request<SettingRow[]>("/api/admin/settings"),
  saveSettings: (values: Record<string, string>) =>
    request<SettingRow[]>("/api/admin/settings", { method: "PUT", body: { values } }),

  reports: (dateFrom: string, dateTo: string) =>
    request<ReportData>(`/api/admin/reports${qs({ date_from: dateFrom, date_to: dateTo })}`),
  audit: (q: string, action: string, limit: number, offset: number) =>
    request<AuditPage>(`/api/admin/audit${qs({ q, action, limit, offset })}`),
};