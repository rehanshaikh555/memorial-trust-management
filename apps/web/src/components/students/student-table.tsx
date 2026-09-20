"use client";

import { Search, Users, Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import type { Student } from "@/types";
import { displayName } from "@/types";

interface StudentTableProps {
  students: Student[];
  loading?: boolean;
}

export function StudentTable({
  students,
  loading,
}: StudentTableProps) {
  const [search, setSearch] =
    useState("");

  const filtered = useMemo(() => {
    const term =
      search.trim().toLowerCase();

    if (!term) return students;

    return students.filter((student) =>
      [
        student.student_id,
        displayName(student),
        student.gender,
        student.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(term),
    );
  }, [students, search]);

  return (
    <div className="glass overflow-hidden rounded-2xl">
      <div className="border-b border-slate-100 p-4 md:p-5">
        <div className="relative max-w-md">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search students..."
            className="h-11 w-full rounded-xl border border-slate-200 bg-white/70 pl-10 pr-4 text-sm outline-none transition focus:border-[#27348B] focus:ring-4 focus:ring-[#27348B]/10"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex min-h-[280px] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-[#27348B]" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex min-h-[280px] flex-col items-center justify-center px-6 text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#edf0ff] text-[#27348B]">
            <Users className="h-5 w-5" />
          </div>
          <div className="font-semibold text-slate-700">
            No students found
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Try changing your search.
          </div>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] uppercase tracking-wide text-slate-400">
                <th className="px-5 py-3 font-semibold">
                  Student
                </th>
                <th className="px-5 py-3 font-semibold">
                  ID
                </th>
                <th className="px-5 py-3 font-semibold">
                  Gender
                </th>
                <th className="px-5 py-3 font-semibold">
                  Status
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {filtered.map((student) => (
                <tr
                  key={student.id}
                  className="transition hover:bg-[#f8f9ff]"
                >
                  <td className="px-5 py-4">
                    <div className="font-semibold text-slate-800">
                      {displayName(student)}
                    </div>
                  </td>

                  <td className="px-5 py-4 text-slate-500">
                    {student.student_id ??
                      "—"}
                  </td>

                  <td className="px-5 py-4 text-slate-500">
                    {student.gender ?? "—"}
                  </td>

                  <td className="px-5 py-4">
                    <span className="rounded-full bg-[#edf0ff] px-2.5 py-1 text-[10px] font-bold text-[#27348B]">
                      {student.status ??
                        "UNKNOWN"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
