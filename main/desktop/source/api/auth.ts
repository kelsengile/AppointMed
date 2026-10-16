import type { AuthUser, LoginResponse } from "../types/auth";
import { apiRequest } from "./client";

export const login = (username: string, password: string) =>
  apiRequest<LoginResponse>("/auth/login", { method: "POST", body: { username, password } });

export const getCurrentUser = (token: string) => apiRequest<AuthUser>("/auth/me", { token });