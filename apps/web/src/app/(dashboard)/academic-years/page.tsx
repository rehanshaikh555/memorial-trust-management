"use client";

import {
  CalendarDays,
  CheckCircle2,
  Plus,
} from "lucide-react";
import { useMemo, useState } from "react";

import {
  useAcademicYears,
  useCreateAcademicYear,
  useSetCurrentAcademicYear,
  useDeactivateAcademicYear,
  useTrustList,
} from "@/hooks/use-academic-structure";

import { useAuth } from "@/hooks/use-auth";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
} from "@/components/ui/card";

export default function AcademicYearsPage() {
  const { user, loading: authLoading } = useAuth();

  const trusts = useTrustList();

  const years =
    useAcademicYears();

  const create =
    useCreateAcademicYear();

  const setCurrent =
    useSetCurrentAcademicYear();

  const deactivate =
    useDeactivateAcademicYear();

  const [selectedTrustId, setSelectedTrustId] =
    useState("");

  const resolvedTrustId =
    user?.trust_id ?? selectedTrustId;

  const availableTrusts = useMemo(
    () =>
      (trusts.data ?? []).filter(
        (trust) => trust.is_active,
      ),
    [trusts.data],
  );

  const requiresTrustSelection =
    !authLoading && !user?.trust_id;

  const [name, setName] =
    useState("");

  const [startDate, setStartDate] =
    useState("");

  const [endDate, setEndDate] =
    useState("");

  async function submit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    if (!resolvedTrustId) {
      return;
    }

    await create.mutateAsync({
      trust_id: resolvedTrustId,
      name: name.trim(),
      start_date: startDate,
      end_date: endDate,
    });

    setName("");
    setStartDate("");
    setEndDate("");
  }

  return (
    <div className="mx-auto max-w-[1300px]">
      <div className="mb-7">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#27348B]/60">
          Academic management
        </p>

        <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-900">
          Academic Years
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Manage current and historical academic years.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
                <Plus className="size-5" />
              </div>

              <div>
                <p className="font-bold text-slate-900">
                  New academic year
                </p>

                <p className="text-xs text-slate-500">
                  Create a new reporting period.
                </p>
              </div>
            </div>

            <form
              onSubmit={submit}
              className="mt-6 space-y-4"
            >
              {requiresTrustSelection && (
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                    Trust
                  </label>

                  <select
                    value={selectedTrustId}
                    onChange={(event) =>
                      setSelectedTrustId(
                        event.target.value,
                      )
                    }
                    required
                    disabled={trusts.isLoading}
                    className="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-[#27348B]"
                  >
                    <option value="">
                      {trusts.isLoading
                        ? "Loading trusts..."
                        : "Select trust"}
                    </option>

                    {availableTrusts.map(
                      (trust) => (
                        <option
                          key={trust.id}
                          value={trust.id}
                        >
                          {trust.name} ({trust.code})
                        </option>
                      ),
                    )}
                  </select>
                </div>
              )}

              {user?.trust_id && (
                <div className="rounded-xl bg-[#27348B]/5 px-4 py-3 text-xs text-[#27348B]">
                  Academic year will be created
                  under your assigned trust.
                </div>
              )}
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  Name
                </label>

                <Input
                  value={name}
                  onChange={(event) =>
                    setName(
                      event.target.value,
                    )
                  }
                  placeholder="2026-27"
                  required
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
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
                  required
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  End date
                </label>

                <Input
                  type="date"
                  value={endDate}
                  onChange={(event) =>
                    setEndDate(
                      event.target.value,
                    )
                  }
                  required
                  className="rounded-xl"
                />
              </div>

              {create.isError && (
                <div className="rounded-xl bg-red-50 p-3 text-xs text-red-700">
                  {create.error instanceof Error
                    ? create.error.message
                    : "Could not create academic year."}
                </div>
              )}

              <Button
                type="submit"
                disabled={
                  create.isPending ||
                  authLoading ||
                  !resolvedTrustId
                }
                className="w-full rounded-xl bg-[#27348B] hover:bg-[#202c78]"
              >
                Create academic year
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-4">
          {years.isLoading && (
            <Card className="border-white/50 bg-white/70">
              <CardContent className="p-8 text-center text-sm text-slate-500">
                Loading academic years...
              </CardContent>
            </Card>
          )}

          {(years.data ?? []).map(
            (year) => (
              <Card
                key={year.id}
                className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl"
              >
                <CardContent className="p-5">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex size-11 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
                        <CalendarDays className="size-5" />
                      </div>

                      <div>
                        <p className="font-black text-slate-900">
                          {year.name}
                        </p>

                        <p className="text-xs text-slate-500">
                          {year.start_date} â†’{" "}
                          {year.end_date}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {year.is_current && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-bold text-emerald-700">
                          <CheckCircle2 className="size-3" />
                          CURRENT
                        </span>
                      )}

                      {!year.is_current &&
                        year.is_active && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={
                              setCurrent.isPending
                            }
                            onClick={() =>
                              setCurrent.mutate(
                                year.id,
                              )
                            }
                            className="rounded-xl"
                          >
                            Set current
                          </Button>
                        )}

                      {year.is_active &&
                        !year.is_current && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={
                              deactivate.isPending
                            }
                            onClick={() =>
                              deactivate.mutate(
                                year.id,
                              )
                            }
                            className="rounded-xl text-red-600"
                          >
                            Deactivate
                          </Button>
                        )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ),
          )}
        </div>
      </div>
    </div>
  );
}
