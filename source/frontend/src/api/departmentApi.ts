// Public department list for the front page. Path matches backend/routes/public_routes.py.
import type { DepartmentItem } from "../types/department";
import { request } from "./client";

export const departmentApi = {
  list: () => request<DepartmentItem[]>("/api/public/departments"),
};