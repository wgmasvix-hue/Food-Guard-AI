"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Bell, CheckCheck, Info, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { api } from "@/lib/api-client";
import type { Notification } from "@/lib/types";
import { cn, formatDateTime } from "@/lib/utils";

const LEVEL_ICON: Record<Notification["level"], typeof Info> = {
  info: Info,
  warning: AlertTriangle,
  critical: ShieldAlert,
};

const LEVEL_CLASSES: Record<Notification["level"], string> = {
  info: "bg-blue-50 text-blue-600",
  warning: "bg-amber-50 text-amber-600",
  critical: "bg-red-50 text-red-600",
};

export function NotificationBell() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get<Notification[]>("/notifications")).data,
    refetchInterval: 60_000,
  });

  const unreadCount = notifications?.filter((n) => !n.is_read).length ?? 0;

  async function markRead(id: string) {
    await api.post(`/notifications/${id}/read`);
    queryClient.setQueryData<Notification[]>(["notifications"], (prev) =>
      prev?.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
  }

  async function markAllRead() {
    await api.post("/notifications/read-all");
    queryClient.setQueryData<Notification[]>(["notifications"], (prev) => prev?.map((n) => ({ ...n, is_read: true })));
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative rounded-md p-2 text-ink-500 hover:bg-ink-100 hover:text-ink-900"
        aria-label={unreadCount > 0 ? `${unreadCount} unread notifications` : "Notifications"}
      >
        <Bell className="h-4.5 w-4.5" />
        {unreadCount > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <button className="fixed inset-0 z-10 cursor-default" aria-label="Close notifications" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-2 w-80 max-w-[90vw] rounded-2xl border border-ink-200/60 bg-surface/95 shadow-soft-lg backdrop-blur-xl animate-fade-in">
            <div className="flex items-center justify-between border-b border-ink-100/80 px-4 py-3">
              <p className="text-sm font-semibold text-ink-900">Notifications</p>
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline">
                  <CheckCheck className="h-3.5 w-3.5" /> Mark all read
                </button>
              )}
            </div>
            <div className="max-h-96 overflow-y-auto scrollbar-thin">
              {notifications?.length === 0 && (
                <p className="px-4 py-8 text-center text-sm text-ink-400">You&apos;re all caught up.</p>
              )}
              {notifications?.map((n) => {
                const Icon = LEVEL_ICON[n.level];
                const content = (
                  <div
                    className={cn(
                      "flex gap-3 border-b border-ink-100/60 px-4 py-3 text-left transition-colors last:border-0 hover:bg-ink-50",
                      !n.is_read && "bg-brand-50/40"
                    )}
                  >
                    <span className={cn("mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg", LEVEL_CLASSES[n.level])}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-ink-900">{n.title}</p>
                      <p className="mt-0.5 line-clamp-2 text-xs text-ink-500">{n.message}</p>
                      <p className="mt-1 text-[11px] text-ink-400">{formatDateTime(n.created_at)}</p>
                    </div>
                    {!n.is_read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-600" />}
                  </div>
                );
                return n.link ? (
                  <Link key={n.id} href={n.link} onClick={() => { if (!n.is_read) markRead(n.id); setOpen(false); }}>
                    {content}
                  </Link>
                ) : (
                  <button key={n.id} className="block w-full" onClick={() => !n.is_read && markRead(n.id)}>
                    {content}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
