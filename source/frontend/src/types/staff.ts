// Shape of one person returned by GET /api/public/staff.
import type { Role } from "./index";

export interface StaffMember {
  id: number;
  full_name: string;
  role: Role;
  specialization: string | null; // doctors only
  assigned_doctor_name: string | null; // nurses only
  weekdays: number[]; // doctors only: 1 = Monday ... 7 = Sunday
}