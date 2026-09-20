"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface SchoolRecord {
  id: string;
  name: string;
  code: string;
  address?: string | null;
  phone?: string | null;
  email?: string | null;
  is_active: boolean;
}

export interface AcademicYearRecord {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_active: boolean;
}

export interface ClassRecord {
  id: string;
  school_id: string;
  academic_year_id: string;
  name: string;
  grade_level: number;
  section?: string | null;
  is_active: boolean;
}

function normalize<T>(
  data: unknown,
  keys: string[],
): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }

  if (
    typeof data === "object" &&
    data !== null
  ) {
    const record =
      data as Record<string, unknown>;

    for (const key of keys) {
      if (Array.isArray(record[key])) {
        return record[key] as T[];
      }
    }
  }

  return [];
}

export function useSchoolList() {
  return useQuery({
    queryKey: ["schools"],
    queryFn: async () =>
      normalize<SchoolRecord>(
        await apiFetch<unknown>(
          "/schools",
        ),
        [
          "items",
          "data",
          "results",
          "records",
          "schools",
        ],
      ),
  });
}

export function useSchool(
  schoolId?: string,
) {
  return useQuery({
    queryKey: [
      "schools",
      schoolId,
    ],
    queryFn: () =>
      apiFetch<SchoolRecord>(
        `/schools/${schoolId}`,
      ),
    enabled: Boolean(schoolId),
  });
}

export function useCreateSchool() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: unknown,
    ) =>
      apiFetch<SchoolRecord>(
        "/schools",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["schools"],
      });
    },
  });
}

export function useUpdateSchool(
  schoolId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: unknown,
    ) =>
      apiFetch<SchoolRecord>(
        `/schools/${schoolId}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["schools"],
      });

      queryClient.invalidateQueries({
        queryKey: [
          "schools",
          schoolId,
        ],
      });
    },
  });
}

export function useDeactivateSchool(
  schoolId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<SchoolRecord>(
        `/schools/${schoolId}/deactivate`,
        {
          method: "POST",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["schools"],
      });
    },
  });
}

export function useAcademicYears() {
  return useQuery({
    queryKey: ["academic-years"],
    queryFn: async () =>
      normalize<AcademicYearRecord>(
        await apiFetch<unknown>(
          "/academic-years",
        ),
        [
          "items",
          "data",
          "results",
          "records",
          "academic_years",
        ],
      ),
  });
}

export function useCreateAcademicYear() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: unknown,
    ) =>
      apiFetch<AcademicYearRecord>(
        "/academic-years",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["academic-years"],
      });
    },
  });
}

export function useSetCurrentAcademicYear() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      academicYearId: string,
    ) =>
      apiFetch<AcademicYearRecord>(
        `/academic-years/${academicYearId}/set-current`,
        {
          method: "POST",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["academic-years"],
      });
    },
  });
}

export function useDeactivateAcademicYear() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      academicYearId: string,
    ) =>
      apiFetch<AcademicYearRecord>(
        `/academic-years/${academicYearId}/deactivate`,
        {
          method: "POST",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["academic-years"],
      });
    },
  });
}

export function useClasses(
  filters?: {
    school_id?: string;
    academic_year_id?: string;
  },
) {
  return useQuery({
    queryKey: [
      "classes",
      filters ?? {},
    ],
    queryFn: async () => {
      const params =
        new URLSearchParams();

      if (filters?.school_id) {
        params.set(
          "school_id",
          filters.school_id,
        );
      }

      if (
        filters?.academic_year_id
      ) {
        params.set(
          "academic_year_id",
          filters.academic_year_id,
        );
      }

      const query =
        params.toString();

      return normalize<ClassRecord>(
        await apiFetch<unknown>(
          `/classes${query ? `?${query}` : ""}`,
        ),
        [
          "items",
          "data",
          "results",
          "records",
          "classes",
        ],
      );
    },
  });
}

export function useCreateClass() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: unknown,
    ) =>
      apiFetch<ClassRecord>(
        "/classes",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["classes"],
      });
    },
  });
}

export function useUpdateClass(
  classId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: unknown,
    ) =>
      apiFetch<ClassRecord>(
        `/classes/${classId}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["classes"],
      });
    },
  });
}

export function useDeactivateClass(
  classId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch<ClassRecord>(
        `/classes/${classId}/deactivate`,
        {
          method: "POST",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["classes"],
      });
    },
  });
}