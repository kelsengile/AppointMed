// The only place that calls fetch. Adds the login token and turns errors into ApiError.
const TOKEN_KEY = "appointmed.token";
export const UNAUTHORIZED_EVENT = "appointmed:unauthorized";

export function getToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the token lasts until refresh */
  }
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function messageFrom(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((entry) => {
          const item = entry as { loc?: unknown[]; msg?: string };
          const field = Array.isArray(item.loc) ? String(item.loc[item.loc.length - 1]) : "";
          return field ? `${field}: ${item.msg}` : String(item.msg);
        })
        .join(" ");
    }
  }
  return fallback;
}

export async function request<T>(path: string, options: { method?: string; body?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(path, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check that the backend is running.", 0);
  }

  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    if (response.status === 401 && token) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    throw new ApiError(messageFrom(data, `Request failed (${response.status}).`), response.status);
  }
  return data as T;
}

/** Downloads a file (such as the database backup). The token is sent, so a plain link cannot be used. */
export async function download(path: string): Promise<{ blob: Blob; filename: string }> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(path, { headers });
  } catch {
    throw new ApiError("Cannot reach the server. Check that the backend is running.", 0);
  }

  if (!response.ok) {
    let data: unknown = null;
    try {
      data = JSON.parse(await response.text());
    } catch {
      data = null;
    }
    if (response.status === 401 && token) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    throw new ApiError(messageFrom(data, `Request failed (${response.status}).`), response.status);
  }

  const match = /filename="?([^";]+)"?/i.exec(response.headers.get("Content-Disposition") ?? "");
  return { blob: await response.blob(), filename: match?.[1] ?? "appointmed-backup.sql" };
}