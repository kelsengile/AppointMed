export type Role = "doctor" | "nurse" | "admin";
export const ROLES: Role[] = ["doctor", "nurse", "admin"];

export interface SessionUser {
  username: string;
  role: Role;
}

export interface NavItem {
  path: string; // relative to /<role>/
  label: string;
  description: string; // shown on the placeholder page
  bottom?: boolean; // true = pinned to the bottom of the side panel
}