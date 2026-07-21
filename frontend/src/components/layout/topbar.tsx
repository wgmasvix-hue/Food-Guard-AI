"use client";

import { LogOut, User as UserIcon } from "lucide-react";
import { useState } from "react";

import { useAuth } from "@/lib/auth-context";
import { roleLabel } from "@/lib/utils";

export function Topbar({ title }: { title: string }) {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="flex h-16 items-center justify-between border-b border-ink-200 bg-white px-6">
      <h1 className="text-lg font-semibold text-ink-900">{title}</h1>

      <div className="relative">
        <button
          onClick={() => setMenuOpen((o) => !o)}
          className="flex items-center gap-2 rounded-full border border-ink-200 py-1 pl-1 pr-3 hover:bg-ink-50"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-brand-700">
            <UserIcon className="h-4 w-4" />
          </span>
          <span className="text-sm font-medium text-ink-800">{user?.full_name ?? "…"}</span>
        </button>

        {menuOpen && (
          <div className="absolute right-0 z-20 mt-2 w-56 rounded-lg border border-ink-200 bg-white py-1 shadow-lg animate-fade-in">
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
        )}
      </div>
    </header>
  );
}
