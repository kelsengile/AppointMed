// Shape of one department returned by GET /api/public/departments.
export interface DepartmentItem {
  id: number;
  name: string;
  description: string;
  icon: string | null; // image path under frontend/public, or null
  is_featured: boolean; // shown as a card on the front page
  doctor_count: number; // active doctors whose specialization equals the name
}