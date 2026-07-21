"use client";

import {
  Bot,
  ClipboardCheck,
  FileText,
  LayoutDashboard,
  ListChecks,
  Settings,
  ShieldAlert,
  Thermometer,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandMark } from "@/components/brand-mark";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/haccp", label: "HACCP", icon: ShieldAlert },
  { href: "/gmp", label: "GMP", icon: ListChecks },
  { href: "/temperature", label: "Temperature Logs", icon: Thermometer },
  { href: "/corrective-actions", label: "Corrective Actions", icon: ClipboardCheck },
  { href: "/audits", label: "Audits", icon: ClipboardCheck },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/ai-assistant", label: "AI Assistant", icon: Bot },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-ink-200 bg-white md:flex">
      <div className="px-5 py-5">
        <BrandMark />
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-brand-50 text-brand-700" : "text-ink-600 hover:bg-ink-100 hover:text-ink-900"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 text-xs text-ink-400">© {new Date().getFullYear()} Food Guard AI</div>
    </aside>
  );
}
