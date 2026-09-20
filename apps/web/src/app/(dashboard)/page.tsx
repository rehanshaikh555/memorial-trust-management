"use client";

import Link from "next/link";
import {
  Activity,
  Bell,
  GraduationCap,
  School,
  Users,
} from "lucide-react";
import { motion } from "framer-motion";

import { DashboardKpi } from "@/components/dashboard/dashboard-kpi";
import { DashboardActivityPanel } from "@/components/dashboard/activity-panel";
import { useSchools, useStudents, useTeachers } from "@/hooks/use-resources";
import { useUnreadNotificationCount } from "@/hooks/use-notifications";
import { useAuth } from "@/providers/auth-provider";

export default function DashboardPage() {
  const { user } = useAuth();

  const schools = useSchools();
  const students = useStudents();
  const teachers = useTeachers();

  const notifications =
    useUnreadNotificationCount(
      Boolean(user),
    );

  const schoolCount =
    schools.data?.length ?? 0;

  const studentCount =
    students.data?.length ?? 0;

  const teacherCount =
    teachers.data?.length ?? 0;

  const notificationCount =
    notifications.data ?? 0;

  const firstName =
    user?.email?.split("@")[0] ??
    "Administrator";

  const activityItems = [
    {
      title: `${schoolCount} schools connected`,
      description:
        "School records currently available within your authorized scope.",
      time: "Live API",
    },
    {
      title: `${studentCount} students visible`,
      description:
        "Student records returned from the current school/trust scope.",
      time: "Live API",
    },
    {
      title: `${teacherCount} teachers visible`,
      description:
        "Teacher records available from the current authorization scope.",
      time: "Live API",
    },
  ];

  return (
    <div className="mx-auto max-w-[1600px]">
      <motion.div
        initial={{
          opacity: 0,
          y: 14,
        }}
        animate={{
          opacity: 1,
          y: 0,
        }}
        className="mb-7 overflow-hidden rounded-[2rem] border border-white/40 bg-[#27348B]/90 p-6 text-white shadow-2xl shadow-[#27348B]/20 backdrop-blur-xl sm:p-8"
      >
        <div className="relative">
          <div className="absolute -right-24 -top-24 size-64 rounded-full bg-white/10 blur-3xl" />

          <p className="relative text-xs font-semibold uppercase tracking-[0.2em] text-white/60">
            Trust management portal
          </p>

          <h1 className="relative mt-2 text-3xl font-black tracking-tight sm:text-4xl">
            Good to see you,{" "}
            <span className="text-white/80">
              {firstName}
            </span>
          </h1>

          <p className="relative mt-3 max-w-2xl text-sm leading-6 text-white/65">
            Monitor schools, students, teachers,
            attendance, activities and reports from
            one secure workspace.
          </p>

          <div className="relative mt-6 flex flex-wrap gap-3">
            <Link
              href="/students"
              className="rounded-xl bg-white px-4 py-2.5 text-xs font-bold text-[#27348B] shadow-lg transition hover:-translate-y-0.5"
            >
              Manage students
            </Link>

            <Link
              href="/attendance"
              className="rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-xs font-bold text-white backdrop-blur transition hover:bg-white/15"
            >
              Open attendance
            </Link>
          </div>
        </div>
      </motion.div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <DashboardKpi
          label="Schools"
          value={
            schools.isLoading
              ? "..."
              : String(schoolCount)
          }
          description="Authorized school records"
          icon={School}
          index={0}
        />

        <DashboardKpi
          label="Students"
          value={
            students.isLoading
              ? "..."
              : String(studentCount)
          }
          description="Active student records"
          icon={GraduationCap}
          index={1}
        />

        <DashboardKpi
          label="Teachers"
          value={
            teachers.isLoading
              ? "..."
              : String(teacherCount)
          }
          description="Teacher records"
          icon={Users}
          index={2}
        />

        <DashboardKpi
          label="Notifications"
          value={
            notifications.isLoading
              ? "..."
              : String(notificationCount)
          }
          description="Unread notifications"
          icon={Bell}
          index={3}
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <DashboardActivityPanel
          items={activityItems}
        />

        <div className="rounded-3xl border border-white/50 bg-white/70 p-6 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-[#27348B]/10 text-[#27348B]">
              <Activity className="size-5" />
            </div>

            <div>
              <p className="text-sm font-bold text-slate-900">
                Operations
              </p>
              <p className="text-xs text-slate-500">
                Quick access
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-3">
            {[
              [
                "Students",
                "/students",
                "Admissions and student lifecycle",
              ],
              [
                "Teachers",
                "/teachers",
                "Staff and assignments",
              ],
              [
                "Attendance",
                "/attendance",
                "Daily and reporting workflows",
              ],
              [
                "Activities",
                "/activities",
                "Review and publication workflow",
              ],
              [
                "Reports",
                "/reports",
                "Operational reporting",
              ],
            ].map(
              ([label, href, description]) => (
                <Link
                  key={href}
                  href={href}
                  className="group rounded-2xl border border-slate-100 bg-white/70 p-4 transition hover:-translate-y-0.5 hover:border-[#27348B]/20 hover:shadow-md"
                >
                  <p className="text-sm font-bold text-slate-800 group-hover:text-[#27348B]">
                    {label}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {description}
                  </p>
                </Link>
              ),
            )}
          </div>
        </div>
      </div>
    </div>
  );
}