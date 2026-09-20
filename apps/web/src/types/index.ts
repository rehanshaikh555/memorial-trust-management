export type UserRole =
  | "SUPER_ADMIN"
  | "TRUST_ADMIN"
  | "SCHOOL_ADMIN"
  | "TEACHER"
  | "VIEWER"
  | string;

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role?: UserRole;
  role_name?: UserRole;
  trust_id?: string | null;
  school_id?: string | null;
  is_active: boolean;
  is_verified: boolean;
  [key: string]: unknown;
}

export interface School {
  id: string;
  name: string;
  code?: string;
  address?: string;
  city?: string;
  state?: string;
  phone?: string;
  email?: string;
  is_active?: boolean;
  [key: string]: unknown;
}

export interface Student {
  id: string;
  student_id?: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  name?: string;
  gender?: string;
  date_of_birth?: string;
  status?: string;
  school_id?: string;
  class_id?: string;
  [key: string]: unknown;
}

export interface Teacher {
  id: string;
  teacher_id?: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  name?: string;
  email?: string;
  phone?: string;
  qualification?: string;
  status?: string;
  school_id?: string;
  is_active?: boolean;
  [key: string]: unknown;
}

export function displayName(
  item: {
    first_name?: string;
    middle_name?: string;
    last_name?: string;
    name?: string;
  },
) {
  if (item.name) return item.name;

  return [
    item.first_name,
    item.middle_name,
    item.last_name,
  ]
    .filter(Boolean)
    .join(" ")
    .trim() || "Unnamed";
}

export function normalizeCollection<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (
    payload &&
    typeof payload === "object"
  ) {
    const object = payload as Record<string, unknown>;

    const candidates = [
      object.items,
      object.data,
      object.results,
      object.records,
      object.schools,
      object.students,
      object.teachers,
    ];

    for (const candidate of candidates) {
      if (Array.isArray(candidate)) {
        return candidate as T[];
      }
    }
  }

  return [];
}
export interface DashboardStat {
  label: string;
  value: string;
  change: string;
  trend: "up" | "down" | "neutral";
  description: string;
}