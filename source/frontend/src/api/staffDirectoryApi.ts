// Public staff list for the front page. Path matches backend/routes/public_routes.py.
import type { StaffMember } from "../types/staff";
import { request } from "./client";

export const staffDirectoryApi = {
  list: () => request<StaffMember[]>("/api/public/staff"),
};