import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export type TeacherStatus =
  | "APPLICATION_DRAFT"
  | "SUBMITTED"
  | "READY_FOR_APPROVAL"
  | "ACTIVE"
  | "INACTIVE"
  | "DEACTIVATED";

export interface TeacherRecord {
  id: string;
  user_id: string | null;
  teacher_id: string;
  school_id: string;
  first_name: string;
  middle_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  gender: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  qualification: string | null;
  status: string;
  is_active: boolean;
}

export interface TeacherCreatePayload {
  school_id: string;
  teacher_id: string;
  first_name: string;
  middle_name?: string | null;
  last_name?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  qualification?: string | null;
}

export interface TeacherUpdatePayload {
  first_name?: string;
  middle_name?: string | null;
  last_name?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  qualification?: string | null;
}

export interface TeacherAssignmentRecord {
  id: string;
  teacher_id: string;
  school_id: string;
  academic_year_id: string;
  class_id: string | null;
  subject: string | null;
  start_date: string;
  end_date: string | null;
  status: string;
}

export interface TeacherAssignmentCreatePayload {
  teacher_id: string;
  school_id: string;
  academic_year_id: string;
  class_id?: string | null;
  subject?: string | null;
  start_date: string;
  end_date?: string | null;
}

export interface TeacherAssignmentUpdatePayload {
  class_id?: string | null;
  subject?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  status?: string | null;
}

export interface TeacherAttendanceRecord {
  id: string;
  teacher_id: string;
  attendance_date: string;
  status: string;
  marked_by: string;
  remarks: string | null;
}

export interface TeacherAttendanceCreatePayload {
  teacher_id: string;
  attendance_date: string;
  status: string;
  remarks?: string | null;
}

interface ListOptions {
  schoolId?: string;
  includeInactive?: boolean;
}

interface AssignmentListOptions {
  teacherId?: string;
  schoolId?: string;
  academicYearId?: string;
  includeInactive?: boolean;
}

interface TeacherAttendanceOptions {
  schoolId?: string;
  teacherId?: string;
  attendanceDate?: string;
}

function normalizeList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;

    for (const key of ["items", "data", "results", "records"]) {
      if (Array.isArray(record[key])) {
        return record[key] as T[];
      }
    }
  }

  return [];
}

function buildQuery(
  params: Record<string, string | boolean | undefined>,
) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });

  const query = search.toString();
  return query ? `?${query}` : "";
}

export const teacherKeys = {
  all: ["teachers"] as const,
  list: (options: ListOptions) => ["teachers", "list", options] as const,
  detail: (teacherId: string) => ["teachers", "detail", teacherId] as const,
  assignments: (options: AssignmentListOptions) =>
    ["teachers", "assignments", options] as const,
  attendance: (options: TeacherAttendanceOptions) =>
    ["teachers", "attendance", options] as const,
};

export function useTeachers(options: ListOptions = {}) {
  return useQuery({
    queryKey: teacherKeys.list(options),
    queryFn: async () => {
      const query = buildQuery({
        school_id: options.schoolId,
        include_inactive: options.includeInactive,
      });

      const response = await apiFetch<unknown>(`/teachers${query}`);
      return normalizeList<TeacherRecord>(response);
    },
  });
}

export function useTeacher(teacherId: string | undefined) {
  return useQuery({
    queryKey: teacherKeys.detail(teacherId ?? ""),
    enabled: Boolean(teacherId),
    queryFn: () =>
      apiFetch<TeacherRecord>(`/teachers/${teacherId}`),
  });
}

export function useCreateTeacher() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TeacherCreatePayload) =>
      apiFetch<TeacherRecord>("/teachers", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
  });
}

export function useUpdateTeacher(teacherId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TeacherUpdatePayload) =>
      apiFetch<TeacherRecord>(`/teachers/${teacherId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: teacherKeys.detail(teacherId),
      });
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
  });
}

function createLifecycleMutation(
  teacherId: string,
  action: "submit" | "ready-for-approval" | "approve" | "deactivate",
) {
  return {
    teacherId,
    action,
  };
}

export function useSubmitTeacher(teacherId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<TeacherRecord>(
        `/teachers/${createLifecycleMutation(teacherId, "submit").teacherId}/submit`,
        { method: "POST" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: teacherKeys.detail(teacherId),
      });
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
  });
}

export function useReadyTeacher(teacherId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<TeacherRecord>(
        `/teachers/${createLifecycleMutation(teacherId, "ready-for-approval").teacherId}/ready-for-approval`,
        { method: "POST" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: teacherKeys.detail(teacherId),
      });
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
  });
}

export function useApproveTeacher(teacherId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<TeacherRecord>(
        `/teachers/${createLifecycleMutation(teacherId, "approve").teacherId}/approve`,
        { method: "POST" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: teacherKeys.detail(teacherId),
      });
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
  });
}

export function useDeactivateTeacher(teacherId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<TeacherRecord>(
        `/teachers/${createLifecycleMutation(teacherId, "deactivate").teacherId}/deactivate`,
        { method: "POST" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: teacherKeys.detail(teacherId),
      });
      queryClient.invalidateQueries({ queryKey: teacherKeys.all });
    },
  });
}

export function useTeacherAssignments(
  options: AssignmentListOptions = {},
) {
  return useQuery({
    queryKey: teacherKeys.assignments(options),
    queryFn: async () => {
      const query = buildQuery({
        teacher_id: options.teacherId,
        school_id: options.schoolId,
        academic_year_id: options.academicYearId,
        include_inactive: options.includeInactive,
      });

      const response = await apiFetch<unknown>(
        `/teachers/assignments${query}`,
      );

      return normalizeList<TeacherAssignmentRecord>(response);
    },
  });
}

export function useCreateTeacherAssignment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TeacherAssignmentCreatePayload) =>
      apiFetch<TeacherAssignmentRecord>("/teachers/assignments", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["teachers", "assignments"],
      });
    },
  });
}

export function useUpdateTeacherAssignment(assignmentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TeacherAssignmentUpdatePayload) =>
      apiFetch<TeacherAssignmentRecord>(
        `/teachers/assignments/${assignmentId}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["teachers", "assignments"],
      });
    },
  });
}

export function useDeactivateTeacherAssignment(
  assignmentId: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<TeacherAssignmentRecord>(
        `/teachers/assignments/${assignmentId}/deactivate`,
        { method: "POST" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["teachers", "assignments"],
      });
    },
  });
}

export function useTeacherAttendance(
  options: TeacherAttendanceOptions = {},
) {
  return useQuery({
    queryKey: teacherKeys.attendance(options),
    queryFn: async () => {
      const query = buildQuery({
        school_id: options.schoolId,
        teacher_id: options.teacherId,
        attendance_date: options.attendanceDate,
      });

      const response = await apiFetch<unknown>(
        `/teachers/attendance${query}`,
      );

      return normalizeList<TeacherAttendanceRecord>(response);
    },
  });
}

export function useCreateTeacherAttendance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      schoolId,
      payload,
    }: {
      schoolId: string;
      payload: TeacherAttendanceCreatePayload;
    }) =>
      apiFetch<TeacherAttendanceRecord>(
        `/teachers/attendance?school_id=${encodeURIComponent(schoolId)}`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["teachers", "attendance"],
      });
    },
  });
}
