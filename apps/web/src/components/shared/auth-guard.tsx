"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";

export function AuthGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  const {
    authenticated,
    loading,
  } = useAuth();

  useEffect(() => {
    if (loading) return;

    if (
      !authenticated &&
      pathname !== "/login"
    ) {
      router.replace("/login");
    }
  }, [
    authenticated,
    loading,
    pathname,
    router,
  ]);

  if (loading && pathname !== "/login") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f7ff]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-pulse rounded-2xl bg-[#27348B]" />
          <div className="text-sm font-medium text-slate-500">
            Loading Memorial Trust...
          </div>
        </div>
      </div>
    );
  }

  if (
    !authenticated &&
    pathname !== "/login"
  ) {
    return null;
  }

  return <>{children}</>;
}
