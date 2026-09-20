"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  CalendarCheck,
  GraduationCap,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { motion } from "framer-motion";

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
}

const navigation = [
  {
    label: "Overview",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Schools",
    href: "/schools",
    icon: Building2,
  },
  {
    label: "Students",
    href: "/students",
    icon: GraduationCap,
  },
  {
    label: "Teachers",
    href: "/teachers",
    icon: Users,
  },
  {
    label: "Attendance",
    href: "/attendance",
    icon: CalendarCheck,
  },
  {
    label: "Activities",
    href: "/activities",
    icon: Activity,
  },
  {
    label: "Notifications",
    href: "/notifications",
    icon: Bell,
  },
  {
    label: "Reports",
    href: "/reports",
    icon: BarChart3,
  },
];

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  const content = (
    <aside className="glass-dark flex h-full w-[270px] flex-col overflow-hidden text-white">
      <div className="flex h-20 items-center justify-between border-b border-white/10 px-6">
        <Link href="/" onClick={onClose} className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-[#27348B] shadow-lg">
            <ShieldCheck className="h-6 w-6" />
          </div>

          <div>
            <div className="text-[15px] font-bold tracking-wide">
              MEMORIAL
            </div>
            <div className="text-[10px] font-medium uppercase tracking-[0.25em] text-white/60">
              Trust Management
            </div>
          </div>
        </Link>

        <button
          onClick={onClose}
          className="rounded-lg p-2 text-white/60 hover:bg-white/10 hover:text-white lg:hidden"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="px-4 pt-6">
        <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40">
          Workspace
        </div>

        <nav className="space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`relative flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition-all ${
                  active
                    ? "bg-white text-[#27348B] shadow-lg"
                    : "text-white/70 hover:bg-white/10 hover:text-white"
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="active-nav"
                    className="absolute inset-0 rounded-xl bg-white"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}

                <span className="relative z-10 flex items-center gap-3">
                  <Icon className="h-[18px] w-[18px]" />
                  <span>{item.label}</span>
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-4">
        <Link
          href="/settings"
          onClick={onClose}
          className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
            pathname.startsWith("/settings")
              ? "bg-white text-[#27348B]"
              : "text-white/60 hover:bg-white/10 hover:text-white"
          }`}
        >
          <Settings className="h-[18px] w-[18px]" />
          Settings
        </Link>

        <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="mb-2 flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-white/70" />
            <span className="text-xs font-semibold">Academic Year</span>
          </div>
          <div className="text-sm font-medium">2026 - 2027</div>
          <div className="mt-1 text-[11px] text-white/45">
            Current session
          </div>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      <div className="hidden h-screen lg:block">{content}</div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="Close navigation"
            onClick={onClose}
            className="absolute inset-0 bg-[#101844]/50 backdrop-blur-sm"
          />

          <motion.div
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="relative h-full"
          >
            {content}
          </motion.div>
        </div>
      )}
    </>
  );
}
