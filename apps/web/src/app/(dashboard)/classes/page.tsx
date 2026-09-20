"use client";

import {
  Plus,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";

import {
  useAcademicYears,
  useClasses,
  useCreateClass,
  useSchoolList,
} from "@/hooks/use-academic-structure";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
} from "@/components/ui/card";

export default function ClassesPage() {
  const [schoolId, setSchoolId] =
    useState("");

  const [yearId, setYearId] =
    useState("");

  const [name, setName] =
    useState("");

  const [gradeLevel, setGradeLevel] =
    useState("");

  const [section, setSection] =
    useState("");

  const schools =
    useSchoolList();

  const years =
    useAcademicYears();

  const classes =
    useClasses({
      school_id:
        schoolId || undefined,
      academic_year_id:
        yearId || undefined,
    });

  const create =
    useCreateClass();

  const filteredYears =
    useMemo(
      () =>
        years.data ?? [],
      [years.data],
    );

  async function submit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    await create.mutateAsync({
      school_id: schoolId,
      academic_year_id: yearId,
      name: name.trim(),
      grade_level:
        Number(gradeLevel),
      section:
        section.trim() || null,
    });

    setName("");
    setGradeLevel("");
    setSection("");
  }

  return (
    <div className="mx-auto max-w-[1400px]">
      <div className="mb-7">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#27348B]/60">
          Academic management
        </p>

        <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-900">
          Classes
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Organize classes by school and academic year.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
                <Plus className="size-5" />
              </div>

              <div>
                <p className="font-bold text-slate-900">
                  Create class
                </p>

                <p className="text-xs text-slate-500">
                  Add a class to an academic year.
                </p>
              </div>
            </div>

            <form
              onSubmit={submit}
              className="mt-6 space-y-4"
            >
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  School
                </label>

                <select
                  value={schoolId}
                  onChange={(event) =>
                    setSchoolId(
                      event.target.value,
                    )
                  }
                  required
                  className="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                >
                  <option value="">
                    Select school
                  </option>

                  {(
                    schools.data ?? []
                  ).map((school) => (
                    <option
                      key={school.id}
                      value={school.id}
                    >
                      {school.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Academic year
                </label>

                <select
                  value={yearId}
                  onChange={(event) =>
                    setYearId(
                      event.target.value,
                    )
                  }
                  required
                  className="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                >
                  <option value="">
                    Select academic year
                  </option>

                  {filteredYears.map(
                    (year) => (
                      <option
                        key={year.id}
                        value={year.id}
                      >
                        {year.name}
                        {year.is_current
                          ? " • Current"
                          : ""}
                      </option>
                    ),
                  )}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Class name
                </label>

                <Input
                  value={name}
                  onChange={(event) =>
                    setName(
                      event.target.value,
                    )
                  }
                  placeholder="Grade 5"
                  required
                  className="rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                    Grade level
                  </label>

                  <Input
                    type="number"
                    min="1"
                    max="12"
                    value={gradeLevel}
                    onChange={(event) =>
                      setGradeLevel(
                        event.target.value,
                      )
                    }
                    required
                    className="rounded-xl"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                    Section
                  </label>

                  <Input
                    value={section}
                    onChange={(event) =>
                      setSection(
                        event.target.value,
                      )
                    }
                    placeholder="A"
                    className="rounded-xl"
                  />
                </div>
              </div>

              {create.isError && (
                <div className="rounded-xl bg-red-50 p-3 text-xs text-red-700">
                  {create.error instanceof Error
                    ? create.error.message
                    : "Class creation failed."}
                </div>
              )}

              <Button
                type="submit"
                disabled={
                  create.isPending
                }
                className="w-full rounded-xl bg-[#27348B] hover:bg-[#202c78]"
              >
                Create class
              </Button>
            </form>
          </CardContent>
        </Card>

        <div>
          <div className="mb-4 flex flex-col gap-3 sm:flex-row">
            <select
              value={schoolId}
              onChange={(event) =>
                setSchoolId(
                  event.target.value,
                )
              }
              className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm"
            >
              <option value="">
                All schools
              </option>

              {(schools.data ?? []).map(
                (school) => (
                  <option
                    key={school.id}
                    value={school.id}
                  >
                    {school.name}
                  </option>
                ),
              )}
            </select>

            <select
              value={yearId}
              onChange={(event) =>
                setYearId(
                  event.target.value,
                )
              }
              className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm"
            >
              <option value="">
                All academic years
              </option>

              {filteredYears.map(
                (year) => (
                  <option
                    key={year.id}
                    value={year.id}
                  >
                    {year.name}
                  </option>
                ),
              )}
            </select>
          </div>

          <div className="space-y-3">
            {classes.isLoading && (
              <Card className="border-white/50 bg-white/70">
                <CardContent className="p-8 text-center text-sm text-slate-500">
                  Loading classes...
                </CardContent>
              </Card>
            )}

            {!classes.isLoading &&
              (classes.data ?? [])
                .length === 0 && (
                <Card className="border-dashed border-slate-200 bg-white/60">
                  <CardContent className="p-12 text-center">
                    <Users className="mx-auto size-9 text-[#27348B]/40" />
                    <p className="mt-4 font-bold text-slate-800">
                      No classes found
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Create a class or change the filters.
                    </p>
                  </CardContent>
                </Card>
              )}

            {(classes.data ?? []).map(
              (item) => (
                <Card
                  key={item.id}
                  className="border-white/50 bg-white/70 shadow-lg backdrop-blur-xl"
                >
                  <CardContent className="p-5">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex size-11 items-center justify-center rounded-2xl bg-[#27348B]/10 font-black text-[#27348B]">
                          {item.grade_level}
                        </div>

                        <div>
                          <p className="font-black text-slate-900">
                            {item.name}
                            {item.section
                              ? ` • ${item.section}`
                              : ""}
                          </p>

                          <p className="text-xs text-slate-500">
                            Grade {item.grade_level}
                          </p>
                        </div>
                      </div>

                      <span
                        className={[
                          "rounded-full px-2.5 py-1 text-[10px] font-bold",
                          item.is_active
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-slate-100 text-slate-500",
                        ].join(" ")}
                      >
                        {item.is_active
                          ? "ACTIVE"
                          : "INACTIVE"}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ),
            )}
          </div>
        </div>
      </div>
    </div>
  );
}