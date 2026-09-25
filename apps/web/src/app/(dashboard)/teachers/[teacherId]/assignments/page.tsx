"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import {
  ArrowLeft,
  BriefcaseBusiness,
  Edit3,
  Loader2,
  Plus,
  Power,
  Save,
  X,
} from "lucide-react";

import {
  useAcademicYears,
  useClasses,
} from "@/hooks/use-academic-structure";

import {
  useCreateTeacherAssignment,
  useDeactivateTeacherAssignment,
  useTeacher,
  useTeacherAssignments,
  useUpdateTeacherAssignment,
} from "@/hooks/use-teachers";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

function statusClass(status: string) {
  return status === "ACTIVE"
    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
    : "border-slate-200 bg-slate-100 text-slate-600";
}

function classLabel(
  name: string,
  gradeLevel: number,
  section?: string | null,
) {
  return [
    name,
    gradeLevel ? `Grade ${gradeLevel}` : "",
    section ? `Section ${section}` : "",
  ]
    .filter(Boolean)
    .join(" • ");
}

export default function TeacherAssignmentsPage() {
  const params = useParams<{ teacherId: string }>();
  const teacherId = params.teacherId;

  const teacher = useTeacher(teacherId);
  const record = teacher.data;

  const years = useAcademicYears();

  const assignments = useTeacherAssignments({
    teacherId,
    schoolId: record?.school_id,
    includeInactive: true,
  });

  const create = useCreateTeacherAssignment();

  const [editingId, setEditingId] = useState<string | null>(null);

  const update = useUpdateTeacherAssignment(
    editingId ?? "",
  );

  const deactivate = useDeactivateTeacherAssignment();

  const [academicYearId, setAcademicYearId] = useState("");
  const [classId, setClassId] = useState("");
  const [subject, setSubject] = useState("");
  const [startDate, setStartDate] = useState(todayString());
  const [endDate, setEndDate] = useState("");

  const classes = useClasses({
    school_id: record?.school_id,
    academic_year_id:
      academicYearId || undefined,
  });

  const activeYears = useMemo(
    () =>
      (years.data ?? []).filter(
        (year) => year.is_active,
      ),
    [years.data],
  );

  const resetForm = () => {
    setEditingId(null);
    setAcademicYearId("");
    setClassId("");
    setSubject("");
    setStartDate(todayString());
    setEndDate("");
  };

  const beginEdit = (
    assignment: NonNullable<
      typeof assignments.data
    >[number],
  ) => {
    setEditingId(assignment.id);
    setAcademicYearId(
      assignment.academic_year_id,
    );
    setClassId(
      assignment.class_id ?? "",
    );
    setSubject(
      assignment.subject ?? "",
    );
    setStartDate(
      assignment.start_date,
    );
    setEndDate(
      assignment.end_date ?? "",
    );
  };

  const saveAssignment = async () => {
    if (
      !record ||
      !academicYearId ||
      !startDate
    ) {
      return;
    }

    if (
      endDate &&
      endDate < startDate
    ) {
      return;
    }

    if (editingId) {
      await update.mutateAsync({
        class_id:
          classId || null,
        subject:
          subject.trim() || null,
        start_date:
          startDate,
        end_date:
          endDate || null,
      });
    } else {
      await create.mutateAsync({
        teacher_id:
          teacherId,
        school_id:
          record.school_id,
        academic_year_id:
          academicYearId,
        class_id:
          classId || null,
        subject:
          subject.trim() || null,
        start_date:
          startDate,
        end_date:
          endDate || null,
      });
    }

    resetForm();
  };

  if (teacher.isLoading) {
    return (
      <div className="flex min-h-[500px] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-[#27348B]" />
      </div>
    );
  }

  if (
    teacher.isError ||
    !record
  ) {
    return (
      <div className="mx-auto max-w-4xl rounded-3xl border border-red-100 bg-red-50 p-10 text-center">
        <p className="font-bold text-red-800">
          Teacher could not be loaded.
        </p>

        <Link
          href="/teachers"
          className="mt-5 inline-flex rounded-xl bg-[#27348B] px-4 py-2.5 text-sm font-bold text-white"
        >
          Back to teachers
        </Link>
      </div>
    );
  }

  const mutationError =
    create.error ??
    update.error ??
    deactivate.error;

  return (
    <div className="mx-auto max-w-[1450px]">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link
          href={`/teachers/${teacherId}`}
          className="inline-flex items-center gap-2 text-xs font-bold text-[#27348B]"
        >
          <ArrowLeft className="size-4" />
          Back to teacher profile
        </Link>

        <div className="text-right">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
            Teacher assignments
          </p>

          <p className="mt-1 text-sm font-bold text-slate-800">
            {record.first_name}{" "}
            {record.last_name ?? ""}
          </p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <Card className="h-fit border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              {editingId ? (
                <Edit3 className="size-4 text-[#27348B]" />
              ) : (
                <Plus className="size-4 text-[#27348B]" />
              )}

              {editingId
                ? "Edit assignment"
                : "Add assignment"}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="rounded-2xl bg-[#27348B]/5 p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Teacher
              </p>

              <p className="mt-1 font-semibold text-slate-800">
                {record.first_name}{" "}
                {record.middle_name ?? ""}{" "}
                {record.last_name ?? ""}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                ID: {record.teacher_id}
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-500">
                Academic year
              </label>

              <select
                value={academicYearId}
                onChange={(event) => {
                  setAcademicYearId(
                    event.target.value,
                  );
                  setClassId("");
                }}
                disabled={Boolean(editingId)}
                className="flex h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-[#27348B]"
              >
                <option value="">
                  Select academic year
                </option>

                {activeYears.map((year) => (
                  <option
                    key={year.id}
                    value={year.id}
                  >
                    {year.name}
                    {year.is_current
                      ? " • Current"
                      : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-500">
                Class
              </label>

              <select
                value={classId}
                onChange={(event) =>
                  setClassId(
                    event.target.value,
                  )
                }
                disabled={!academicYearId}
                className="flex h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-[#27348B] disabled:bg-slate-50"
              >
                <option value="">
                  No class / school-wide assignment
                </option>

                {(classes.data ?? [])
                  .filter(
                    (item) =>
                      item.is_active,
                  )
                  .map((item) => (
                    <option
                      key={item.id}
                      value={item.id}
                    >
                      {classLabel(
                        item.name,
                        item.grade_level,
                        item.section,
                      )}
                    </option>
                  ))}
              </select>

              {!academicYearId && (
                <p className="text-[11px] text-slate-400">
                  Select an academic year to
                  load its classes.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-500">
                Subject
              </label>

              <Input
                value={subject}
                maxLength={100}
                onChange={(event) =>
                  setSubject(
                    event.target.value,
                  )
                }
                placeholder="Mathematics"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Start date
                </label>

                <Input
                  type="date"
                  value={startDate}
                  onChange={(event) =>
                    setStartDate(
                      event.target.value,
                    )
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  End date
                </label>

                <Input
                  type="date"
                  value={endDate}
                  min={startDate}
                  onChange={(event) =>
                    setEndDate(
                      event.target.value,
                    )
                  }
                />
              </div>
            </div>

            {endDate &&
              endDate < startDate && (
                <p className="rounded-xl border border-red-100 bg-red-50 p-3 text-xs text-red-700">
                  End date cannot be earlier
                  than the start date.
                </p>
              )}

            {mutationError && (
              <p className="rounded-xl border border-red-100 bg-red-50 p-3 text-xs text-red-700">
                {mutationError instanceof Error
                  ? mutationError.message
                  : "The assignment request failed."}
              </p>
            )}

            <div className="flex flex-wrap justify-end gap-2">
              {editingId && (
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-xl"
                  onClick={resetForm}
                >
                  <X className="mr-2 size-4" />
                  Cancel
                </Button>
              )}

              <Button
                type="button"
                disabled={
                  create.isPending ||
                  update.isPending ||
                  !academicYearId ||
                  !startDate ||
                  Boolean(
                    endDate &&
                    endDate < startDate,
                  )
                }
                className="rounded-xl bg-[#27348B] hover:bg-[#202c78]"
                onClick={saveAssignment}
              >
                {create.isPending ||
                update.isPending ? (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                ) : editingId ? (
                  <Save className="mr-2 size-4" />
                ) : (
                  <Plus className="mr-2 size-4" />
                )}

                {editingId
                  ? "Save assignment"
                  : "Add assignment"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <BriefcaseBusiness className="size-4 text-[#27348B]" />
                Assignment history
              </CardTitle>

              <Badge
                variant="outline"
                className="rounded-full"
              >
                {assignments.data?.length ?? 0} records
              </Badge>
            </div>
          </CardHeader>

          <CardContent>
            {assignments.isLoading ? (
              <div className="flex items-center justify-center p-10">
                <Loader2 className="size-6 animate-spin text-[#27348B]" />
              </div>
            ) : assignments.isError ? (
              <div className="rounded-2xl border border-red-100 bg-red-50 p-5 text-sm text-red-700">
                {assignments.error instanceof Error
                  ? assignments.error.message
                  : "Unable to load assignments."}
              </div>
            ) : assignments.data?.length ? (
              <div className="space-y-3">
                {assignments.data.map(
                  (assignment) => {
                    const year =
                      years.data?.find(
                        (item) =>
                          item.id ===
                          assignment.academic_year_id,
                      );

                    const classRecord =
                      (classes.data ?? []).find(
                        (item) =>
                          item.id ===
                          assignment.class_id,
                      );

                    return (
                      <div
                        key={assignment.id}
                        className="rounded-2xl border border-slate-100 bg-white/80 p-4 transition hover:border-[#27348B]/20"
                      >
                        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <h3 className="font-bold text-slate-800">
                                {assignment.subject ||
                                  "General assignment"}
                              </h3>

                              <Badge
                                variant="outline"
                                className={`rounded-full ${statusClass(
                                  assignment.status,
                                )}`}
                              >
                                {assignment.status}
                              </Badge>
                            </div>

                            <p className="mt-2 text-sm text-slate-600">
                              {year?.name ??
                                assignment.academic_year_id}
                            </p>

                            <p className="mt-1 text-xs text-slate-500">
                              {classRecord
                                ? classLabel(
                                    classRecord.name,
                                    classRecord.grade_level,
                                    classRecord.section,
                                  )
                                : assignment.class_id
                                  ? `Class: ${assignment.class_id}`
                                  : "School-wide assignment"}
                            </p>

                            <p className="mt-2 text-xs text-slate-400">
                              {assignment.start_date}
                              {" → "}
                              {assignment.end_date ??
                                "Current"}
                            </p>
                          </div>

                          <div className="flex shrink-0 gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              className="rounded-xl"
                              onClick={() =>
                                beginEdit(
                                  assignment,
                                )
                              }
                              disabled={
                                assignment.status !==
                                "ACTIVE"
                              }
                            >
                              <Edit3 className="mr-1.5 size-3.5" />
                              Edit
                            </Button>

                            {assignment.status ===
                              "ACTIVE" && (
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                className="rounded-xl text-red-600 hover:text-red-700"
                                disabled={
                                  deactivate.isPending
                                }
                                onClick={() => {
                                  if (
                                    window.confirm(
                                      "Deactivate this teacher assignment?",
                                    )
                                  ) {
                                    deactivate.mutate(
                                      assignment.id,
                                    );
                                  }
                                }}
                              >
                                {deactivate.isPending ? (
                                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                                ) : (
                                  <Power className="mr-1.5 size-3.5" />
                                )}
                                Deactivate
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  },
                )}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 p-10 text-center">
                <BriefcaseBusiness className="mx-auto size-8 text-slate-300" />

                <p className="mt-3 font-semibold text-slate-600">
                  No assignments yet
                </p>

                <p className="mt-1 text-xs text-slate-400">
                  Create the first school, class,
                  or subject assignment for this
                  teacher.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

