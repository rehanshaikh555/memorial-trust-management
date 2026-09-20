"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { getVisibleNavigation } from "@/lib/navigation";
import { useAuth } from "@/providers/auth-provider";

export function MobileNavigation() {
  const pathname = usePathname();
  const { user } = useAuth();

  const sections = getVisibleNavigation(
    user?.role,
  );

  return (
    <Sheet>
      <SheetTrigger
        className="flex size-10 items-center justify-center rounded-xl border border-white/20 bg-white/10 text-white backdrop-blur-xl lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="size-5" />
      </SheetTrigger>

      <SheetContent
        side="left"
        className="w-[290px] border-white/10 bg-[#27348B] p-0 text-white"
      >
        <div className="border-b border-white/15 px-6 py-6">
          <p className="text-lg font-bold">
            Memorial Trust
          </p>

          <p className="text-xs text-white/60">
            Management Portal
          </p>
        </div>

        <nav className="space-y-6 overflow-y-auto p-4">
          {sections.map((section) => (
            <div key={section.label}>
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/45">
                {section.label}
              </p>

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
                      className={cn(
                        "flex h-11 items-center gap-3 rounded-xl px-3 text-sm",
                        active
                          ? "bg-white text-[#27348B]"
                          : "text-white/70 hover:bg-white/10 hover:text-white",
                      )}
                    >
                      <Icon className="size-[18px]" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </SheetContent>
    </Sheet>
  );
}