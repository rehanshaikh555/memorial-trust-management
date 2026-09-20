import {
  CheckCircle2,
  Clock3,
  FileCheck2,
  GraduationCap,
  Send,
  XCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";

const styles: Record<
  string,
  {
    label: string;
    className: string;
    icon: typeof Clock3;
  }
> = {
  APPLICATION_DRAFT: {
    label: "Draft",
    className:
      "bg-slate-100 text-slate-600",
    icon: Clock3,
  },
  SUBMITTED: {
    label: "Submitted",
    className:
      "bg-blue-100 text-blue-700",
    icon: Send,
  },
  READY_FOR_APPROVAL: {
    label: "Ready for approval",
    className:
      "bg-amber-100 text-amber-700",
    icon: FileCheck2,
  },
  ACTIVE: {
    label: "Active",
    className:
      "bg-emerald-100 text-emerald-700",
    icon: CheckCircle2,
  },
  TRANSFERRED: {
    label: "Transferred",
    className:
      "bg-purple-100 text-purple-700",
    icon: GraduationCap,
  },
  LEFT: {
    label: "Left",
    className:
      "bg-slate-100 text-slate-600",
    icon: XCircle,
  },
  GRADUATED: {
    label: "Graduated",
    className:
      "bg-indigo-100 text-indigo-700",
    icon: GraduationCap,
  },
  ARCHIVED: {
    label: "Archived",
    className:
      "bg-slate-100 text-slate-500",
    icon: XCircle,
  },
};

export function StudentStatus({
  status,
}: {
  status?: string | null;
}) {
  const config =
    styles[status ?? ""] ??
    styles.APPLICATION_DRAFT;

  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold",
        config.className,
      )}
    >
      <Icon className="size-3.5" />
      {config.label}
    </span>
  );
}