"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "H" },
  { href: "/calendar", label: "Calendar", icon: "C" },
  { href: "/tasks", label: "Tasks", icon: "T" },
  { href: "/chat", label: "Chat", icon: "M" },
  { href: "/insights", label: "Insights", icon: "I" },
  { href: "/materials", label: "Materials", icon: "D" },
  { href: "/settings", label: "Settings", icon: "S" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-60 flex-col border-r border-[var(--border)] bg-[var(--background)] p-4">
      <Link href="/dashboard" className="text-xl font-bold mb-8 px-2">
        BrainyBuddy
      </Link>

      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              pathname === item.href || pathname.startsWith(item.href + "/")
                ? "bg-[var(--accent)] text-[var(--accent-foreground)] font-medium"
                : "text-[var(--muted-foreground)] hover:bg-[var(--accent)]"
            )}
          >
            <span className="w-5 h-5 flex items-center justify-center text-xs font-bold rounded bg-[var(--secondary)]">
              {item.icon}
            </span>
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
