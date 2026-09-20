"use client";

import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { login, setAccessToken } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export default function LoginPage() {
  const router = useRouter();
  const { refreshUser } = useAuth();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const data = await login(
        email,
        password,
      );

      const token =
        data?.tokens?.access_token ??
        data?.access_token;

      if (!token) {
        throw new Error(
          "Authentication response did not contain an access token.",
        );
      }

      setAccessToken(token);

      await refreshUser();

      router.replace("/");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to sign in.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#10184c] px-4 py-10">
      <div className="absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-[#5267d4]/25 blur-[100px]" />
      <div className="absolute -bottom-48 -right-32 h-[600px] w-[600px] rounded-full bg-[#27348B]/60 blur-[110px]" />

      <div className="relative grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-white/10 bg-white/10 shadow-2xl backdrop-blur-2xl lg:grid-cols-[1.05fr_0.95fr]">
        <section className="hidden p-10 text-white lg:flex lg:flex-col lg:justify-between xl:p-14">
          <div>
            <div className="mb-10 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-[#27348B]">
                <ShieldCheck className="h-7 w-7" />
              </div>

              <div>
                <div className="font-bold tracking-wide">
                  MEMORIAL
                </div>
                <div className="text-[10px] uppercase tracking-[0.3em] text-white/50">
                  Trust Management
                </div>
              </div>
            </div>

            <div className="max-w-md">
              <div className="mb-4 text-xs font-semibold uppercase tracking-[0.25em] text-white/50">
                Unified administration
              </div>

              <h1 className="text-4xl font-bold leading-tight xl:text-5xl">
                One place to manage your entire trust.
              </h1>

              <p className="mt-6 text-sm leading-7 text-white/55">
                Manage schools, students, teachers, attendance,
                activities and reports through one secure
                operational platform.
              </p>
            </div>
          </div>

          <div className="text-xs text-white/35">
            Memorial Trust Management - 2026-2027
          </div>
        </section>

        <section className="bg-white/95 p-7 sm:p-10 xl:p-14">
          <motion.div
            initial={{
              opacity: 0,
              y: 14,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
          >
            <div className="mb-8 lg:hidden">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#27348B] text-white">
                  <ShieldCheck className="h-6 w-6" />
                </div>

                <div>
                  <div className="font-bold text-[#27348B]">
                    MEMORIAL
                  </div>
                  <div className="text-[9px] uppercase tracking-[0.25em] text-slate-400">
                    Trust Management
                  </div>
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h2 className="text-2xl font-bold text-slate-900">
                Welcome back
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Sign in to access your trust workspace.
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="space-y-5"
            >
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Email address
                </label>

                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  required
                  autoComplete="email"
                  placeholder="admin@example.com"
                  className="h-12 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-[#27348B] focus:ring-4 focus:ring-[#27348B]/10"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Password
                </label>

                <div className="relative">
                  <LockKeyhole className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

                  <input
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    required
                    autoComplete="current-password"
                    placeholder="Enter your password"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-slate-50 pl-11 pr-12 text-sm outline-none transition focus:border-[#27348B] focus:ring-4 focus:ring-[#27348B]/10"
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword(
                        (value) => !value,
                      )
                    }
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#27348B]"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#27348B] text-sm font-semibold text-white shadow-lg shadow-[#27348B]/20 transition hover:bg-[#202c78] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading
                  ? "Signing in..."
                  : "Sign in"}

                {!loading && (
                  <ArrowRight className="h-4 w-4" />
                )}
              </button>
            </form>

            <div className="mt-8 rounded-xl bg-[#f5f7ff] p-4 text-xs leading-5 text-slate-500">
              <strong className="text-slate-700">
                Secure workspace
              </strong>
              <br />
              Access is controlled by trust, school
              and role-level permissions.
            </div>
          </motion.div>
        </section>
      </div>
    </main>
  );
}
