// Website branding calls. Paths match backend/routes/public_routes.py and admin_routes.py.
import type { SiteContent } from "../types/site";
import { request } from "./client";

export type SiteImageKind = "logo" | "hero";

export const siteApi = {
  get: () => request<SiteContent>("/api/public/site"),
  save: (values: Record<string, string>) => request<SiteContent>("/api/admin/site", { method: "PUT", body: { values } }),
  setImage: (kind: SiteImageKind, image: string) =>
    request<SiteContent>(`/api/admin/site/image/${kind}`, { method: "PUT", body: { image } }),
  removeImage: (kind: SiteImageKind) => request<SiteContent>(`/api/admin/site/image/${kind}`, { method: "DELETE" }),
};