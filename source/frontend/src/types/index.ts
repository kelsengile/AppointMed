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