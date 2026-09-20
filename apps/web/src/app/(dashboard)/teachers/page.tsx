"use client";

import {
  AlertCircle,
  GraduationCap,
  Mail,
  Phone,
  Search,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  displayName,
} from "@/types";
import { useTeachers } from "@/hooks/use-resources";

export default function TeachersPage() {
  const {
    data = [],
    isLoading,
    isError,
    error,
  } = useTeachers();

  const [search, setSearch] =
    useState("");

  const teachers = useMemo(() => {
    const term =
      search.trim().toLowerCase();

    if (!term) return data;

    return data.filter((teacher) =>
      [
        teacher.teacher_id,
        displayName(teacher),
        teacher.email,
        teacher.phone,
        teacher.qualification,
        teacher.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(term),
    );
  }, [data, search]);

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#27348B]">
            Staff management
          </div>

          <h1 className="text-2xl font-bold text-slate-900 md:text-3xl">
            Teachers
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Review teaching staff, approval status and assignments.
          </p>
        </div>

        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search teachers..."
            className="h-11 w-full rounded-xl border border-slate-200 bg-white/70 pl-10 pr-4 text-sm outline-none focus:border-[#27348B] focus:ring-4 focus:ring-[#27348B]/10"
          />
        </div>
      </div>

      {isError ? (
        <div className="glass rounded-2xl p-8 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-rose-500" />
          <h2 className="mt-3 font-semibold text-slate-800">
            Unable to load teachers
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {error instanceof Error
              ? error.message
              : "The API request failed."}
          </p>
        </div>
      ) : isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map(
            (item) => (
              <div
                key={item}
                className="glass h-48 animate-pulse rounded-2xl"
              />
            ),
          )}
        </div>
      ) : teachers.length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center">
          <Users className="mx-auto h-9 w-9 text-slate-300" />
          <h2 className="mt-4 font-semibold text-slate-800">
            No teachers found
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            No teachers match the current search.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {teachers.map((teacher) => (
            <div
              key={teacher.id}
              className="glass rounded-2xl p-5 transition hover:-translate-y-1"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#edf0ff] text-[#27348B]">
                  <Users className="h-6 w-6" />
                </div>

                <span
                  className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${
                    teacher.status === "ACTIVE"
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-amber-50 text-amber-600"
                  }`}
                >
                  {teacher.status ??
                    "UNKNOWN"}
                </span>
              </div>

              <h2 className="mt-5 font-semibold text-slate-900">
                {displayName(teacher)}
              </h2>

              <p className="mt-1 text-xs font-medium text-[#27348B]">
                {teacher.teacher_id ??
                  "Teacher ID unavailable"}
              </p>

              <div className="mt-5 space-y-2 text-xs text-slate-500">
                {teacher.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-3.5 w-3.5" />
                    <span className="truncate">
                      {teacher.email}
                    </span>
                  </div>
                )}

                {teacher.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-3.5 w-3.5" />
                    <span>
                      {teacher.phone}
                    </span>
                  </div>
                )}

                {teacher.qualification && (
                  <div className="flex items-center gap-2">
                    <GraduationCap className="h-3.5 w-3.5" />
                    <span className="truncate">
                      {teacher.qualification}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
