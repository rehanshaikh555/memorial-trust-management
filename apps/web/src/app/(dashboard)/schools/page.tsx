"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Building2,
  Eye,
  Plus,
  Search,
  ShieldCheck,
} from "lucide-react";
import { motion } from "framer-motion";

import {
  useSchoolList,
} from "@/hooks/use-academic-structure";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function SchoolsPage() {
  const [search, setSearch] =
    useState("");

  const schools =
    useSchoolList();

  const filtered =
    useMemo(() => {
      const query =
        search
          .trim()
          .toLowerCase();

      if (!query) {
        return schools.data ?? [];
      }

      return (
        schools.data ?? []
      ).filter((school) =>
        [
          school.name,
          school.code,
          school.address,
          school.email,
          school.phone,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(query),
      );
    }, [
      schools.data,
      search,
    ]);

  return (
    <div className="mx-auto max-w-[1500px]">
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#27348B]/60">
            Trust management
          </p>

          <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-900">
            Schools
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Manage schools and their academic structure.
          </p>
        </div>

        <Link href="/schools/new">
          <Button className="rounded-xl bg-[#27348B] hover:bg-[#202c78]">
            <Plus className="mr-2 size-4" />
            Add school
          </Button>
        </Link>
      </div>

      <div className="mb-5 rounded-3xl border border-white/50 bg-white/70 p-4 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
        <div className="relative max-w-xl">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

          <Input
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
            placeholder="Search schools by name, code, phone or email..."
            className="h-11 rounded-xl border-slate-200 bg-white/80 pl-10"
          />
        </div>
      </div>

      {schools.isLoading && (
        <div className="rounded-3xl bg-white/70 p-12 text-center shadow-xl">
          <p className="text-sm text-slate-500">
            Loading schools...
          </p>
        </div>
      )}

      {schools.isError && (
        <div className="rounded-3xl border border-red-100 bg-red-50 p-8 text-center">
          <p className="font-bold text-red-700">
            Unable to load schools
          </p>
          <p className="mt-1 text-sm text-red-600">
            {schools.error instanceof Error
              ? schools.error.message
              : "The API request failed."}
          </p>
        </div>
      )}

      {!schools.isLoading &&
        !schools.isError &&
        filtered.length === 0 && (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-white/60 p-16 text-center">
            <Building2 className="mx-auto size-10 text-[#27348B]/40" />

            <p className="mt-4 font-bold text-slate-800">
              No schools found
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Create the first school or change your search.
            </p>
          </div>
        )}

      {filtered.length > 0 && (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map(
            (school, index) => (
              <motion.div
                key={school.id}
                initial={{
                  opacity: 0,
                  y: 12,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  delay:
                    index * 0.04,
                }}
                className="group rounded-3xl border border-white/50 bg-white/70 p-5 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl transition hover:-translate-y-1"
              >
                <div className="flex items-start justify-between">
                  <div className="flex size-12 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
                    <Building2 className="size-6" />
                  </div>

                  <span
                    className={[
                      "rounded-full px-2.5 py-1 text-[10px] font-bold",
                      school.is_active
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-slate-100 text-slate-500",
                    ].join(" ")}
                  >
                    {school.is_active
                      ? "ACTIVE"
                      : "INACTIVE"}
                  </span>
                </div>

                <h2 className="mt-5 text-lg font-black text-slate-900">
                  {school.name}
                </h2>

                <p className="mt-1 text-xs font-semibold text-[#27348B]">
                  {school.code}
                </p>

                <p className="mt-4 line-clamp-2 text-sm text-slate-500">
                  {school.address ||
                    "No address provided"}
                </p>

                <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-400">
                  <ShieldCheck className="size-3.5 text-[#27348B]" />
                  Authorized school record
                </div>

                <Link
                  href={`/schools/${school.id}`}
                  className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-[#27348B]/5 py-2.5 text-xs font-bold text-[#27348B] transition hover:bg-[#27348B]/10"
                >
                  <Eye className="size-3.5" />
                  Open school
                </Link>
              </motion.div>
            ),
          )}
        </div>
      )}
    </div>
  );
}