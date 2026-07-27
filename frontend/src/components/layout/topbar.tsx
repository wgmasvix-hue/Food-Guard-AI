"use client";

import { LogOut, Menu, Moon, Sun, User as UserIcon } from "lucide-react";
import { useState } from "react";

import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";
import { roleLabel } from "@/lib/utils";

export function Topbar({ title, onMenuClick }: { title: string; onMenuClick: () => void }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="flex h-16 items-center justify-between border-b border-ink-200 bg-surface px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="-ml-1 rounded-md p-1.5 text-ink-500 hover:bg-ink-100 hover:text-ink-900 md:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="truncate text-base font-semibold text-ink-900 sm:text-lg">{title}</h1>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <button
          onClick={toggleTheme}
          className="rounded-md p-2 text-ink-500 hover:bg-ink-100 hover:text-ink-900"
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? <Sun className="h-4.5 w-4.5" /> : <Moon className="h-4.5 w-4.5" />}
        </button>

        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="flex items-center gap-2 rounded-full border border-ink-200 py-1 pl-1 pr-2 hover:bg-ink-50 sm:pr-3"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-brand-700">
              <UserIcon className="h-4 w-4" />
            </span>
            <span className="hidden text-sm font-medium text-ink-800 sm:inline">{user?.full_name ?? "…"}</span>
          </button>

          {menuOpen && (
            <>
              <button
                className="fixed inset-0 z-10 cursor-default"
                aria-label="Close menu"
                onClick={() => setMenuOpen(false)}
              />
              <div className="absolute right-0 z-20 mt-2 w-56 rounded-lg border border-ink-200 bg-surface py-1 shadow-lg animate-fade-in">
                <div className="border-b border-ink-100 px-3 py-2">
                  <p className="text-sm font-medium text-ink-900">{user?.full_name}</p>
                  <p className="text-xs text-ink-500">{user?.email}</p>
                  <p className="mt-1 text-xs font-medium text-brand-700">{roleLabel(user?.role)}</p>
                </div>
                <button
                  onClick={logout}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <LogOut className="h-4 w-4" /> Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
