"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export type AttendanceStatus =
  | "PRESENT"
  | "ABSENT"
  | "LATE"
  | "EXCUSED";

export interface AttendanceSheetItem {
  enrollment_id: string;
  student_id: string;
  student_code: string;
  student_name: string;
  status: AttendanceStatus | string;
  remarks: string | null;
}

export interface AttendanceSheetResponse {
  school_id: string;
  academic_year_id: string;
  class_id: string;
  attendance_date: string;
  is_working_day: boolean;
  items: AttendanceSheetItem[];
}

export interface AttendanceItem {
  id: string;
  enrollment_id: string;
  student_id: string;
  student_code: string;
  student_name: string;
  class_id: string;
  academic_year_id: string;
  school_id: string;
  attendance_date: string;
  status: AttendanceStatus | string;
  remarks: string | null;
  marked_by: string;
}

export interface AttendanceEntry {
  enrollment_id: string;
  status: AttendanceStatus | string;
  remarks?: string | null;
}

export interface BulkAttendanceRequest {
  school_id: string;
  academic_year_id: string;
  class_id: string;
  attendance_date: string;
  entries: AttendanceEntry[];
}

export interface AttendanceBulkResponse {
  attendance_date: string;
  count: number;
  items: AttendanceItem[];
}

export interface CalendarRecord {
  id: string;
  school_id: string;
  academic_year_id: string;
  calendar_date: string;
  is_working_day: boolean;
  day_type: string;
  holiday_name: string | null;
  remarks: string | null;
}

export interface CalendarCreate {
  school_id: string;
  academic_year_id: string;
  calendar_date: string;
  is_working_day?: boolean;
  day_type?: string;
  holiday_name?: string | null;
  remarks?: string | null;
}

export interface CalendarUpdate {
  is_working_day?: boolean;
  day_type?: string;
  holiday_name?: string | null;
  remarks?: string | null;
}

export interface AttendanceCorrection {
  id: string;
  attendance_id: string;
  school_id: string;
  attendance_date: string;
  old_status: string;
  old_remarks: string | null;
  requested_status: string;
  requested_remarks: string | null;
  reason: string;
  status: string;
  requested_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_remarks: string | null;
}

export interface AttendanceCorrectionCreate {
  attendance_id: string;
  requested_status: string;
  requested_remarks?: string | null;
  reason: string;
}

export interface AttendanceCorrectionReview {
  remarks?: string | null;
}

export interface MonthlyAttendanceReport {
  student_id: string;
  student_code: string;
  student_name: string;
  school_id: string;
  academic_year_id: string;
  month: number;
  year: number;
  working_days: number;
  recorded_days: number;
  present_days: number;
  absent_days: number;
  late_days: number;
  excused_days: number;
  attendance_percentage: number;
}

export interface YearlyAttendanceReport {
  student_id: string;
  student_code: string;
  student_name: string;
  school_id: string;
  academic_year_id: string;
  working_days: number;
  recorded_days: number;
  present_days: number;
  absent_days: number;
  late_days: number;
  excused_days: number;
  attendance_percentage: number;
}

export interface TeacherAttendanceCreate {
  teacher_id: string;
  attendance_date: string;
  status?: string;
  remarks?: string | null;
}

export interface TeacherAttendanceResponse {
  id: string;
  teacher_id: string;
  attendance_date: string;
  status: string;
  marked_by: string;
  remarks: string | null;
}

function normalizeList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (!payload || typeof payload !== "object") {
    return [];
  }

  const record = payload as Record<string, unknown>;

  for (const key of ["items", "data", "results", "records"]) {
    if (Array.isArray(record[key])) {
      return record[key] as T[];
    }
  }

  return [];
}

function buildQuery(params: Record<string, string | undefined>) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      search.set(key, value);
    }
  });

  const query = search.toString();
  return query ? `?${query}` : "";
}

export function useAttendanceSheet(params: {
  school_id?: string;
  academic_year_id?: string;
  class_id?: string;
  attendance_date?: string;
  enabled?: boolean;
}) {
  const query = buildQuery({
    school_id: params.school_id,
    academic_year_id: params.academic_year_id,
    class_id: params.class_id,
    attendance_date: params.attendance_date,
  });

  return useQuery({
    queryKey: [
      "attendance",
      "sheet",
      params.school_id,
      params.academic_year_id,
      params.class_id,
      params.attendance_date,
    ],
    queryFn: () =>
      apiFetch<AttendanceSheetResponse>(
        `/attendance/sheet${query}`,
      ),
    enabled:
      params.enabled !== false &&
      Boolean(
        params.school_id &&
          params.academic_year_id &&
          params.class_id &&
          params.attendance_date,
      ),
  });
}

export function useAttendance(params: {
  school_id?: string;
  academic_year_id?: string;
  class_id?: string;
  attendance_date?: string;
}) {
  const query = buildQuery(params);

  return useQuery({
    queryKey: ["attendance", "records", params],
    queryFn: async () => {
      const response = await apiFetch<unknown>(`/attendance${query}`);
      return normalizeList<AttendanceItem>(response);
    },
    enabled: Boolean(
      params.school_id ||
        params.academic_year_id ||
        params.class_id ||
        params.attendance_date,
    ),
  });
}

