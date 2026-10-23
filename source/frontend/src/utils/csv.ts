// Downloads rows as a CSV file (used by Reports and Audit Logs).
type Cell = string | number | null | undefined;

function escapeCell(cell: Cell): string {
  if (cell === null || cell === undefined) return "";
  let text = String(cell);
  // A leading = + - @ makes spreadsheets run the cell as a formula, so neutralise it.
  if (typeof cell === "string" && /^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function downloadCsv(filename: string, rows: Cell[][]): void {
  const body = rows.map((row) => row.map(escapeCell).join(",")).join("\r\n");
  const blob = new Blob(["\ufeff" + body], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}