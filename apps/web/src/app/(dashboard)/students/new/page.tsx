"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowLeft,
  GraduationCap,
  Loader2,
  UserPlus,
} from "lucide-react";
import { useRouter } from "next/navigation";

import {
  useAcademicYears,
  useClasses,
  useSchoolList,
} from "@/hooks/use-academic-structure";

import {
  useCreateStudent,
} from "@/hooks/use-students";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function NewStudentPage() {
  const router = useRouter();

  const schools =
    useSchoolList();

  const academicYears =
    useAcademicYears();

  const createStudent =
    useCreateStudent();

  const [schoolId, setSchoolId] =
    useState("");

  const [academicYearId, setAcademicYearId] =
    useState("");

  const [classId, setClassId] =
    useState("");

  const [form, setForm] =
    useState({
      student_id: "",
      first_name: "",
      middle_name: "",
      last_name: "",
      date_of_birth: "",
      gender: "",
      phone: "",
      email: "",
      address: "",
      enrollment_date:
        new Date()
          .toISOString()
          .slice(0, 10),
    });

  const classes =
    useClasses({
      school_id:
        schoolId || undefined,
      academic_year_id:
        academicYearId || undefined,
    });

  const availableClasses =
    useMemo(() => {
      if (
        !schoolId ||
        !academicYearId
      ) {
        return [];
      }

      return (
        classes.data ?? []
      ).filter(
        (item) =>
          item.school_id ===
            schoolId &&
          item.academic_year_id ===
            academicYearId &&
          item.is_active,
      );
    }, [
      classes.data,
      schoolId,
      academicYearId,
    ]);

  function update(
    key: keyof typeof form,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function handleSchoolChange(
    value: string,
  ) {
    setSchoolId(value);
    setAcademicYearId("");
    setClassId("");
  }

  function handleAcademicYearChange(
    value: string,
  ) {
    setAcademicYearId(value);
    setClassId("");
  }

  async function submit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    if (!schoolId) {
      return;
    }

    if (!academicYearId) {
      return;
    }

    if (!classId) {
      return;
    }

    try {
      const student =
        await createStudent.mutateAsync({
          student_id:
            form.student_id.trim(),
          first_name:
            form.first_name.trim(),
          middle_name:
            form.middle_name.trim() ||
            null,
          last_name:
            form.last_name.trim(),
          date_of_birth:
            form.date_of_birth,
          gender:
            form.gender.trim() ||
            null,
          phone:
            form.phone.trim() ||
            null,
          email:
            form.email.trim() ||
            null,
          address:
            form.address.trim() ||
            null,
          school_id:
            schoolId,
          academic_year_id:
            academicYearId,
          class_id:
            classId,
          enrollment_date:
            form.enrollment_date,
          guardians: [],
        });

      router.push(
        `/students/${student.id}`,
      );
    } catch {
      // Error rendered below.
    }
  }

  const canSubmit =
    Boolean(
      form.student_id.trim() &&
      form.first_name.trim() &&
      form.last_name.trim() &&
      form.date_of_birth &&
      form.enrollment_date &&
      schoolId &&
      academicYearId &&
      classId,
    );

  return (
    <div className="mx-auto max-w-5xl">
      <Link
        href="/students"
        className="mb-6 inline-flex items-center gap-2 text-xs font-bold text-[#27348B]"
      >
        <ArrowLeft className="size-4" />
        Back to students
      </Link>

      <div className="mb-7">
        <div className="flex items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
            <UserPlus className="size-6" />
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#27348B]/60">
              Student management
            </p>

            <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-900">
              Add student
            </h1>
          </div>
        </div>

        <p className="mt-3 text-sm text-slate-500">
          Create the student&apos;s permanent identity and initial enrollment.
        </p>
      </div>

      <form
        onSubmit={submit}
        className="space-y-6"
      >
        <Card className="border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base">
              Student identity
            </CardTitle>
          </CardHeader>

          <CardContent>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Student ID
                </label>

                <Input
                  value={form.student_id}
                  onChange={(event) =>
                    update(
                      "student_id",
                      event.target.value,
                    )
                  }
                  placeholder="STU-2026-001"
                  required
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  First name
                </label>

                <Input
                  value={form.first_name}
                  onChange={(event) =>
                    update(
                      "first_name",
                      event.target.value,
                    )
                  }
                  required
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Last name
                </label>

                <Input
                  value={form.last_name}
                  onChange={(event) =>
                    update(
                      "last_name",
                      event.target.value,
                    )
                  }
                  required
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Middle name
                </label>

                <Input
                  value={form.middle_name}
                  onChange={(event) =>
                    update(
                      "middle_name",
                      event.target.value,
                    )
                  }
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Date of birth
                </label>

                <Input
                  type="date"
                  value={
                    form.date_of_birth
                  }
                  onChange={(event) =>
                    update(
                      "date_of_birth",
                      event.target.value,
                    )
                  }
                  required
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Gender
                </label>

                <select
                  value={form.gender}
                  onChange={(event) =>
                    update(
                      "gender",
                      event.target.value,
                    )
                  }
                  className="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                >
                  <option value="">
                    Select gender
                  </option>
                  <option value="MALE">
                    Male
                  </option>
                  <option value="FEMALE">
                    Female
                  </option>
                  <option value="OTHER">
                    Other
                  </option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-base">
              Contact information
            </CardTitle>
          </CardHeader>

          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Phone
                </label>

                <Input
                  value={form.phone}
                  onChange={(event) =>
                    update(
                      "phone",
                      event.target.value,
                    )
                  }
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Email
                </label>

                <Input
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    update(
                      "email",
                      event.target.value,
                    )
                  }
                  className="rounded-xl"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Address
                </label>

                <Input
                  value={form.address}
                  onChange={(event) =>
                    update(
                      "address",
                      event.target.value,
                    )
                  }
                  className="rounded-xl"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-[#27348B]/10 bg-white/80 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-[#27348B]/10 text-[#27348B]">
                <GraduationCap className="size-5" />
              </div>

              <div>
                <CardTitle className="text-base">
                  Initial enrollment
                </CardTitle>

                <p className="mt-1 text-xs text-slate-500">
                  Select the student&apos;s school, academic year and class.
                </p>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  School
                </label>

                <select
                  value={schoolId}
                  onChange={(event) =>
                    handleSchoolChange(
                      event.target.value,
                    )
                  }
                  required
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-[#27348B]"
                >
                  <option value="">
                    Select school
                  </option>

                  {(schools.data ?? [])
                    .filter(
                      (school) =>
                        school.is_active,
                    )
                    .map(
                      (school) => (
                        <option
                          key={school.id}
                          value={school.id}
                        >
                          {school.name} Â·{" "}
                          {school.code}
                        </option>
                      ),
                    )}
                </select>

                {schools.isLoading && (
                  <p className="mt-1.5 text-[11px] text-slate-400">
                    Loading schools...
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Academic year
                </label>

                <select
                  value={
                    academicYearId
                  }
                  onChange={(event) =>
                    handleAcademicYearChange(
                      event.target.value,
                    )
                  }
                  disabled={!schoolId}
                  required
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-[#27348B] disabled:cursor-not-allowed disabled:bg-slate-50"
                >
                  <option value="">
                    {schoolId
                      ? "Select academic year"
                      : "Select school first"}
                  </option>

                  {(academicYears.data ?? [])
                    .filter(
                      (year) =>
                        year.is_active,
                    )
                    .map(
                      (year) => (
                        <option
                          key={year.id}
                          value={year.id}
                        >
                          {year.name}
                          {year.is_current
                            ? " Â· Current"
                            : ""}
                        </option>
                      ),
                    )}
                </select>

                {academicYears.isLoading &&
                  schoolId && (
                    <p className="mt-1.5 text-[11px] text-slate-400">
                      Loading academic years...
                    </p>
                  )}
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Class
                </label>

                <select
                  value={classId}
                  onChange={(event) =>
                    setClassId(
                      event.target.value,
                    )
                  }
                  disabled={
                    !schoolId ||
                    !academicYearId ||
                    classes.isLoading
                  }
                  required
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-[#27348B] disabled:cursor-not-allowed disabled:bg-slate-50"
                >
                  <option value="">
                    {!schoolId
                      ? "Select school first"
                      : !academicYearId
                        ? "Select academic year first"
                        : classes.isLoading
                          ? "Loading classes..."
                          : "Select class"}
                  </option>

                  {availableClasses.map(
                    (item) => (
                      <option
                        key={item.id}
                        value={item.id}
                      >
                        {item.name}
                        {item.section
                          ? ` Â· ${item.section}`
                          : ""}
                      </option>
                    ),
                  )}
                </select>

                {!classes.isLoading &&
                  schoolId &&
                  academicYearId &&
                  availableClasses.length ===
                    0 && (
                    <p className="mt-1.5 text-[11px] text-amber-600">
                      No active classes found for this school and academic year.
                    </p>
                  )}
              </div>

              <div className="md:col-span-3">
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Enrollment date
                </label>

                <Input
                  type="date"
                  value={
                    form.enrollment_date
                  }
                  onChange={(event) =>
                    update(
                      "enrollment_date",
                      event.target.value,
                    )
                  }
                  required
                  className="rounded-xl md:max-w-xs"
                />
              </div>
            </div>

            <div className="mt-5 rounded-2xl bg-[#27348B]/5 p-4">
              <p className="text-xs font-bold text-[#27348B]">
                Enrollment structure
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                The student&apos;s permanent identity remains independent
                from this enrollment. School, academic year and class
                define the student&apos;s current academic placement.
              </p>
            </div>
          </CardContent>
        </Card>

        {createStudent.isError && (
          <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
            <p className="font-bold">
              Student creation failed
            </p>

            <p className="mt-1">
              {createStudent.error instanceof Error
                ? createStudent.error.message
                : "The API request could not be completed."}
            </p>
          </div>
        )}

        <div className="flex justify-end gap-3 border-t border-slate-200/70 pt-5">
          <Link href="/students">
            <Button
              type="button"
              variant="outline"
              className="rounded-xl"
            >
              Cancel
            </Button>
          </Link>

          <Button
            type="submit"
            disabled={
              !canSubmit ||
              createStudent.isPending
            }
            className="rounded-xl bg-[#27348B] px-6 hover:bg-[#202c78]"
          >
            {createStudent.isPending && (
              <Loader2 className="mr-2 size-4 animate-spin" />
            )}

            Create student
          </Button>
        </div>
      </form>
    </div>
  );
}
