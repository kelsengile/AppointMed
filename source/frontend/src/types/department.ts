// Shape of one department returned by GET /api/public/departments (and /api/admin/departments).
export interface DepartmentItem {
  id: number;
  name: string;
  description: string;
  icon: string | null; // image path or API address, or null
  is_featured: boolean; // shown as a card on the front page
  doctor_count: number; // active doctors whose specialization equals the name
  is_active?: boolean; // admin list only
  sort_order?: number; // admin list only
}

export interface DepartmentPayload {
  name: string;
  description: string;
  is_featured: boolean;
  is_active: boolean;
  sort_order: number;
}