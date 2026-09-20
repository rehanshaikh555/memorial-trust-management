"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  { day: "Mon", attendance: 91 },
  { day: "Tue", attendance: 94 },
  { day: "Wed", attendance: 89 },
  { day: "Thu", attendance: 96 },
  { day: "Fri", attendance: 93 },
  { day: "Sat", attendance: 87 },
];

export function AttendanceChart() {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="mb-5 flex items-start justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">
            Attendance overview
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Average attendance across active schools
          </p>
        </div>

        <div className="rounded-lg bg-[#edf0ff] px-3 py-1.5 text-xs font-semibold text-[#27348B]">
          This week
        </div>
      </div>

      <div className="h-[270px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="attendanceFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#27348B" stopOpacity={0.28} />
                <stop offset="100%" stopColor="#27348B" stopOpacity={0.02} />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke="#e9ecf4"
              strokeDasharray="4 4"
              vertical={false}
            />

            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#8a93aa", fontSize: 11 }}
            />

            <YAxis
              domain={[70, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#8a93aa", fontSize: 11 }}
              tickFormatter={(value) => `${value}%`}
            />

            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #e3e7f2",
                boxShadow: "0 12px 30px rgba(39,52,139,0.12)",
              }}
              formatter={(value) => [`${value}%`, "Attendance"]}
            />

            <Area
              type="monotone"
              dataKey="attendance"
              stroke="#27348B"
              strokeWidth={3}
              fill="url(#attendanceFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
