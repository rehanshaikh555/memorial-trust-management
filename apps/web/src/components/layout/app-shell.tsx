"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen">
      <div className="fixed inset-y-0 left-0 z-40 hidden w-[270px] lg:block">
        <Sidebar
          mobileOpen={false}
          onClose={() => setMobileOpen(false)}
        />
      </div>

      <Sidebar
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      <div className="min-h-screen lg:pl-[270px]">
        <Topbar onMenu={() => setMobileOpen(true)} />

        <main className="dashboard-grid min-h-[calc(100vh-76px)] p-4 md:p-6 xl:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
