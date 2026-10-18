export interface ParsedAddress {
  host: string;
  port: number;
}

/** Accepts "localhost", "192.168.1.5" or "192.168.1.5:3307". Default port is 3306. */
export function parseAddress(input: string): ParsedAddress | null {
  const value = input.trim();
  if (!value) return null;

  const index = value.lastIndexOf(":");
  if (index === -1) return { host: value, port: 3306 };

  const host = value.slice(0, index).trim();
  const portText = value.slice(index + 1).trim();
  const port = Number(portText);
  if (!host || !/^\d+$/.test(portText) || port < 1 || port > 65535) return null;
  return { host, port };
}