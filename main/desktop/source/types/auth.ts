export type Role = "doctor" | "nurse" | "admin";

export interface AuthUser {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  specialization: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface ServerStatus {
  connected: boolean;
  host: string | null;
  port: number | null;
  user: string | null;
  database: string | null;
}

export interface ServerCredentials {
  host: string;
  port: number;
  user: string;
  password: string;
}