"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  CheckSquare,
  MessageSquare,
  BarChart3,
  FileText,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCourses } from "@/lib/hooks";
import { useAuthStore } from "@/lib/stores";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/calendar", label: "Calendar", icon: Calendar },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/insights", label: "Insights", icon: BarChart3 },
  { href: "/materials", label: "Materials", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: courses } = useCourses();
  const user = useAuthStore((s) => s.user);

  return (
    <aside className="hidden md:flex w-[257px] flex-col border-r border-[var(--border)] bg-[var(--sidebar)]">
      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-2.5 px-5 py-5">
        <Image src="/logo.png" alt="BrainyBuddy" width={32} height={32} />
        <span className="text-lg font-semibold text-[var(--foreground)]">
          BrainyBuddy
        </span>
      </Link>

      {/* Nav */}
      <nav className="flex flex-col gap-0.5 px-3">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--accent)] text-[var(--accent-foreground)]"
                  : "text-[var(--muted-foreground)] hover:bg-[rgba(170,120,166,0.1)] hover:text-[var(--foreground)]"
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="mx-5 my-4 h-px bg-[var(--border)]" />

      {/* Courses */}
      <div className="flex-1 overflow-y-auto px-5">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
          My Courses
        </p>
        <div className="flex flex-col gap-1">
          {courses?.map((course) => (
            <Link
              key={course.id}
              href={`/tasks?course=${course.id}`}
              className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-[var(--foreground)] transition-colors hover:bg-[rgba(170,120,166,0.08)]"
            >
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: course.color || "var(--accent)" }}
              />
              <span className="truncate">{course.name}</span>
            </Link>
          ))}
          {(!courses || courses.length === 0) && (
            <p className="px-2 text-xs text-[var(--muted-foreground)]">
              No courses yet
            </p>
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="mx-5 h-px bg-[var(--border)]" />

      {/* User card + Settings */}
      <div className="flex items-center gap-3 px-5 py-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--secondary)] text-sm font-semibold text-[var(--foreground)]">
          {user?.display_name?.charAt(0)?.toUpperCase() || "U"}
        </div>
        <div className="flex-1 overflow-hidden">
          <p className="truncate text-sm font-medium text-[var(--foreground)]">
            {user?.display_name || "User"}
          </p>
          <p className="truncate text-xs text-[var(--muted-foreground)]">
            {user?.email || ""}
          </p>
        </div>
        <Link
          href="/settings"
          className="shrink-0 rounded-md p-1.5 text-[var(--muted-foreground)] transition-colors hover:bg-[var(--secondary)] hover:text-[var(--foreground)]"
        >
          <Settings className="h-4 w-4" />
        </Link>
      </div>
    </aside>
  );
}
