"use client";

import { Smartphone } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandMark } from "@/components/brand-mark";
import { NAV_ITEMS } from "@/components/layout/nav-items";
import { ANDROID_APK_DOWNLOAD_URL } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-ink-200/60 bg-surface/80 backdrop-blur-xl md:flex">
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
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-150",
                active
                  ? "bg-brand-600 text-white shadow-soft"
                  : "text-ink-600 hover:bg-ink-100/80 hover:text-ink-900"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-3 pb-2">
        <a
          href={ANDROID_APK_DOWNLOAD_URL}
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-ink-600 hover:bg-ink-100 hover:text-ink-900"
        >
          <Smartphone className="h-4 w-4" />
          Download Android App
        </a>
      </div>
      <div className="space-y-0.5 px-5 py-4 text-xs text-ink-400">
        <p>© {new Date().getFullYear()} FoodOS</p>
        <p>Powered by ChengetAi Labs</p>
      </div>
    </aside>
  );
}