export function useBulkMarkAttendance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BulkAttendanceRequest) =>
      apiFetch<AttendanceBulkResponse>("/attendance/bulk", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "sheet"],
      });

      queryClient.invalidateQueries({
        queryKey: ["attendance", "records"],
      });
    },
  });
}

export function useAttendanceCalendar(params: {
  school_id?: string;
  academic_year_id?: string;
  calendar_date?: string;
}) {
  const query = buildQuery(params);

  return useQuery({
    queryKey: ["attendance", "calendar", params],
    queryFn: async () => {
      const response = await apiFetch<unknown>(
        `/attendance/calendar${query}`,
      );
      return normalizeList<CalendarRecord>(response);
    },
    enabled: Boolean(params.school_id && params.academic_year_id),
  });
}

export function useCreateAttendanceCalendar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CalendarCreate) =>
      apiFetch<CalendarRecord>("/attendance/calendar", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "calendar"],
      });

      queryClient.invalidateQueries({
        queryKey: ["attendance", "sheet"],
      });
    },
  });
}

export function useUpdateAttendanceCalendar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      calendarId,
      payload,
    }: {
      calendarId: string;
      payload: CalendarUpdate;
    }) =>
      apiFetch<CalendarRecord>(
        `/attendance/calendar/${calendarId}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "calendar"],
      });

      queryClient.invalidateQueries({
        queryKey: ["attendance", "sheet"],
      });
    },
  });
}

export function useAttendanceCorrections(params?: {
  school_id?: string;
  status?: string;
}) {
  const query = buildQuery(params ?? {});

  return useQuery({
    queryKey: ["attendance", "corrections", params],
    queryFn: async () => {
      const response = await apiFetch<unknown>(
        `/attendance/corrections${query}`,
      );
      return normalizeList<AttendanceCorrection>(response);
    },
  });
}

export function useCreateAttendanceCorrection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AttendanceCorrectionCreate) =>
      apiFetch<AttendanceCorrection>("/attendance/corrections", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "corrections"],
      });
    },
  });
}

export function useApproveAttendanceCorrection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      correctionId,
      payload,
    }: {
      correctionId: string;
      payload?: AttendanceCorrectionReview;
    }) =>
      apiFetch<AttendanceCorrection>(
        `/attendance/corrections/${correctionId}/approve`,
        {
          method: "POST",
          body: JSON.stringify(payload ?? {}),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "corrections"],
      });

      queryClient.invalidateQueries({
        queryKey: ["attendance", "sheet"],
      });

      queryClient.invalidateQueries({
        queryKey: ["attendance", "records"],
      });
    },
  });
}

export function useRejectAttendanceCorrection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      correctionId,
      payload,
    }: {
      correctionId: string;
      payload?: AttendanceCorrectionReview;
    }) =>
      apiFetch<AttendanceCorrection>(
        `/attendance/corrections/${correctionId}/reject`,
        {
          method: "POST",
          body: JSON.stringify(payload ?? {}),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["attendance", "corrections"],
      });
    },
  });
}

export function useMonthlyAttendanceReport(params: {
  school_id?: string;
  academic_year_id?: string;
  class_id?: string;
  month?: string;
  year?: string;
}) {
  const query = buildQuery(params);

  return useQuery({
    queryKey: ["attendance", "reports", "monthly", params],
    queryFn: async () => {
      const response = await apiFetch<unknown>(
        `/attendance/reports/monthly${query}`,
      );
      return normalizeList<MonthlyAttendanceReport>(response);
    },
    enabled: Boolean(
      params.school_id &&
        params.academic_year_id &&
        params.month &&
        params.year,
    ),
  });
}

export function useYearlyAttendanceReport(params: {
  school_id?: string;
  academic_year_id?: string;
}) {
  const query = buildQuery(params);

  return useQuery({
    queryKey: ["attendance", "reports", "yearly", params],
    queryFn: async () => {
      const response = await apiFetch<unknown>(
        `/attendance/reports/yearly${query}`,
      );
      return normalizeList<YearlyAttendanceReport>(response);
    },
    enabled: Boolean(params.school_id && params.academic_year_id),
  });
}

export function useTeacherAttendance(params?: {
  teacher_id?: string;
  attendance_date?: string;
}) {
  const query = buildQuery(params ?? {});

  return useQuery({
    queryKey: ["teachers", "attendance", params],
    queryFn: async () => {
      const response = await apiFetch<unknown>(
        `/teachers/attendance${query}`,
      );
      return normalizeList<TeacherAttendanceResponse>(response);
    },
  });
}

export function useCreateTeacherAttendance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TeacherAttendanceCreate) =>
      apiFetch<TeacherAttendanceResponse>("/teachers/attendance", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["teachers", "attendance"],
      });
    },
  });
}
