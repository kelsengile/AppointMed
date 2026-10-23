import type {
  AppointmentItem,
  BookingPayload,
  BookingReceipt,
  Catalog,
  Encounter,
  ExamPayload,
  InvoiceItem,
  LoginResponse,
  NotificationItem,
  PatientItem,
} from "../types";
import { request } from "./client";

export const authApi = {
  login: (username: string, password: string) =>
    request<LoginResponse>("/api/auth/login", { method: "POST", body: { username, password } }),
};

export const publicApi = {
  catalog: () => request<Catalog>("/api/public/doctors"),
  slots: (doctorId: number, day: string) =>
    request<{ date: string; slots: string[] }>(`/api/public/doctors/${doctorId}/slots?date=${day}`),
  book: (payload: BookingPayload) =>
    request<BookingReceipt>("/api/public/booking-requests", { method: "POST", body: payload }),
};

export const staffApi = {
  notifications: (status: string) => request<NotificationItem[]>(`/api/notifications?status=${status}`),
  approve: (id: number) => request<{ emailed: boolean }>(`/api/notifications/${id}/approve`, { method: "POST" }),
  dismiss: (id: number, note: string | null) =>
    request<{ emailed: boolean }>(`/api/notifications/${id}/dismiss`, { method: "POST", body: { note } }),

  appointments: (day: string) => request<AppointmentItem[]>(`/api/appointments?date=${day}`),
  checkIn: (id: number) => request<unknown>(`/api/appointments/${id}/check-in`, { method: "POST" }),
  cancel: (id: number) => request<unknown>(`/api/appointments/${id}/cancel`, { method: "POST" }),
  start: (id: number) => request<unknown>(`/api/appointments/${id}/start`, { method: "POST" }),
  finish: (id: number, payload: ExamPayload) =>
    request<unknown>(`/api/appointments/${id}/finish`, { method: "POST", body: payload }),

  invoices: (status: string) => request<InvoiceItem[]>(`/api/invoices?status=${status}`),
  pay: (id: number) => request<unknown>(`/api/invoices/${id}/pay`, { method: "POST" }),

  history: (search: string, patientId?: number) => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (patientId !== undefined) params.set("patient_id", String(patientId));
    return request<Encounter[]>(`/api/history?${params.toString()}`);
  },
  patients: (search: string) => request<PatientItem[]>(`/api/patients?search=${encodeURIComponent(search)}`),
};