"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface StudentRecord {
  id: string;
  student_id: string;
  first_name: string;
  middle_name?: string | null;
  last_name?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  status: string;
  is_active?: boolean;
  school_id?: string | null;
  academic_year_id?: string | null;
  class_id?: string | null;
}

export interface GuardianRecord {
  id: string;
  full_name: string;
  relationship: string;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  is_primary: boolean;
}

export interface StudentDocumentRecord {
  id: string;
  student_id: string;
  document_type: string;
  file_name?: string | null;
  storage_path?: string | null;
  mime_type?: string | null;
  file_size?: number | null;
  status: string;
  rejection_reason?: string | null;
}

export interface EnrollmentRecord {
  id: string;
  student_id: string;
  school_id: string;
  academic_year_id: string;
  class_id: string;
  enrollment_date: string;
  exit_date?: string | null;
  status: string;
}

export interface StudentDetailRecord
  extends StudentRecord {
  guardians: GuardianRecord[];
  enrollment?: EnrollmentRecord | null;
}

export interface StudentFilters {
  school_id?: string;
  academic_year_id?: string;
  class_id?: string;
  status?: string;
  include_inactive?: boolean;
}

function normalize<T>(data: unknown): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }

  if (
    typeof data === "object" &&
    data !== null
  ) {
    const record =
      data as Record<string, unknown>;

    for (const key of [
      "items",
      "data",
      "results",
      "records",
      "students",
    ]) {
      if (Array.isArray(record[key])) {
        return record[key] as T[];
      }
    }
  }

  return [];
}

function queryString(
  filters?: StudentFilters,
) {
  if (!filters) {
    return "";
  }

  const params = new URLSearchParams();

  for (const [
    key,
    value,
  ] of Object.entries(filters)) {
    if (
      value !== undefined &&
      value !== null &&
      value !== ""
    ) {
      params.set(key, String(value));
    }
  }

  const query = params.toString();

  return query ? `?${query}` : "";
}

export function useStudents(
  filters?: StudentFilters,
) {
  return useQuery({
    queryKey: [
      "students",
      filters ?? {},
    ],
    queryFn: async () => {
      const data = await apiFetch<unknown>(
        `/students${queryString(filters)}`,
      );

      return normalize<StudentRecord>(data);
    },
  });
}

export function useStudent(
  studentId?: string,
) {
  return useQuery({
    queryKey: [
      "students",
      studentId,
    ],
    queryFn: () =>
      apiFetch<StudentDetailRecord>(
        `/students/${studentId}`,
      ),
    enabled: Boolean(studentId),
  });
}

export function useStudentGuardians(
  studentId?: string,
) {
  return useQuery({
    queryKey: [
      "students",
      studentId,
      "guardians",
    ],
    queryFn: async () =>
      normalize<GuardianRecord>(
        await apiFetch<unknown>(
          `/students/${studentId}/guardians`,
        ),
      ),
    enabled: Boolean(studentId),
  });
}

export function useStudentDocuments(
  studentId?: string,
) {
  return useQuery({
    queryKey: [
      "students",
      studentId,
      "documents",
    ],
    queryFn: async () =>
      normalize<StudentDocumentRecord>(
        await apiFetch<unknown>(
          `/students/${studentId}/documents`,
        ),
      ),
    enabled: Boolean(studentId),
  });
}

export function useCreateStudent() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (payload: unknown) =>
      apiFetch<StudentRecord>(
        "/students",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["students"],
      });
    },
  });
}

export function useUpdateStudent(
  studentId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (payload: unknown) =>
      apiFetch<StudentRecord>(
        `/students/${studentId}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["students"],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
        ],
      });
    },
  });
}

function useStudentAction(
  studentId: string,
  action: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<StudentRecord>(
        `/students/${studentId}/${action}`,
        {
          method: "POST",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["students"],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
        ],
      });
    },
  });
}

export function useSubmitStudent(
  studentId: string,
) {
  return useStudentAction(
    studentId,
    "submit",
  );
}

export function useReadyStudent(
  studentId: string,
) {
  return useStudentAction(
    studentId,
    "ready-for-approval",
  );
}

export function useApproveStudent(
  studentId: string,
) {
  return useStudentAction(
    studentId,
    "approve",
  );
}

export function useExitStudent(
  studentId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (exitDate: string) =>
      apiFetch<StudentRecord>(
        `/students/${studentId}/exit?exit_date=${encodeURIComponent(exitDate)}`,
        {
          method: "POST",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["students"],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
        ],
      });
    },
  });
}

export function useGraduateStudent(
  studentId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (exitDate: string) =>
      apiFetch<StudentRecord>(
        `/students/${studentId}/graduate?exit_date=${encodeURIComponent(exitDate)}`,
        {
          method: "POST",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["students"],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
        ],
      });
    },
  });
}

export function useAddGuardian(
  studentId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: unknown,
    ) =>
      apiFetch<GuardianRecord>(
        `/students/${studentId}/guardians`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
          "guardians",
        ],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
        ],
      });
    },
  });
}

export function useVerifyDocument(
  studentId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      documentId,
      remarks,
    }: {
      documentId: string;
      remarks?: string;
    }) =>
      apiFetch<StudentDocumentRecord>(
        `/students/documents/${documentId}/verify`,
        {
          method: "POST",
          body: JSON.stringify({
            remarks:
              remarks || null,
          }),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
          "documents",
        ],
      });
    },
  });
}

export function useRejectDocument(
  studentId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      documentId,
      reason,
    }: {
      documentId: string;
      reason: string;
    }) =>
      apiFetch<StudentDocumentRecord>(
        `/students/documents/${documentId}/reject`,
        {
          method: "POST",
          body: JSON.stringify({
            reason,
          }),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [
          "students",
          studentId,
          "documents",
        ],
      });
    },
  });
}