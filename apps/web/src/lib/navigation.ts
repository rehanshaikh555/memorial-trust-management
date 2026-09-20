import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BarChart3,
  Bell,
  CalendarDays,
  GraduationCap,
  LayoutDashboard,
  School,
  Settings,
  ShieldCheck,
  Users,
  UserRoundCog,
} from "lucide-react";

export type AppRole =
  | "SUPER_ADMIN"
  | "TRUST_ADMIN"
  | "SCHOOL_ADMIN"
  | "TEACHER"
  | "VIEWER";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  roles?: AppRole[];
  badge?: string;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

const MANAGEMENT_ROLES: AppRole[] = [
  "SUPER_ADMIN",
  "TRUST_ADMIN",
  "SCHOOL_ADMIN",
];

const ADMIN_ROLES: AppRole[] = [
  "SUPER_ADMIN",
  "TRUST_ADMIN",
];

export const navigationSections: NavSection[] = [
  {
    label: "Overview",
    items: [
      {
        label: "Dashboard",
        href: "/",
        icon: LayoutDashboard,
      },
      {
        label: "Notifications",
        href: "/notifications",
        icon: Bell,
      },
    ],
  },
  {
    label: "Management",
    items: [
      {
        label: "Schools",
        href: "/schools",
        icon: School,
        roles: MANAGEMENT_ROLES,
      },
      {
        label: "Students",
        href: "/students",
        icon: GraduationCap,
      },
      {
        label: "Teachers",
        href: "/teachers",
        icon: Users,
      },
      {
        label: "Classes",
        href: "/classes",
        icon: Users,
        roles: MANAGEMENT_ROLES,
      },
      {
        label: "Academic Years",
        href: "/academic-years",
        icon: CalendarDays,
        roles: ADMIN_ROLES,
      },
    ],
  },
  {
    label: "Operations",
    items: [
      {
        label: "Attendance",
        href: "/attendance",
        icon: CalendarDays,
      },
      {
        label: "Activities",
        href: "/activities",
        icon: Activity,
      },
      {
        label: "Reports",
        href: "/reports",
        icon: BarChart3,
      },
    ],
  },
  {
    label: "System",
    items: [
      {
        label: "Settings",
        href: "/settings",
        icon: Settings,
        roles: ADMIN_ROLES,
      },
      {
        label: "Administration",
        href: "/administration",
        icon: ShieldCheck,
        roles: ["SUPER_ADMIN", "TRUST_ADMIN"],
      },
    ],
  },
];

export function canSeeNavItem(
  item: NavItem,
  role?: string | null,
) {
  if (!item.roles || item.roles.length === 0) {
    return true;
  }

  if (!role) {
    return false;
  }

  return item.roles.includes(
    role.toUpperCase() as AppRole,
  );
}

export function getVisibleNavigation(
  role?: string | null,
) {
  return navigationSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) =>
        canSeeNavItem(item, role),
      ),
    }))
    .filter((section) => section.items.length > 0);
}