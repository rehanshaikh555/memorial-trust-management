"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useUnreadNotificationCount(
  enabled = true,
) {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: async () => {
      const data = await apiFetch<unknown>(
        "/notifications/unread-count",
      );

      if (
        typeof data === "number"
      ) {
        return data;
      }

      if (
        typeof data === "object" &&
        data !== null
      ) {
        const record =
          data as Record<string, unknown>;

        for (const key of [
          "count",
          "unread_count",
          "unreadCount",
        ]) {
          if (
            typeof record[key] === "number"
          ) {
            return record[key];
          }
        }
      }

      return 0;
    },
    enabled,
    refetchInterval: 30_000,
  });
}