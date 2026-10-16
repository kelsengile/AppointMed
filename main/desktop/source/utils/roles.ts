import type { Role } from "../types/auth";

export const ROLE_HOME: Record<Role, string> = {
  doctor: "/doctor",
  nurse: "/nurse",
  admin: "/admin",
};

export const ROLE_LABEL: Record<Role, string> = {
  doctor: "Doctor",
  nurse: "Nurse",
  admin: "Administrator",
};