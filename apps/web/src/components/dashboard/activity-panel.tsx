"use client";

import Link from "next/link";
import { ArrowRight, BellRing } from "lucide-react";
import { motion } from "framer-motion";

interface ActivityItem {
  title: string;
  description: string;
  time: string;
}

interface DashboardActivityPanelProps {
  items: ActivityItem[];
}

export function DashboardActivityPanel({
  items,
}: DashboardActivityPanelProps) {
  return (
    <div className="rounded-3xl border border-white/50 bg-white/70 p-6 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-bold text-slate-900">
            Recent activity
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Latest events across the trust
          </p>
        </div>

        <BellRing className="size-5 text-[#27348B]" />
      </div>

      <div className="mt-6 space-y-4">
        {items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center">
            <p className="text-sm font-medium text-slate-600">
              No recent activity
            </p>
            <p className="mt-1 text-xs text-slate-400">
              New workflow events will appear here.
            </p>
          </div>
        ) : (
          items.map((item, index) => (
            <motion.div
              key={`${item.title}-${index}`}
              initial={{
                opacity: 0,
                x: -10,
              }}
              animate={{
                opacity: 1,
                x: 0,
              }}
              transition={{
                delay: index * 0.05,
              }}
              className="flex gap-3 rounded-2xl bg-white/60 p-3"
            >
              <div className="mt-1 size-2 shrink-0 rounded-full bg-[#27348B]" />

              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-800">
                  {item.title}
                </p>
                <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">
                  {item.description}
                </p>
                <p className="mt-1 text-[10px] text-slate-400">
                  {item.time}
                </p>
              </div>
            </motion.div>
          ))
        )}
      </div>

      <Link
        href="/notifications"
        className="mt-5 flex items-center justify-center gap-2 rounded-xl bg-[#27348B]/5 py-2.5 text-xs font-semibold text-[#27348B] transition hover:bg-[#27348B]/10"
      >
        Open notification center
        <ArrowRight className="size-3.5" />
      </Link>
    </div>
  );
}