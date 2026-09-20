"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Eye,
  GraduationCap,
  Plus,
  Search,
  Users,
} from "lucide-react";
import { motion } from "framer-motion";

import {
  useStudents,
} from "@/hooks/use-students";
import {
  useSchools,
} from "@/hooks/use-resources";
import { StudentStatus } from "@/components/students/student-status";
import {
  Button,
} from "@/components/ui/button";
import {
  Input,
} from "@/components/ui/input";

export default function StudentsPage() {
  const [search, setSearch] =
    useState("");

  const students =
    useStudents();

  const schools =
    useSchools();

  const filtered = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    if (!query) {
      return students.data ?? [];
    }

    return (students.data ?? []).filter(
      (student) =>
        [
          student.student_id,
          student.first_name,
          student.middle_name,
          student.last_name,
          student.email,
          student.phone,
          student.status,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(query),
    );
  }, [students.data, search]);

  return (
    <div className="mx-auto max-w-[1600px]">
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#27348B]/60">
            Student management
          </p>

          <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-900">
            Students
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Manage admissions, student records,
            documents and lifecycle workflows.
          </p>
        </div>

        <Link href="/students/new">
          <Button className="rounded-xl bg-[#27348B] shadow-lg shadow-[#27348B]/20 hover:bg-[#202c78]">
            <Plus className="mr-2 size-4" />
            Add student
          </Button>
        </Link>
      </div>

      <div className="mb-5 rounded-3xl border border-white/50 bg-white/70 p-4 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full max-w-xl">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

            <Input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search by student ID, name, email or phone..."
              className="h-11 rounded-xl border-slate-200 bg-white/80 pl-10"
            />
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Users className="size-4 text-[#27348B]" />
            {filtered.length} visible students
          </div>
        </div>
      </div>

      {students.isLoading && (
        <div className="rounded-3xl border border-white/50 bg-white/70 p-12 text-center shadow-xl backdrop-blur-xl">
          <p className="text-sm font-medium text-slate-600">
            Loading students...
          </p>
        </div>
      )}

      {students.isError && (
        <div className="rounded-3xl border border-red-100 bg-red-50 p-8 text-center">
          <p className="font-bold text-red-700">
            Unable to load students
          </p>
          <p className="mt-1 text-sm text-red-600">
            {students.error instanceof Error
              ? students.error.message
              : "The API request failed."}
          </p>
        </div>
      )}

      {!students.isLoading &&
        !students.isError &&
        filtered.length === 0 && (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-white/60 p-16 text-center backdrop-blur-xl">
            <GraduationCap className="mx-auto size-10 text-[#27348B]/40" />
            <p className="mt-4 font-bold text-slate-800">
              No students found
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Try another search or create a new
              student record.
            </p>
          </div>
        )}

      {filtered.length > 0 && (
        <div className="overflow-hidden rounded-3xl border border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead>
                <tr className="border-b border-slate-100 bg-white/60 text-left">
                  <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Student
                  </th>

                  <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Student ID
                  </th>

                  <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Status
                  </th>

                  <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Contact
                  </th>

                  <th className="px-5 py-4 text-right text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Action
                  </th>
                </tr>
              </thead>

              <tbody>
                {filtered.map(
                  (student, index) => (
                    <motion.tr
                      key={student.id}
                      initial={{
                        opacity: 0,
                      }}
                      animate={{
                        opacity: 1,
                      }}
                      transition={{
                        delay:
                          index * 0.025,
                      }}
                      className="border-b border-slate-100/80 transition hover:bg-white/70"
                    >
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[#27348B]/10 font-bold text-[#27348B]">
                            {student.first_name
                              ?.charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <p className="font-semibold text-slate-800">
                              {[
                                student.first_name,
                                student.middle_name,
                                student.last_name,
                              ]
                                .filter(
                                  Boolean,
                                )
                                .join(" ")}
                            </p>

                            <p className="text-xs text-slate-400">
                              {student.email ||
                                "No email"}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-sm font-medium text-slate-600">
                        {student.student_id}
                      </td>

                      <td className="px-5 py-4">
                        <StudentStatus
                          status={
                            student.status
                          }
                        />
                      </td>

                      <td className="px-5 py-4 text-sm text-slate-500">
                        {student.phone ||
                          "—"}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/students/${student.id}`}
                          className="inline-flex items-center gap-2 rounded-xl bg-[#27348B]/5 px-3 py-2 text-xs font-bold text-[#27348B] transition hover:bg-[#27348B]/10"
                        >
                          <Eye className="size-3.5" />
                          View
                        </Link>
                      </td>
                    </motion.tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {schools.isLoading && (
        <p className="mt-4 text-xs text-slate-400">
          Loading school context...
        </p>
      )}
    </div>
  );
}