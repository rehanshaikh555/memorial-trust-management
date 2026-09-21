"use client";

import {
  Bell,
  ChevronDown,
  LogOut,
  Menu,
  Search,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

interface TopbarProps {
  onMenu: () => void;
}

export function Topbar({
  onMenu,
}: TopbarProps) {
  const router = useRouter();
  const { user, signOut } =
    useAuth();

  async function handleLogout() {
    await signOut();
    router.replace("/login");
  }

  const name =
    user?.full_name ??
    user?.email ??
    "Administrator";

  const role =
    user?.role_name ??
    user?.role ??
    "Administrator";

  return (
    <header className="glass sticky top-0 z-30 flex h-[76px] items-center justify-between border-x-0 border-t-0 px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenu}
          className="rounded-xl p-2.5 text-slate-600 hover:bg-[#edf0ff] hover:text-[#27348B] lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white/70 px-3 py-2 md:flex">
          <Search className="h-4 w-4 text-slate-400" />

          <input
            className="w-52 bg-transparent text-sm outline-none placeholder:text-slate-400"
            placeholder="Search anything..."
          />

          <kbd className="rounded-md border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-400">
            Ctrl K
          </kbd>
        </div>

        <div className="md:hidden">
          <div className="text-sm font-bold text-[#27348B]">
            MEMORIAL
          </div>
          <div className="text-[9px] uppercase tracking-[0.2em] text-slate-400">
            Trust Management
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        <Link
          href="/notifications"
          className="relative rounded-xl p-2.5 text-slate-500 transition hover:bg-[#edf0ff] hover:text-[#27348B]"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-[#27348B] ring-2 ring-white" />
        </Link>

        <div className="hidden h-8 w-px bg-slate-200 sm:block" />

        <div className="group relative">
          <button className="flex items-center gap-3 rounded-xl p-1.5 pr-2 transition hover:bg-white">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#27348B] text-sm font-bold text-white shadow-md">
              {name
                .slice(0, 1)
                .toUpperCase()}
            </div>

            <div className="hidden text-left sm:block">
              <div className="max-w-[160px] truncate text-sm font-semibold text-slate-800">
                {name}
              </div>

              <div className="text-[11px] text-slate-400">
                {role}
              </div>
            </div>

            <ChevronDown className="hidden h-4 w-4 text-slate-400 sm:block" />
          </button>

          <div className="invisible absolute right-0 top-full mt-2 w-48 translate-y-1 rounded-2xl border border-slate-100 bg-white p-2 opacity-0 shadow-xl transition group-focus-within:visible group-focus-within:translate-y-0 group-focus-within:opacity-100 group-hover:visible group-hover:translate-y-0 group-hover:opacity-100">
            <Link
              href="/settings"
              className="block rounded-xl px-3 py-2.5 text-sm text-slate-600 hover:bg-slate-50"
            >
              Settings
            </Link>

            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm text-rose-600 hover:bg-rose-50"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
