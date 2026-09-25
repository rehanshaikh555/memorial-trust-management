import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export type ActivityStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "APPROVED"
  | "REJECTED"
  | "PUBLISHED";

export type ActivityVisibility = "INTERNAL" | "PUBLIC";

export interface ActivityRecord {
  id: string;
  school_id: string;
  academic_year_id: string;
  title: string;
  description: string | null;
  activity_date: string;
  activity_type: string;
  status: ActivityStatus;
  visibility: ActivityVisibility;
  created_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ActivityPhotoRecord {
  id: string;
  activity_id: string;
  file_name: string;
  storage_path: string;
  mime_type: string;
  file_size: number;
  caption: string | null;
  display_order: number;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}

export interface ActivityCreatePayload {
  school_id: string;
  academic_year_id: string;
  title: string;
  description?: string | null;
  activity_date: string;
  activity_type: string;
  visibility: ActivityVisibility;
}

export interface ActivityUpdatePayload {
  title?: string | null;
  description?: string | null;
  activity_date?: string | null;
  activity_type?: string | null;
  visibility?: ActivityVisibility | null;
}

export interface ActivityPhotoCreatePayload {
  file_name: string;
  storage_path: string;
  mime_type: string;
  file_size: number;
  caption?: string | null;
  display_order: number;
}

function normalizeList<T>(value: unknown): T[] {
  if (Array.isArray(value)) {
    return value as T[];
  }

  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;

    for (const key of ["items", "data", "results", "records"]) {
      if (Array.isArray(record[key])) {
        return record[key] as T[];
      }
    }
  }

  return [];
}

function buildQuery(
  params: Record<string, string | undefined>,
) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      search.set(key, value);
    }
  });

  const query = search.toString();

  return query ? `?${query}` : "";
}

const activityKeys = {
  all: ["activities"] as const,
  list: (schoolId?: string, academicYearId?: string, status?: string) =>
    ["activities", "list", schoolId, academicYearId, status] as const,
  detail: (activityId: string) =>
    ["activities", "detail", activityId] as const,
  photos: (activityId: string) =>
    ["activities", "photos", activityId] as const,
};

export function useActivities(params?: {
  schoolId?: string;
  academicYearId?: string;
  status?: ActivityStatus;
}) {
  const query = buildQuery({
    school_id: params?.schoolId,
    academic_year_id: params?.academicYearId,
    status: params?.status,
  });

  return useQuery({
    queryKey: activityKeys.list(
      params?.schoolId,
      params?.academicYearId,
      params?.status,
    ),
    queryFn: async () =>
      normalizeList<ActivityRecord>(
        await apiFetch(`/activities${query}`),
      ),
  });
}

export function useActivity(activityId?: string) {
  return useQuery({
    queryKey: activityId
      ? activityKeys.detail(activityId)
      : ["activities", "detail", "empty"],
    queryFn: () =>
      apiFetch<ActivityRecord>(`/activities/${activityId}`),
    enabled: Boolean(activityId),
  });
}

export function useActivityPhotos(activityId?: string) {
  return useQuery({
    queryKey: activityId
      ? activityKeys.photos(activityId)
      : ["activities", "photos", "empty"],
    queryFn: async () =>
      normalizeList<ActivityPhotoRecord>(
        await apiFetch(`/activities/${activityId}/photos`),
      ),
    enabled: Boolean(activityId),
  });
}

export function useCreateActivity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ActivityCreatePayload) =>
      apiFetch<ActivityRecord>("/activities", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: activityKeys.all,
      });
    },
  });
}

export function useUpdateActivity(activityId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ActivityUpdatePayload) =>
      apiFetch<ActivityRecord>(`/activities/${activityId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: (activity) => {
      queryClient.setQueryData(
        activityKeys.detail(activity.id),
        activity,
      );

      queryClient.invalidateQueries({
        queryKey: activityKeys.all,
      });
    },
  });
}

function createLifecycleMutation(
  activityId: string,
  action: "submit" | "approve" | "publish",
) {
  return {
    mutationFn: () =>
      apiFetch<ActivityRecord>(
        `/activities/${activityId}/${action}`,
        {
          method: "POST",
        },
      ),
  };
}

export function useSubmitActivity(activityId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    ...createLifecycleMutation(activityId, "submit"),
    onSuccess: (activity) => {
      queryClient.setQueryData(
        activityKeys.detail(activity.id),
        activity,
      );
      queryClient.invalidateQueries({
        queryKey: activityKeys.all,
      });
    },
  });
}

export function useApproveActivity(activityId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    ...createLifecycleMutation(activityId, "approve"),
    onSuccess: (activity) => {
      queryClient.setQueryData(
        activityKeys.detail(activity.id),
        activity,
      );
      queryClient.invalidateQueries({
        queryKey: activityKeys.all,
      });
    },
  });
}

export function usePublishActivity(activityId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    ...createLifecycleMutation(activityId, "publish"),
    onSuccess: (activity) => {
      queryClient.setQueryData(
        activityKeys.detail(activity.id),
        activity,
      );
      queryClient.invalidateQueries({
        queryKey: activityKeys.all,
      });
    },
  });
}

export function useRejectActivity(activityId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reason: string) =>
      apiFetch<ActivityRecord>(
        `/activities/${activityId}/reject`,
        {
          method: "POST",
          body: JSON.stringify({ reason }),
        },
      ),
    onSuccess: (activity) => {
      queryClient.setQueryData(
        activityKeys.detail(activity.id),
        activity,
      );
      queryClient.invalidateQueries({
        queryKey: activityKeys.all,
      });
    },
  });
}

export function useAddActivityPhoto(activityId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ActivityPhotoCreatePayload) =>
      apiFetch<ActivityPhotoRecord>(
        `/activities/${activityId}/photos`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: activityKeys.photos(activityId),
      });
    },
  });
}

export function useDeleteActivityPhoto(activityId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (photoId: string) =>
      apiFetch<void>(
        `/activities/${activityId}/photos/${photoId}`,
        {
          method: "DELETE",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: activityKeys.photos(activityId),
      });
    },
  });
}
