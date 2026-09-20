"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import {
  normalizeCollection,
  type School,
  type Student,
  type Teacher,
} from "@/types";

export function useSchools() {
  return useQuery({
    queryKey: ["schools"],
    queryFn: async () => {
      const response =
        await apiFetch<unknown>("/schools");

      return normalizeCollection<School>(
        response,
      );
    },
  });
}

export function useStudents() {
  return useQuery({
    queryKey: ["students"],
    queryFn: async () => {
      const response =
        await apiFetch<unknown>("/students");

      return normalizeCollection<Student>(
        response,
      );
    },
  });
}

export function useTeachers() {
  return useQuery({
    queryKey: ["teachers"],
    queryFn: async () => {
      const response =
        await apiFetch<unknown>("/teachers");

      return normalizeCollection<Teacher>(
        response,
      );
    },
  });
}
