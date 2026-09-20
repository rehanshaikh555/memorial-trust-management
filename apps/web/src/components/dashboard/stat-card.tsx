"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { motion } from "framer-motion";
import type { DashboardStat } from "@/types";

const icons = ["students", "schools", "attendance", "teachers"] as const;

function IconBox({ index }: { index: number }) {
  const icon =
    icons[index] === "students"
      ? "?"
      : icons[index] === "schools"
        ? "?"
        : icons[index] === "attendance"
          ? "?"
          : "?";

  return (
    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#edf0ff] text-lg font-bold text-[#27348B]">
      {icon}
    </div>
  );
}

export function StatCard({
  stat,
  index,
}: {
  stat: DashboardStat;
  index: number;
}) {
  const TrendIcon =
    stat.trend === "up"
      ? ArrowUpRight
      : stat.trend === "down"
        ? ArrowDownRight
        : Minus;

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07 }}
      whileHover={{ y: -3 }}
      className="glass rounded-2xl p-5"
    >
      <div className="flex items-start justify-between">
        <IconBox index={index} />

        <div
          className={`flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-semibold ${
            stat.trend === "down"
              ? "bg-rose-50 text-rose-600"
              : "bg-emerald-50 text-emerald-600"
          }`}
        >
          <TrendIcon className="h-3 w-3" />
          {stat.change}
        </div>
      </div>

      <div className="mt-5">
        <div className="text-2xl font-bold tracking-tight text-slate-900">
          {stat.value}
        </div>
        <div className="mt-1 text-sm font-medium text-slate-600">
          {stat.label}
        </div>
        <div className="mt-1 text-xs text-slate-400">
          {stat.description}
        </div>
      </div>
    </motion.div>
  );
}
