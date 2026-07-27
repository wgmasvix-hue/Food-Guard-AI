"use client";

import { X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { BrandMark } from "@/components/brand-mark";
import { NAV_ITEMS } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";

export function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  // Close automatically on route change.
  useEffect(() => {
    onClose();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex md:hidden">
      <button
        aria-label="Close menu"
        onClick={onClose}
        className="absolute inset-0 bg-black/50 animate-fade-in"
      />
      <div className="relative flex w-72 max-w-[80vw] flex-col bg-surface shadow-xl animate-fade-in">
        <div className="flex items-center justify-between px-5 py-5">
          <BrandMark />
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-700"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
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
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
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
      </div>
    </div>
  );
}
