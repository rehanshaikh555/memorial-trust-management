"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight } from "lucide-react";

interface DashboardKpiProps {
  label: string;
  value: string;
  description: string;
  icon: LucideIcon;
  index?: number;
}

export function DashboardKpi({
  label,
  value,
  description,
  icon: Icon,
  index = 0,
}: DashboardKpiProps) {
  return (
    <motion.div
      initial={{
        opacity: 0,
        y: 18,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        duration: 0.45,
        delay: index * 0.06,
      }}
      className="group relative overflow-hidden rounded-3xl border border-white/50 bg-white/70 p-5 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl"
    >
      <div className="absolute -right-8 -top-8 size-28 rounded-full bg-[#27348B]/10 blur-2xl transition-transform duration-500 group-hover:scale-150" />

      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            {label}
          </p>

          <p className="mt-3 text-3xl font-black tracking-tight text-slate-900">
            {value}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            {description}
          </p>
        </div>

        <div className="flex size-11 items-center justify-center rounded-2xl bg-[#27348B] text-white shadow-lg shadow-[#27348B]/20">
          <Icon className="size-5" />
        </div>
      </div>

      <div className="mt-5 flex items-center gap-1 text-xs font-semibold text-[#27348B]">
        View details
        <ArrowUpRight className="size-3.5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
      </div>
    </motion.div>
  );
}