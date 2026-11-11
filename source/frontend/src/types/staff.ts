// Shapes returned by GET /api/public/staff and GET /api/public/staff/{id}.
import type { Role } from "./index";

export interface StaffMember {
  id: number;
  full_name: string;
  role: Role;
  specialization: string | null; // doctors only
  assigned_doctor_id: number | null; // nurses only
  assigned_doctor_name: string | null; // nurses only
  weekdays: number[]; // doctors only: 1 = Monday ... 7 = Sunday
  has_photo: boolean; // true when the person uploaded a profile picture
  photo_version: number; // changes when the picture changes (cache buster)
}

export interface StaffDetail extends StaffMember {
  bio: string | null;
  education: string | null;
  years_experience: number | null;
  languages: string | null;
  nurses: { id: number; full_name: string; has_photo: boolean; photo_version: number }[]; // doctors only
}