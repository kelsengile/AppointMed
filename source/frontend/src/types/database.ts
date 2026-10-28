// Types for the admin Database page. Field names match backend/services/database_service.py.

export type DbCell = string | number | boolean | null;
export type DbRow = Record<string, DbCell>;

export interface DbTableSummary {
  name: string;
  rows: number;
  columns: number;
  read_only: boolean;
  can_insert: boolean;
}

export interface DbColumn {
  name: string;
  type: string; // full MySQL type, for example "enum('Male','Female','Other')"
  data_type: string; // base type, for example "varchar"
  nullable: boolean;
  primary: boolean;
  auto: boolean; // AUTO_INCREMENT
  generated: boolean; // computed by MySQL, cannot be set
  hidden: boolean; // never sent to the browser (password hashes, pictures)
}

export interface DbTableData {
  name: string;
  columns: DbColumn[];
  primary_key: string | null;
  read_only: boolean;
  can_insert: boolean;
  rows: DbRow[];
  total: number;
  limit: number;
  offset: number;
}

export interface DbQueryResult {
  kind: string;
  columns: string[];
  rows: DbCell[][];
  truncated: boolean;
  affected: number | null;
}