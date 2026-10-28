// Backend calls for the admin Database page. Paths match backend/routes/database_routes.py.
import type { DbQueryResult, DbTableData, DbTableSummary } from "../types/database";
import { download, request } from "./client";

type Ok = { ok: boolean };

const BASE = "/api/admin/database";

function qs(params: Record<string, string | number>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== "") search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const databaseApi = {
  tables: () => request<DbTableSummary[]>(`${BASE}/tables`),
  table: (name: string, q: string, limit: number, offset: number) =>
    request<DbTableData>(`${BASE}/tables/${encodeURIComponent(name)}${qs({ q, limit, offset })}`),
  insertRow: (name: string, values: Record<string, string>) =>
    request<Ok>(`${BASE}/tables/${encodeURIComponent(name)}/rows`, { method: "POST", body: { values } }),
  updateRow: (name: string, key: string, values: Record<string, string>) =>
    request<Ok>(`${BASE}/tables/${encodeURIComponent(name)}/rows/${encodeURIComponent(key)}`, { method: "PUT", body: { values } }),
  deleteRow: (name: string, key: string) =>
    request<Ok>(`${BASE}/tables/${encodeURIComponent(name)}/rows/${encodeURIComponent(key)}`, { method: "DELETE" }),
  query: (sql: string) => request<DbQueryResult>(`${BASE}/query`, { method: "POST", body: { sql } }),
  backup: () => download(`${BASE}/backup`),
};