"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { apiFetch, clearAccessToken, getAccessToken } from "@/lib/api";
import type { CurrentUser } from "@/types";

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  authenticated: boolean;
  refreshUser: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext =
  createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] =
    useState<CurrentUser | null>(null);

  const [loading, setLoading] =
    useState(true);

  async function refreshUser() {
    const token = getAccessToken();

    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response =
        await apiFetch<CurrentUser>("/auth/me");

      setUser(response);
    } catch {
      clearAccessToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function signOut() {
    try {
      await apiFetch("/auth/logout", {
        method: "POST",
      });
    } catch {
      // Local auth state must still be cleared.
    } finally {
      clearAccessToken();
      setUser(null);
    }
  }

  useEffect(() => {
    void refreshUser();

    const handler = () => {
      setUser(null);
      setLoading(false);
    };

    window.addEventListener(
      "memorial:unauthorized",
      handler,
    );

    return () => {
      window.removeEventListener(
        "memorial:unauthorized",
        handler,
      );
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      authenticated: Boolean(user),
      refreshUser,
      signOut,
    }),
    [user, loading],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}
