"use client";

import { useState } from "react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { MobileNavigation } from "@/components/layout/mobile-navigation";

interface AppFrameProps {
  children: React.ReactNode;
}

export function AppFrame({
  children,
}: AppFrameProps) {
  const [collapsed, setCollapsed] =
    useState(false);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.25),transparent_28%),linear-gradient(135deg,#27348B_0%,#3345A8_48%,#EEF1FF_140%)]">
      <AppSidebar
        collapsed={collapsed}
        onToggle={() =>
          setCollapsed((value) => !value)
        }
      />

      <div
        className={[
          "min-h-screen transition-[padding] duration-300",
          collapsed
            ? "lg:pl-[84px]"
            : "lg:pl-[260px]",
        ].join(" ")}
      >
        <div className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-white/20 bg-[#27348B]/70 px-4 backdrop-blur-xl lg:hidden">
          <MobileNavigation />
          <div>
            <p className="text-sm font-bold text-white">
              Memorial Trust
            </p>
            <p className="text-[10px] text-white/60">
              Management Portal
            </p>
          </div>
        </div>

        <main className="min-h-[calc(100vh-4rem)] p-4 sm:p-6 xl:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}