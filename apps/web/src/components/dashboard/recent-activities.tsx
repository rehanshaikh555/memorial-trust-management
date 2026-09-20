import { CalendarDays, ChevronRight, Image as ImageIcon } from "lucide-react";
import Link from "next/link";

const activities = [
  {
    title: "Annual Sports Day",
    school: "Memorial Primary School",
    date: "18 Sep 2026",
    status: "PUBLISHED",
  },
  {
    title: "Science Exhibition",
    school: "Memorial Secondary School",
    date: "16 Sep 2026",
    status: "APPROVED",
  },
  {
    title: "Community Health Camp",
    school: "Al-Noor Mini School",
    date: "14 Sep 2026",
    status: "SUBMITTED",
  },
];

export function RecentActivities() {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">
            Recent activities
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Latest school updates
          </p>
        </div>

        <Link
          href="/activities"
          className="flex items-center gap-1 text-xs font-semibold text-[#27348B]"
        >
          View all
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="divide-y divide-slate-100">
        {activities.map((activity) => (
          <div
            key={activity.title}
            className="flex items-center gap-3 py-4 first:pt-1 last:pb-1"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#edf0ff] text-[#27348B]">
              <ImageIcon className="h-5 w-5" />
            </div>

            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-slate-800">
                {activity.title}
              </div>

              <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                <span className="truncate">{activity.school}</span>
                <span>*</span>
                <span className="flex items-center gap-1 whitespace-nowrap">
                  <CalendarDays className="h-3 w-3" />
                  {activity.date}
                </span>
              </div>
            </div>

            <span
              className={`hidden rounded-full px-2 py-1 text-[9px] font-bold sm:inline-block ${
                activity.status === "PUBLISHED"
                  ? "bg-emerald-50 text-emerald-600"
                  : activity.status === "APPROVED"
                    ? "bg-blue-50 text-blue-600"
                    : "bg-amber-50 text-amber-600"
              }`}
            >
              {activity.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
