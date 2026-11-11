// Public staff list and profile. Paths match backend/routes/public_routes.py.
import type { StaffDetail, StaffMember } from "../types/staff";
import { request } from "./client";

export const staffDirectoryApi = {
  list: () => request<StaffMember[]>("/api/public/staff"),
  get: (id: number) => request<StaffDetail>(`/api/public/staff/${id}`),
};