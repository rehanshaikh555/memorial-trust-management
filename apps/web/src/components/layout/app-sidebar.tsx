"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  GraduationCap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getVisibleNavigation,
} from "@/lib/navigation";
import { useAuth } from "@/providers/auth-provider";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function AppSidebar({
  collapsed,
  onToggle,
}: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuth();

  const sections = getVisibleNavigation(
    user?.role,
  );

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 hidden border-r border-white/20 bg-[#27348B]/95 text-white shadow-2xl backdrop-blur-xl transition-all duration-300 lg:flex lg:flex-col",
        collapsed ? "w-[84px]" : "w-[260px]",
      )}
    >
      <div className="flex h-20 items-center border-b border-white/15 px-5">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-white/15 ring-1 ring-white/20">
            <GraduationCap className="size-5" />
          </div>

          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-sm font-bold">
                Memorial Trust
              </p>
              <p className="truncate text-[11px] text-white/60">
                Management Portal
              </p>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 space-y-7 overflow-y-auto px-3 py-6">
        {sections.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/45">
                {section.label}
              </p>
            )}

            <div className="space-y-1">
              {section.items.map((item) => {
                const active =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname.startsWith(
                        item.href,
                      );

                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={
                      collapsed
                        ? item.label
                        : undefined
                    }
                    className={cn(
                      "group flex h-11 items-center gap-3 rounded-xl px-3 text-sm transition-all duration-200",
                      active
                        ? "bg-white text-[#27348B] shadow-lg"
                        : "text-white/70 hover:bg-white/10 hover:text-white",
                      collapsed &&
                        "justify-center px-0",
                    )}
                  >
                    <Icon
                      className={cn(
                        "size-[18px] shrink-0 transition-transform group-hover:scale-110",
                        active &&
                          "text-[#27348B]",
                      )}
                    />

                    {!collapsed && (
                      <span className="truncate">
                        {item.label}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/15 p-3">
        <button
          type="button"
          onClick={onToggle}
          className="flex h-10 w-full items-center justify-center rounded-xl bg-white/10 text-white/70 transition hover:bg-white/15 hover:text-white"
        >
          {collapsed ? (
            <ChevronRight className="size-4" />
          ) : (
            <ChevronLeft className="size-4" />
          )}
        </button>
      </div>
    </aside>
  );
}