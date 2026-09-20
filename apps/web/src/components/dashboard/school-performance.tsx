"use client";

import { motion } from "framer-motion";
import { Progress } from "@/components/ui/progress";

const schools = [
  { name: "Memorial Primary School", students: 482, attendance: 96 },
  { name: "Memorial Secondary School", students: 631, attendance: 94 },
  { name: "Al-Noor Mini School", students: 294, attendance: 91 },
  { name: "Community Learning Centre", students: 218, attendance: 89 },
];

export function SchoolPerformance() {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="mb-5">
        <h2 className="font-semibold text-slate-900">
          School performance
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Attendance snapshot by school
        </p>
      </div>

      <div className="space-y-5">
        {schools.map((school, index) => (
          <motion.div
            key={school.name}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.08 }}
          >
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-slate-700">
                  {school.name}
                </div>
                <div className="mt-0.5 text-[11px] text-slate-400">
                  {school.students} active students
                </div>
              </div>

              <div className="text-sm font-bold text-[#27348B]">
                {school.attendance}%
              </div>
            </div>

            <Progress value={school.attendance} className="h-2" />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
