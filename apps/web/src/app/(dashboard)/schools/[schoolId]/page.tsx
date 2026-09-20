"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  GraduationCap,
  Loader2,
  Users,
} from "lucide-react";

import {
  useSchool,
} from "@/hooks/use-academic-structure";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SchoolDetailPage() {
  const params =
    useParams<{
      schoolId: string;
    }>();

  const school =
    useSchool(params.schoolId);

  if (school.isLoading) {
    return (
      <div className="flex min-h-[500px] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-[#27348B]" />
      </div>
    );
  }

  if (
    school.isError ||
    !school.data
  ) {
    return (
      <div className="mx-auto max-w-4xl rounded-3xl bg-red-50 p-10 text-center">
        <p className="font-bold text-red-700">
          School could not be loaded
        </p>
        <p className="mt-1 text-sm text-red-600">
          {school.error instanceof Error
            ? school.error.message
            : "The API request failed."}
        </p>
      </div>
    );
  }

  const record = school.data;

  return (
    <div className="mx-auto max-w-[1400px]">
      <Link
        href="/schools"
        className="mb-6 inline-flex items-center gap-2 text-xs font-bold text-[#27348B]"
      >
        <ArrowLeft className="size-4" />
        Back to schools
      </Link>

      <div className="rounded-[2rem] bg-[#27348B] p-7 text-white shadow-2xl shadow-[#27348B]/20 sm:p-9">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex size-16 items-center justify-center rounded-2xl bg-white/15 ring-1 ring-white/20">
              <Building2 className="size-8" />
            </div>

            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-white/50">
                School
              </p>

              <h1 className="mt-1 text-3xl font-black">
                {record.name}
              </h1>

              <p className="mt-1 text-sm text-white/60">
                {record.code}
              </p>
            </div>
          </div>

          <span className="rounded-full bg-white/15 px-3 py-1.5 text-xs font-bold">
            {record.is_active
              ? "ACTIVE"
              : "INACTIVE"}
          </span>
        </div>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-3">
        {[
          {
            title: "Students",
            description: "Open student management",
            href: "/students",
            Icon: GraduationCap,
          },
          {
            title: "Teachers",
            description: "Open teacher management",
            href: "/teachers",
            Icon: Users,
          },
          {
            title: "Academic years",
            description: "Manage school years",
            href: "/academic-years",
            Icon: CalendarDays,
          },
        ].map(
          ({
            title,
            description,
            href,
            Icon,
          }) => (
            <Link
              key={href}
              href={href}
              className="group rounded-3xl border border-white/50 bg-white/70 p-6 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl transition hover:-translate-y-1"
            >
              <div className="flex size-12 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
                <Icon className="size-6" />
              </div>

              <h2 className="mt-5 font-black text-slate-900 group-hover:text-[#27348B]">
                {title}
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                {description}
              </p>
            </Link>
          ),
        )}
      </div>

      <Card className="mt-6 border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-sm">
            School information
          </CardTitle>
        </CardHeader>

        <CardContent className="grid gap-5 sm:grid-cols-2">
          {[
            [
              "Email",
              record.email ||
                "Not provided",
            ],
            [
              "Phone",
              record.phone ||
                "Not provided",
            ],
            [
              "Address",
              record.address ||
                "Not provided",
            ],
          ].map(
            ([label, value]) => (
              <div key={label}>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {label}
                </p>

                <p className="mt-1 text-sm text-slate-700">
                  {value}
                </p>
              </div>
            ),
          )}
        </CardContent>
      </Card>
    </div>
  );
}