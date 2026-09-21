"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowLeft,
  Building2,
  Loader2,
} from "lucide-react";
import { useRouter } from "next/navigation";

import {
  useCreateSchool,
  useTrustList,
} from "@/hooks/use-academic-structure";
import { useAuth } from "@/hooks/use-auth";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function NewSchoolPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const create = useCreateSchool();
  const trusts = useTrustList();

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

  const [form, setForm] = useState({
    name: "",
    code: "",
    address: "",
  });

  function update(
    key: keyof typeof form,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  async function submit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    if (!resolvedTrustId) {
      return;
    }

    try {
      const school =
        await create.mutateAsync({
          trust_id: resolvedTrustId,
          name: form.name.trim(),
          code: form.code.trim(),
          address:
            form.address.trim() || null,
        });

      router.push(
        `/schools/${school.id}`,
      );
    } catch {
      // Error shown below.
    }
  }

  const canSubmit =
    Boolean(resolvedTrustId) &&
    Boolean(form.name.trim()) &&
    Boolean(form.code.trim()) &&
    !create.isPending &&
    !authLoading;

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        href="/schools"
        className="mb-6 inline-flex items-center gap-2 text-xs font-bold text-[#27348B]"
      >
        <ArrowLeft className="size-4" />
        Back to schools
      </Link>

      <Card className="border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
              <Building2 className="size-5" />
            </div>

            <div>
              <CardTitle>
                Create school
              </CardTitle>

              <p className="mt-1 text-xs text-slate-500">
                Add a school to the trust.
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <form
            onSubmit={submit}
            className="space-y-5"
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
                School will be created under your
                assigned trust.
              </div>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  School name
                </label>

                <Input
                  value={form.name}
                  onChange={(event) =>
                    update(
                      "name",
                      event.target.value,
                    )
                  }
                  required
                  className="rounded-xl"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                  School code
                </label>

                <Input
                  value={form.code}
                  onChange={(event) =>
                    update(
                      "code",
                      event.target.value,
                    )
                  }
                  required
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

            {create.isError && (
              <div className="rounded-2xl bg-red-50 p-4 text-sm text-red-700">
                {create.error instanceof Error
                  ? create.error.message
                  : "School creation failed."}
              </div>
            )}

            {requiresTrustSelection &&
              trusts.isError && (
                <div className="rounded-2xl bg-red-50 p-4 text-sm text-red-700">
                  Could not load trusts.
                </div>
              )}

            <div className="flex justify-end gap-3 border-t border-slate-100 pt-5">
              <Link href="/schools">
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
                disabled={!canSubmit}
                className="rounded-xl bg-[#27348B] hover:bg-[#202c78]"
              >
                {create.isPending && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                Create school
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
