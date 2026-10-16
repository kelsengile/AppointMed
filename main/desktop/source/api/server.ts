import type { ServerCredentials, ServerStatus } from "../types/auth";
import { apiRequest } from "./client";

export const getServerStatus = () => apiRequest<ServerStatus>("/server/status");

export const connectServer = (credentials: ServerCredentials) =>
  apiRequest<ServerStatus>("/server/connect", { method: "POST", body: credentials });

export const disconnectServer = () =>
  apiRequest<ServerStatus>("/server/disconnect", { method: "POST" });