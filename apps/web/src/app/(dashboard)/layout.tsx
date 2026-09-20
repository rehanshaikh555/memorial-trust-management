"use client";

import type { ReactNode } from "react";
import { AuthGuard } from "@/components/shared/auth-guard";
import { AppFrame } from "@/components/layout/app-frame";

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <AuthGuard>
      <AppFrame>
        {children}
      </AppFrame>
    </AuthGuard>
  );
}